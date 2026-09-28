from .errors import CapacityExceeded, NotFound, Conflict

class TeamRegistry:
    def __init__(self, audit):
        self.teams = {}
        self.audit = audit

    def register(self, team, request_id):
        if team.team_id in self.teams:
            raise Conflict("队伍已登记")
        if team.capacity <= 0:
            raise ValueError("队伍容量必须为正")
        self.teams[team.team_id] = team
        self.audit.append("register_team", "team", team.team_id, request_id, {"capacity": team.capacity})
        return team

    def get(self, team_id):
        if team_id not in self.teams:
            raise NotFound("队伍不存在")
        return self.teams[team_id]

    def consume(self, team_id, amount, request_id):
        team = self.get(team_id)
        if amount <= 0 or amount > team.capacity:
            raise CapacityExceeded("队伍可用能力不足")
        team.capacity -= amount
        self.audit.append("consume_team", "team", team_id, request_id, {"amount": amount})
        return team.capacity

    def restore(self, team_id, amount, request_id):
        team = self.get(team_id)
        if amount <= 0:
            raise ValueError("恢复量必须为正")
        team.capacity += amount
        self.audit.append("restore_team", "team", team_id, request_id, {"amount": amount})
        return team.capacity
