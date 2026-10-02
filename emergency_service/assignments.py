import threading

from .clock import utc_now
from .errors import Conflict, InvalidTransition, NotFound


class AssignmentBoard:
    def __init__(self, events, teams, audit, store=None):
        self.events = events
        self.teams = teams
        self.audit = audit
        self.store = store
        self.items = {}
        self._lock = threading.RLock()

    def plan(self, assignment, request_id):
        with self._lock:
            if assignment.assignment_id in self.items:
                old = self.items[assignment.assignment_id]
                if old.event_id == assignment.event_id and old.team_id == assignment.team_id:
                    # 同一派单的重试/重放：原样返回，绝不再次扣减队伍能力。
                    return old
                raise Conflict("派单编号冲突")
            event = self.events.get(assignment.event_id, assignment.region or None)
            if not assignment.region:
                assignment.region = event.region
            if event.status == "closed":
                raise InvalidTransition("关闭事件不能派单")
            self.teams.consume(
                assignment.team_id,
                max(1, assignment.quantity),
                request_id,
                effect_key=f"plan-consume:{assignment.assignment_id}",
            )
            assignment.updated_at = utc_now()
            self.items[assignment.assignment_id] = assignment
            self.audit.append(
                "plan_assignment", "assignment", assignment.assignment_id, request_id,
                {"event_id": assignment.event_id, "region": assignment.region},
            )
            if self.store is not None:
                self.store.upsert_assignment(assignment)
            return assignment
    def get(self, assignment_id):
        with self._lock:
            if assignment_id not in self.items:
                raise NotFound("派单不存在")
            return self.items[assignment_id]

    def for_event(self, event_id):
        with self._lock:
            return [item for item in self.items.values() if item.event_id == event_id]

    def _already_applied(self, request_id, effect_key):
        return self.store is not None and self.store.effect_seen(request_id, effect_key)

    def acknowledge(self, assignment_id, request_id):
        with self._lock:
            item = self.get(assignment_id)
            effect_key = f"ack:{assignment_id}"
            if item.state != "planned":
                # 同一请求的重放：状态已推进则原样返回，不报错、不重复审计。
                if self._already_applied(request_id, effect_key):
                    return item
                raise InvalidTransition("派单不是待确认状态")
            item.state = "acknowledged"
            item.updated_at = utc_now()
            self.audit.append("ack_assignment", "assignment", assignment_id, request_id, {})
            if self.store is not None:
                applied = self.store.save_assignment_effect(item, request_id, effect_key)
                if not applied:
                    item.state = "planned"
            return item

    def complete(self, assignment_id, request_id):
        with self._lock:
            item = self.get(assignment_id)
            effect_key = f"complete:{assignment_id}"
            if item.state != "acknowledged":
                if self._already_applied(request_id, effect_key):
                    return item
                raise InvalidTransition("派单尚未确认")
            item.state = "completed"
            item.updated_at = utc_now()
            self.audit.append("complete_assignment", "assignment", assignment_id, request_id, {})
            if self.store is not None:
                applied = self.store.save_assignment_effect(item, request_id, effect_key)
                if not applied:
                    item.state = "acknowledged"
            return item

    def cancel(self, assignment_id, request_id):
        with self._lock:
            item = self.get(assignment_id)
            effect_key = f"cancel:{assignment_id}"
            if self._already_applied(request_id, effect_key):
                return item
            if item.state in {"completed", "cancelled"}:
                raise InvalidTransition("派单不能取消")
            previous_state = item.state
            item.state = "cancelled"
            item.updated_at = utc_now()
            self.teams.restore(
                item.team_id,
                max(1, item.quantity),
                request_id,
                effect_key=f"cancel-restore:{assignment_id}",
            )
            self.audit.append("cancel_assignment", "assignment", assignment_id, request_id, {})
            if self.store is not None:
                applied = self.store.save_assignment_effect(item, request_id, effect_key)
                if not applied:
                    item.state = previous_state
            return item

    def load_snapshot(self, rows):
        with self._lock:
            from .models import Assignment
            from .clock import parse_time

            for row in rows:
                self.items[row["assignment_id"]] = Assignment(
                    assignment_id=row["assignment_id"],
                    event_id=row["event_id"],
                    team_id=row["team_id"],
                    region=row.get("region") or "",
                    state=row["state"],
                    quantity=int(row["quantity"]),
                    updated_at=parse_time(row["updated_at"]) if row.get("updated_at") else None,
                )
