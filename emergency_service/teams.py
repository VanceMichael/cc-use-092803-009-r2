from .errors import CapacityExceeded, NotFound, Conflict

class TeamRegistry:
    def __init__(self, audit):
        self.teams = {}
        self.audit = audit
        # request_id -> (team_id, action, amount)，保证能力扣减/恢复可安全重试与重建
        self._requests = {}

    def register(self, team, request_id):
        if team.team_id in self.teams:
            raise Conflict("队伍已登记")
        if team.capacity <= 0:
            raise ValueError("队伍容量必须为正")
        self.teams[team.team_id] = team
        self.audit.append("register_team", "team", team.team_id, request_id,
                          {"capacity": team.capacity, "region": team.region,
                           "skills": sorted(team.skills)})
        return team

    def get(self, team_id):
        if team_id not in self.teams:
            raise NotFound("队伍不存在")
        return self.teams[team_id]

    def consume(self, team_id, amount, request_id):
        seen = self._requests.get(request_id)
        if seen is not None:
            if seen[:2] != (team_id, "consume"):
                raise Conflict("重复请求编号对应不同操作")
            return self.get(team_id).capacity
        team = self.get(team_id)
        if amount <= 0 or amount > team.capacity:
            raise CapacityExceeded("队伍可用能力不足")
        team.capacity -= amount
        self._requests[request_id] = (team_id, "consume", amount)
        self.audit.append("consume_team", "team", team_id, request_id, {"amount": amount})
        return team.capacity

    def restore(self, team_id, amount, request_id):
        seen = self._requests.get(request_id)
        if seen is not None:
            if seen[:2] != (team_id, "restore"):
                raise Conflict("重复请求编号对应不同操作")
            return self.get(team_id).capacity
        team = self.get(team_id)
        if amount <= 0:
            raise ValueError("恢复量必须为正")
        team.capacity += amount
        self._requests[request_id] = (team_id, "restore", amount)
        self.audit.append("restore_team", "team", team_id, request_id, {"amount": amount})
        return team.capacity
