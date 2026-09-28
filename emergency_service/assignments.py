from .errors import Conflict, InvalidTransition, NotFound

class AssignmentBoard:
    def __init__(self, events, teams, audit):
        self.events = events
        self.teams = teams
        self.audit = audit
        self.items = {}

    def plan(self, assignment, request_id):
        if assignment.assignment_id in self.items:
            old = self.items[assignment.assignment_id]
            if old.event_id == assignment.event_id and old.team_id == assignment.team_id:
                return old
            raise Conflict("派单编号冲突")
        event = self.events.get(assignment.event_id)
        if event.status == "closed":
            raise InvalidTransition("关闭事件不能派单")
        self.teams.consume(assignment.team_id, max(1, assignment.quantity), request_id)
        self.items[assignment.assignment_id] = assignment
        self.audit.append("plan_assignment", "assignment", assignment.assignment_id, request_id, {"event_id": assignment.event_id})
        return assignment

    def get(self, assignment_id):
        if assignment_id not in self.items:
            raise NotFound("派单不存在")
        return self.items[assignment_id]

    def acknowledge(self, assignment_id, request_id):
        item = self.get(assignment_id)
        if item.state != "planned":
            raise InvalidTransition("派单不是待确认状态")
        item.state = "acknowledged"
        self.audit.append("ack_assignment", "assignment", assignment_id, request_id, {})
        return item

    def complete(self, assignment_id, request_id):
        item = self.get(assignment_id)
        if item.state != "acknowledged":
            raise InvalidTransition("派单尚未确认")
        item.state = "completed"
        self.audit.append("complete_assignment", "assignment", assignment_id, request_id, {})
        return item

    def cancel(self, assignment_id, request_id):
        item = self.get(assignment_id)
        if item.state in {"completed", "cancelled"}:
            raise InvalidTransition("派单不能取消")
        item.state = "cancelled"
        self.teams.restore(item.team_id, max(1, item.quantity), request_id)
        self.audit.append("cancel_assignment", "assignment", assignment_id, request_id, {})
        return item
