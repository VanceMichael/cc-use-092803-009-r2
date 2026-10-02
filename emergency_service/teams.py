import json
import threading

from .errors import CapacityExceeded, Conflict, NotFound


class TeamRegistry:
    def __init__(self, audit, store=None):
        self.teams = {}
        self.audit = audit
        self.store = store
        self._lock = threading.RLock()

    def register(self, team, request_id):
        with self._lock:
            if team.team_id in self.teams:
                raise Conflict("队伍已登记")
            if team.capacity <= 0:
                raise ValueError("队伍容量必须为正")
            self.teams[team.team_id] = team
            self.audit.append(
                "register_team", "team", team.team_id, request_id, {"capacity": team.capacity}
            )
            if self.store is not None:
                self.store.upsert_team(team)
            return team

    def get(self, team_id):
        with self._lock:
            if team_id not in self.teams:
                raise NotFound("队伍不存在")
            return self.teams[team_id]

    def consume(self, team_id, amount, request_id, effect_key=None):
        with self._lock:
            if self.store is not None and effect_key is not None:
                if self.store.effect_seen(request_id, effect_key):
                    return self.get(team_id).capacity
            team = self.get(team_id)
            if amount <= 0 or amount > team.capacity:
                raise CapacityExceeded("队伍可用能力不足")
            team.capacity -= amount
            if self.store is not None and effect_key is not None:
                applied = self.store.save_team_effect(team, request_id, effect_key)
                if not applied:
                    # 并发下副作用已登记：回滚内存扣减，保持与持久层一致。
                    team.capacity += amount
                    return self.get(team_id).capacity
            self.audit.append("consume_team", "team", team_id, request_id, {"amount": amount})
            if self.store is not None and effect_key is None:
                self.store.upsert_team(team)
            return team.capacity

    def restore(self, team_id, amount, request_id, effect_key=None):
        with self._lock:
            if self.store is not None and effect_key is not None:
                if self.store.effect_seen(request_id, effect_key):
                    return self.get(team_id).capacity
            team = self.get(team_id)
            if amount <= 0:
                raise ValueError("恢复量必须为正")
            team.capacity += amount
            self.audit.append("restore_team", "team", team_id, request_id, {"amount": amount})
            if self.store is not None:
                if effect_key is not None:
                    applied = self.store.save_team_effect(team, request_id, effect_key)
                    if not applied:
                        team.capacity -= amount
                else:
                    self.store.upsert_team(team)
            return team.capacity

    def load_snapshot(self, rows):
        with self._lock:
            from .models import Team

            for row in rows:
                self.teams[row["team_id"]] = Team(
                    team_id=row["team_id"],
                    region=row["region"],
                    skills=set(json.loads(row["skills"])) if row.get("skills") else set(),
                    capacity=int(row["capacity"]),
                    active=bool(row["active"]),
                )
