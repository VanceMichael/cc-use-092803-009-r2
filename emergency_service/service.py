import threading
from datetime import datetime
from .assignments import AssignmentBoard
from .audit import AuditLog
from .auth import Principal, require
from .events import EventRegister
from .models import Assignment, Event, SupplyLot, Team
from .plans import PlanBook
from .recovery import RecoveryJournal
from .store import StateStore
from .supplies import SupplyLedger
from .teams import TeamRegistry
from .geo import RiskMap

class EmergencyPlatform:
    def __init__(self, db_path=":memory:"):
        # 所有写请求在此串行化，保证并发提交下"检查-写入"是原子的
        self._lock = threading.RLock()
        self.audit = AuditLog()
        self.store = StateStore(db_path)
        # 审计实时落盘，重启后据流水重建领域状态
        self.audit.set_sink(self.store.append_audit)
        self.events = EventRegister(self.audit)
        self.teams = TeamRegistry(self.audit)
        self.supplies = SupplyLedger(self.audit)
        self.assignments = AssignmentBoard(self.events, self.teams, self.audit)
        self.risks = RiskMap(self.audit)
        self.plans = PlanBook(self.audit)
        self._restore_from_audit()
        self.journal = RecoveryJournal(self.audit, self.store)
        # 崩溃前未确认完成的动作按原 request_id 重放
        self.recover()

    # ---- 重启重建：按审计流水顺序回放，只重建状态、不新增审计 ----

    def _restore_from_audit(self):
        rows = self.store.load_audit()
        if not rows:
            return
        # 先载入历史审计（恢复条目与序号），再在不新增审计的前提下回放重建领域状态
        self.audit.restore(rows)
        with self.audit.rewriting():
            for row in rows:
                self._apply_audit_row(row)

    def _apply_audit_row(self, row):
        action = row["action"]
        entity_id = row["entity_id"]
        detail = row["detail"]
        request_id = row["request_id"]
        created_at = datetime.fromisoformat(row["created_at"])
        if action == "create_event":
            event = Event(entity_id, detail["region"], detail.get("kind", "rain"),
                          int(detail.get("severity", 1)),
                          datetime.fromisoformat(detail["occurred_at"]),
                          detail.get("source", "manual"))
            self.events.create(event, request_id)
        elif action == "register_team":
            self.teams.register(Team(entity_id, detail["region"],
                                     frozenset(detail.get("skills", [])),
                                     int(detail["capacity"])), request_id)
        elif action == "add_supply":
            self.supplies.add(SupplyLot(entity_id, detail.get("item", ""),
                                        int(detail["quantity"])), request_id)
        elif action == "plan_assignment":
            item = Assignment(entity_id, detail["event_id"], detail["team_id"],
                              quantity=int(detail.get("quantity", 0)),
                              region=detail.get("region"))
            self.assignments.plan(item, request_id)
        elif action == "ack_assignment":
            acked = self.assignments.acknowledge(entity_id, request_id)
            acked.updated_at = created_at
        elif action == "complete_assignment":
            done = self.assignments.complete(entity_id, request_id)
            done.updated_at = created_at
        elif action == "cancel_assignment":
            cancelled = self.assignments.cancel(entity_id, request_id)
            cancelled.updated_at = created_at
        elif action == "reserve_supply":
            self.supplies.reserve(entity_id, int(detail["amount"]), request_id,
                                  detail.get("reservation_id"))
        elif action == "release_supply":
            self.supplies.release(entity_id, int(detail["amount"]), request_id,
                                  detail.get("reservation_id"))
        elif action == "freeze_supply":
            self.supplies.freeze(entity_id, request_id)
        elif action == "consume_team":
            self.teams.consume(entity_id, int(detail["amount"]), request_id)
        elif action == "restore_team":
            self.teams.restore(entity_id, int(detail["amount"]), request_id)
        elif action == "change_event":
            self.events.change_status(entity_id, detail["status"], request_id,
                                      detail.get("region"))
        # plan/cancel 回放会再次调用 consume/restore，但 request_id 相同，
        # TeamRegistry 按请求幂等，不会重复改变队伍能力

    # ---- 通用执行管线：请求缓存 + 未决日志，全部按 request_id 幂等 ----

    def _execute(self, request_id, action, payload, func, build):
        with self._lock:
            cached = self.store.get_request(request_id)
            if cached is not None:
                return cached
            self.journal.record_pending(request_id, action, payload)
            try:
                outcome = func()
            except BaseException:
                # 被拒绝的请求不应留在未决日志里；进程崩溃才会绕过这里
                self.journal.mark_done(request_id)
                raise
            result = build(outcome)
            saved = self.store.save_request(request_id, result)
            self.journal.mark_done(request_id)
            return saved

    # ---- 事件接收 ----

    @staticmethod
    def _event_payload(event):
        return {
            "event_id": event.event_id,
            "region": event.region,
            "kind": event.kind,
            "severity": event.severity,
            "occurred_at": event.occurred_at.isoformat(),
            "source": event.source,
        }

    @staticmethod
    def _event_from(payload):
        from .clock import parse_time
        return Event(
            payload["event_id"], payload["region"], payload.get("kind", "rain"),
            int(payload.get("severity", 1)), parse_time(payload["occurred_at"]),
            payload.get("source", "manual"),
        )

    def create_event(self, principal, event, request_id):
        require(principal, "plan", event.region)
        return self._execute(
            request_id, "create_event", self._event_payload(event),
            lambda: self.events.create(event, request_id),
            lambda result: {"event_id": result.event_id, "region": result.region,
                            "status": result.status, "version": result.version},
        )

    def _change_event(self, principal, event_id, status, action_name, request_id, region):
        event = self.events.get(event_id, region)
        require(principal, action_name, event.region)
        return self._execute(
            request_id, action_name + "_event", {"event_id": event_id, "region": event.region, "status": status},
            lambda: self.events.change_status(event_id, status, request_id, event.region),
            lambda result: {"event_id": result.event_id, "region": result.region,
                            "status": result.status, "version": result.version},
        )

    def escalate(self, principal, event_id, request_id, region=None):
        return self._change_event(principal, event_id, "escalated", "escalate", request_id, region)

    def close(self, principal, event_id, request_id, region=None):
        return self._change_event(principal, event_id, "closed", "close", request_id, region)

    # ---- 派单 ----

    @staticmethod
    def _assignment_payload(assignment):
        return {"assignment_id": assignment.assignment_id, "event_id": assignment.event_id,
                "team_id": assignment.team_id, "quantity": assignment.quantity,
                "region": assignment.region}

    def _assignment_view(self, item):
        team = self.teams.get(item.team_id)
        return {"assignment_id": item.assignment_id, "event_id": item.event_id,
                "team_id": item.team_id, "region": item.region, "state": item.state,
                "quantity": item.quantity, "team_capacity": team.capacity}

    def assign(self, principal, assignment, request_id):
        team = self.teams.get(assignment.team_id)
        event = self.events.get(assignment.event_id, team.region)
        require(principal, "assign", event.region)
        assignment.region = event.region
        return self._execute(
            request_id, "assign", self._assignment_payload(assignment),
            lambda: self.assignments.plan(assignment, request_id),
            self._assignment_view,
        )

    def acknowledge(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        require(principal, "assign", item.region or "global")
        return self._execute(
            request_id, "acknowledge_assignment", {"assignment_id": assignment_id},
            lambda: self.assignments.acknowledge(assignment_id, request_id),
            self._assignment_view,
        )

    def complete_assignment(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        require(principal, "assign", item.region or "global")
        return self._execute(
            request_id, "complete_assignment", {"assignment_id": assignment_id},
            lambda: self.assignments.complete(assignment_id, request_id),
            self._assignment_view,
        )

    def cancel_assignment(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        require(principal, "assign", item.region or "global")
        return self._execute(
            request_id, "cancel_assignment", {"assignment_id": assignment_id},
            lambda: self.assignments.cancel(assignment_id, request_id),
            self._assignment_view,
        )

    # ---- 物资 ----

    def _lot_view(self, lot, amount=None):
        view = {"lot_id": lot.lot_id, "item": lot.item, "quantity": lot.quantity,
                "reserved": lot.reserved, "available": lot.quantity - lot.reserved,
                "frozen": lot.frozen}
        if amount is not None:
            view["amount"] = amount
        return view

    def add_supply(self, principal, lot, request_id):
        require(principal, "reserve", "global")
        return self._execute(
            request_id, "add_supply", {"lot_id": lot.lot_id, "item": lot.item, "quantity": lot.quantity},
            lambda: self.supplies.add(lot, request_id),
            lambda result: self._lot_view(result),
        )

    def reserve(self, principal, lot_id, amount, request_id, reservation_id=None):
        require(principal, "reserve", "global")
        return self._execute(
            request_id, "reserve_supply", {"lot_id": lot_id, "amount": amount, "reservation_id": reservation_id},
            lambda: self.supplies.reserve(lot_id, amount, request_id, reservation_id),
            lambda _: self._lot_view(self.supplies.get(lot_id), amount),
        )

    def release(self, principal, lot_id, amount, request_id, reservation_id=None):
        require(principal, "release", "global")
        return self._execute(
            request_id, "release_supply", {"lot_id": lot_id, "amount": amount, "reservation_id": reservation_id},
            lambda: self.supplies.release(lot_id, amount, request_id, reservation_id),
            lambda _: self._lot_view(self.supplies.get(lot_id), amount),
        )

    def freeze_supply(self, principal, lot_id, request_id):
        require(principal, "freeze", "global")
        return self._execute(
            request_id, "freeze_supply", {"lot_id": lot_id},
            lambda: self.supplies.freeze(lot_id, request_id),
            lambda result: self._lot_view(result),
        )

    # ---- 崩溃恢复 ----

    def _replay(self, action, payload, request_id):
        """按未决日志重放单个动作。领域层按 request_id 幂等，不会产生重复副作用。"""
        if action == "create_event":
            self.events.create(self._event_from(payload), request_id)
            return None
        if action == "assign":
            item = Assignment(payload["assignment_id"], payload["event_id"],
                              payload["team_id"], quantity=int(payload.get("quantity", 0)),
                              region=payload.get("region"))
            return self._assignment_view(self.assignments.plan(item, request_id))
        if action == "acknowledge_assignment":
            return self._assignment_view(self.assignments.acknowledge(payload["assignment_id"], request_id))
        if action == "complete_assignment":
            return self._assignment_view(self.assignments.complete(payload["assignment_id"], request_id))
        if action == "cancel_assignment":
            return self._assignment_view(self.assignments.cancel(payload["assignment_id"], request_id))
        if action == "reserve_supply":
            self.supplies.reserve(payload["lot_id"], int(payload["amount"]), request_id,
                                  payload.get("reservation_id"))
            return self._lot_view(self.supplies.get(payload["lot_id"]), int(payload["amount"]))
        if action == "release_supply":
            self.supplies.release(payload["lot_id"], int(payload["amount"]), request_id,
                                  payload.get("reservation_id"))
            return self._lot_view(self.supplies.get(payload["lot_id"]), int(payload["amount"]))
        if action == "freeze_supply":
            return self._lot_view(self.supplies.freeze(payload["lot_id"], request_id))
        if action in {"escalate_event", "close_event"}:
            result = self.events.change_status(payload["event_id"], payload["status"],
                                               request_id, payload.get("region"))
            return {"event_id": result.event_id, "region": result.region,
                    "status": result.status, "version": result.version}
        if action == "add_supply":
            lot = SupplyLot(payload["lot_id"], payload["item"], int(payload["quantity"]))
            return self._lot_view(self.supplies.add(lot, request_id))
        raise ValueError("未知的恢复动作: " + action)

    def recover(self):
        with self._lock:
            def handle(action, payload, request_id):
                cached = self.store.get_request(request_id)
                if cached is not None:
                    # 结果已落盘但日志未清理，无需再放副作用
                    return cached
                result = self._replay(action, payload, request_id)
                if result is not None:
                    self.store.save_request(request_id, result)
                return result
            return self.journal.drain(handle)

    # ---- 审计 ----

    def audit_for(self, principal, entity, entity_id, region=None):
        require(principal, "read_audit", "global")
        entries = self.audit.for_entity(entity, entity_id)
        if region is not None:
            # 同一外部事件号可能跨地区复用，按地区只取本灾害这一条处置链
            entries = [e for e in entries if e.detail.get("region") == region]
        return entries
