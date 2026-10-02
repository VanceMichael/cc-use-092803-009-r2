import threading

from .assignments import AssignmentBoard
from .audit import AuditLog
from .auth import Principal, require
from .clock import parse_time
from .events import EventRegister
from .models import Assignment, Event, SupplyLot, Team
from .plans import PlanBook
from .recovery import RecoveryJournal
from .store import StateStore
from .supplies import SupplyLedger
from .teams import TeamRegistry
from .geo import RiskMap
from .errors import Conflict


class EmergencyPlatform:
    def __init__(self, db_path=":memory:"):
        self._lock = threading.RLock()
        self.store = StateStore(db_path)
        self.audit = AuditLog(self.store)
        self.audit.restore(self.store.list_audit())
        self.journal = RecoveryJournal(self.audit, self.store)
        self.events = EventRegister(self.audit, self.store)
        self.teams = TeamRegistry(self.audit, self.store)
        self.supplies = SupplyLedger(self.audit, self.store)
        self.assignments = AssignmentBoard(self.events, self.teams, self.audit, self.store)
        self.risks = RiskMap(self.audit)
        self.plans = PlanBook(self.audit)

        # 从快照重建领域状态。
        self.events.restore(self.store.list_events())
        self.teams.load_snapshot(self.store.list_teams())
        self.supplies.load_snapshot(self.store.list_lots())
        self.assignments.load_snapshot(self.store.list_assignments())

        self._register_recovery_handlers()
        # 重启后重放崩溃时未决的意图；各处理函数按 request_id/effect_key 幂等。
        self.recover()

    # ---- 请求先占模板 ----

    def _run_once(self, request_id, action, payload, work):
        """串行化 + 请求先占。

        同一 request_id 的并发/重试提交只有一路真正执行业务；已完成的直接
        回灌原结果；正在处理中的明确报冲突，不允许重复扣减、重复派单。
        """
        with self._lock:
            claim = self.store.claim_request(request_id, action)
            if claim["status"] == "done":
                return claim["result"]
            if claim["status"] == "processing":
                raise Conflict("请求正在处理中，请稍后查询结果")
            self.journal.record_pending(request_id, action, payload)
            try:
                result = work()
            except BaseException:
                # 业务失败：释放先占，调用方可凭原 request_id 重试。
                self.store.abandon_request(request_id)
                self.journal.complete(request_id)
                raise
            return self.store.finish_request(request_id, result)

    # ---- 事件 ----

    def create_event(self, principal, event, request_id):
        require(principal, "plan", event.region)

        def work():
            result = self.events.create(event, request_id)
            return {
                "event_id": result.event_id,
                "status": result.status,
                "version": result.version,
                "region": result.region,
            }

        return self._run_once(
            request_id,
            "create_event",
            {
                "event_id": event.event_id,
                "region": event.region,
                "kind": event.kind,
                "severity": event.severity,
                "occurred_at": event.occurred_at.isoformat(),
                "source": event.source,
            },
            work,
        )

    # ---- 派单 ----

    def assign(self, principal, assignment, request_id):
        event = self.events.get(assignment.event_id, assignment.region or None)
        require(principal, "assign", event.region)
        if not assignment.region:
            assignment.region = event.region

        def work():
            result = self.assignments.plan(assignment, request_id)
            return {"assignment_id": result.assignment_id, "state": result.state}

        return self._run_once(
            request_id,
            "assign",
            {
                "assignment_id": assignment.assignment_id,
                "event_id": assignment.event_id,
                "region": assignment.region,
                "team_id": assignment.team_id,
                "quantity": assignment.quantity,
            },
            work,
        )

    def acknowledge(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        event = self.events.get(item.event_id, item.region or None)
        require(principal, "assign", event.region)

        def work():
            result = self.assignments.acknowledge(assignment_id, request_id)
            return {"assignment_id": result.assignment_id, "state": result.state}

        return self._run_once(request_id, "acknowledge", {"assignment_id": assignment_id}, work)

    def complete_assignment(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        event = self.events.get(item.event_id, item.region or None)
        require(principal, "assign", event.region)

        def work():
            result = self.assignments.complete(assignment_id, request_id)
            return {"assignment_id": result.assignment_id, "state": result.state}

        return self._run_once(request_id, "complete_assignment", {"assignment_id": assignment_id}, work)

    def cancel_assignment(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        event = self.events.get(item.event_id, item.region or None)
        require(principal, "assign", event.region)

        def work():
            result = self.assignments.cancel(assignment_id, request_id)
            return {"assignment_id": result.assignment_id, "state": result.state}

        return self._run_once(request_id, "cancel_assignment", {"assignment_id": assignment_id}, work)

    # ---- 事件升级 / 关闭 ----

    def escalate(self, principal, event_id, request_id, region=None):
        event = self.events.get(event_id, region)
        require(principal, "escalate", event.region)

        def work():
            result = self.events.change_status(
                event_id, "escalated", request_id, event.region,
                effect_key=f"escalate:{event_id}",
            )
            return {
                "event_id": result.event_id,
                "status": result.status,
                "version": result.version,
                "region": result.region,
            }

        return self._run_once(
            request_id, "escalate", {"event_id": event_id, "region": event.region}, work
        )

    def close(self, principal, event_id, request_id, region=None):
        event = self.events.get(event_id, region)
        require(principal, "close", event.region)

        def work():
            result = self.events.change_status(
                event_id, "closed", request_id, event.region,
                effect_key=f"close:{event_id}",
            )
            return {
                "event_id": result.event_id,
                "status": result.status,
                "version": result.version,
                "region": result.region,
            }

        return self._run_once(
            request_id, "close", {"event_id": event_id, "region": event.region}, work
        )

    # ---- 物资 ----

    def add_lot(self, principal, lot, request_id):
        require(principal, "reserve", "global")

        def work():
            result = self.supplies.add(lot, request_id)
            return {"lot_id": result.lot_id, "quantity": result.quantity, "reserved": result.reserved}

        return self._run_once(request_id, "add_lot", {"lot_id": lot.lot_id}, work)

    def reserve_supply(self, principal, lot_id, amount, request_id, event_id=None, region=None):
        if event_id is not None:
            event = self.events.get(event_id, region)
            require(principal, "reserve", event.region)
        else:
            require(principal, "reserve", "global")

        def work():
            reserved = self.supplies.reserve(
                lot_id, amount, request_id, event_id=event_id,
                effect_key=f"reserve:{lot_id}:{request_id}",
            )
            return {"lot_id": lot_id, "reserved": reserved}

        return self._run_once(
            request_id,
            "reserve_supply",
            {"lot_id": lot_id, "amount": amount, "event_id": event_id, "region": region},
            work,
        )

    def release_supply(self, principal, lot_id, amount, request_id, event_id=None, region=None):
        if event_id is not None:
            event = self.events.get(event_id, region)
            require(principal, "release", event.region)
        else:
            require(principal, "release", "global")

        def work():
            reserved = self.supplies.release(
                lot_id, amount, request_id, event_id=event_id,
                effect_key=f"release:{lot_id}:{request_id}",
            )
            return {"lot_id": lot_id, "reserved": reserved}

        return self._run_once(
            request_id,
            "release_supply",
            {"lot_id": lot_id, "amount": amount, "event_id": event_id, "region": region},
            work,
        )

    def freeze_supply(self, principal, lot_id, request_id):
        require(principal, "freeze", "global")

        def work():
            lot = self.supplies.freeze(lot_id, request_id, effect_key=f"freeze:{lot_id}:{request_id}")
            return {"lot_id": lot.lot_id, "frozen": lot.frozen}

        return self._run_once(request_id, "freeze_supply", {"lot_id": lot_id}, work)

    # ---- 处置链视图 ----

    def event_chain(self, principal, event_id, region=None):
        """现场人员查看同一灾害的唯一处置链：事件、实际派单、物资变动。"""
        event = self.events.get(event_id, region)
        require(principal, "plan", event.region)
        with self._lock:
            assignments = [
                {
                    "assignment_id": item.assignment_id,
                    "team_id": item.team_id,
                    "state": item.state,
                    "quantity": item.quantity,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
                for item in self.assignments.for_event(event_id)
            ]
            movements = self.supplies.movements_for_event(event_id)
            lot_totals = {}
            for move in movements:
                delta = move["amount"] if move["direction"] == "reserve" else -move["amount"]
                lot_totals[move["lot_id"]] = lot_totals.get(move["lot_id"], 0) + delta
            supplies = [
                {
                    "lot_id": lot_id,
                    "net_locked": net,
                    "movements": [
                        {"direction": m["direction"], "amount": m["amount"], "request_id": m["request_id"]}
                        for m in movements
                        if m["lot_id"] == lot_id
                    ],
                }
                for lot_id, net in lot_totals.items()
            ]
            return {
                "event": {
                    "event_id": event.event_id,
                    "region": event.region,
                    "status": event.status,
                    "version": event.version,
                    "source": event.source,
                },
                "assignments": assignments,
                "supplies": supplies,
            }

    # ---- 恢复 ----

    def _register_recovery_handlers(self):
        def replay_create_event(payload, request_id):
            event = Event(
                event_id=payload["event_id"],
                region=payload["region"],
                kind=payload.get("kind", "rain"),
                severity=int(payload.get("severity", 1)),
                occurred_at=parse_time(payload["occurred_at"]),
                source=payload.get("source", "manual"),
            )
            self.events.create(event, request_id)

        def replay_assign(payload, request_id):
            assignment = Assignment(
                assignment_id=payload["assignment_id"],
                event_id=payload["event_id"],
                team_id=payload["team_id"],
                region=payload.get("region", ""),
                quantity=int(payload.get("quantity", 0)),
            )
            self.assignments.plan(assignment, request_id)

        def replay_reserve(payload, request_id):
            self.supplies.reserve(
                payload["lot_id"],
                int(payload["amount"]),
                request_id,
                event_id=payload.get("event_id"),
                effect_key=f"reserve:{payload['lot_id']}:{request_id}",
            )

        def replay_release(payload, request_id):
            self.supplies.release(
                payload["lot_id"],
                int(payload["amount"]),
                request_id,
                event_id=payload.get("event_id"),
                effect_key=f"release:{payload['lot_id']}:{request_id}",
            )

        def replay_acknowledge(payload, request_id):
            self.assignments.acknowledge(payload["assignment_id"], request_id)

        def replay_complete(payload, request_id):
            self.assignments.complete(payload["assignment_id"], request_id)

        def replay_cancel(payload, request_id):
            self.assignments.cancel(payload["assignment_id"], request_id)

        def replay_escalate(payload, request_id):
            self.events.change_status(
                payload["event_id"], "escalated", request_id,
                payload.get("region"), effect_key=f"escalate:{payload['event_id']}",
            )

        def replay_close(payload, request_id):
            self.events.change_status(
                payload["event_id"], "closed", request_id,
                payload.get("region"), effect_key=f"close:{payload['event_id']}",
            )

        def replay_freeze(payload, request_id):
            self.supplies.freeze(
                payload["lot_id"], request_id,
                effect_key=f"freeze:{payload['lot_id']}:{request_id}",
            )

        self.journal.register_handler("create_event", replay_create_event)
        self.journal.register_handler("assign", replay_assign)
        self.journal.register_handler("acknowledge", replay_acknowledge)
        self.journal.register_handler("complete_assignment", replay_complete)
        self.journal.register_handler("cancel_assignment", replay_cancel)
        self.journal.register_handler("escalate", replay_escalate)
        self.journal.register_handler("close", replay_close)
        self.journal.register_handler("reserve_supply", replay_reserve)
        self.journal.register_handler("release_supply", replay_release)
        self.journal.register_handler("freeze_supply", replay_freeze)

    def recover(self):
        with self._lock:
            return self.journal.drain()

    # ---- 审计 ----

    def audit_for(self, principal, entity, entity_id):
        require(principal, "read_audit", "global")
        return self.audit.for_entity(entity, entity_id)
