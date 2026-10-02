from .errors import Conflict, InvalidTransition, NotFound

class AssignmentBoard:
    def __init__(self, events, teams, audit):
        self.events = events
        self.teams = teams
        self.audit = audit
        self.items = {}
        # request_id -> (assignment_id, action)，保证重试/重放不产生重复派单
        self._requests = {}

    def _remember(self, request_id, assignment_id, action):
        previous = self._requests.get(request_id)
        if previous is not None and previous != (assignment_id, action):
            raise Conflict("重复请求编号对应不同操作")
        self._requests[request_id] = (assignment_id, action)

    def plan(self, assignment, request_id):
        seen = self._requests.get(request_id)
        if seen is not None:
            return self.items[seen[0]]
        if assignment.assignment_id in self.items:
            old = self.items[assignment.assignment_id]
            if old.event_id == assignment.event_id and old.team_id == assignment.team_id:
                self._remember(request_id, assignment.assignment_id, "plan")
                return old
            raise Conflict("派单编号冲突")
        # 同一外部事件号可能分属不同地区，按队伍所属地区取本区事件，
        # 避免把异地同号事件的派单挂到同一条处置链上
        team = self.teams.get(assignment.team_id)
        event = self.events.get(assignment.event_id, team.region)
        # 同一队伍针对同一地区同一灾害只允许一条在途派单：
        # 不同派单号的重复提交不得把队伍再次派往同一地点
        for other in self.items.values():
            if (other.team_id == assignment.team_id
                    and other.event_id == event.event_id
                    and (other.region or team.region) == event.region
                    and other.state in {"planned", "acknowledged"}):
                raise Conflict("该队伍已派往此灾害")
        if event.status == "closed":
            raise InvalidTransition("关闭事件不能派单")
        assignment.region = event.region
        self.teams.consume(assignment.team_id, max(1, assignment.quantity), request_id)
        self.items[assignment.assignment_id] = assignment
        self._remember(request_id, assignment.assignment_id, "plan")
        self.audit.append("plan_assignment", "assignment", assignment.assignment_id, request_id,
                          {"event_id": assignment.event_id, "team_id": assignment.team_id,
                           "region": team.region, "quantity": assignment.quantity})
        return assignment

    def get(self, assignment_id):
        if assignment_id not in self.items:
            raise NotFound("派单不存在")
        return self.items[assignment_id]

    def acknowledge(self, assignment_id, request_id):
        item = self.get(assignment_id)
        seen = self._requests.get(request_id)
        if seen is not None:
            return item
        changed = False
        if item.state == "planned":
            item.state = "acknowledged"
            item.updated_at = self._now()
            changed = True
        elif item.state in {"acknowledged", "completed"}:
            # 崩溃重放或重复提交：确认效果已达成，不再重复记账
            pass
        else:
            raise InvalidTransition("派单不是待确认状态")
        self._remember(request_id, assignment_id, "acknowledge")
        if changed:
            self.audit.append("ack_assignment", "assignment", assignment_id, request_id, {})
        return item

    def complete(self, assignment_id, request_id):
        item = self.get(assignment_id)
        seen = self._requests.get(request_id)
        if seen is not None:
            return item
        changed = False
        if item.state == "acknowledged":
            item.state = "completed"
            item.updated_at = self._now()
            changed = True
        elif item.state == "completed":
            # 完成效果已达成，重放幂等
            pass
        else:
            raise InvalidTransition("派单尚未确认")
        self._remember(request_id, assignment_id, "complete")
        if changed:
            self.audit.append("complete_assignment", "assignment", assignment_id, request_id, {})
        return item

    def cancel(self, assignment_id, request_id):
        item = self.get(assignment_id)
        seen = self._requests.get(request_id)
        if seen is not None:
            # 撤销请求重放：能力已归还，直接返回当前状态
            return item
        if item.state == "cancelled":
            # 崩溃重放：能力此前已归还，直接返回，不能再次 restore
            self._remember(request_id, assignment_id, "cancel")
            return item
        if item.state == "completed":
            raise InvalidTransition("派单不能取消")
        item.state = "cancelled"
        item.updated_at = self._now()
        self.teams.restore(item.team_id, max(1, item.quantity), request_id)
        self._remember(request_id, assignment_id, "cancel")
        self.audit.append("cancel_assignment", "assignment", assignment_id, request_id, {})
        return item

    @staticmethod
    def _now():
        from .clock import utc_now
        return utc_now()
