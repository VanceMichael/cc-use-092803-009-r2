import threading

from .clock import parse_time
from .errors import Conflict, InvalidTransition, NotFound


class EventRegister:
    """事件登记册。

    灾害的自然键是 (region, event_id)：外部事件号只在来源地区内唯一，
    不同地区的同号事件是两起不同灾害，绝不能合并。
    """

    def __init__(self, audit, store=None):
        # 键：(region, event_id)
        self.events = {}
        # event_id -> 该号出现过的地区集合，用于对跨区同号给出明确错误
        self._ids = {}
        self.audit = audit
        self.store = store
        self._lock = threading.RLock()

    @staticmethod
    def _key(event):
        return event.region, event.event_id

    def create(self, event, request_id):
        with self._lock:
            key = self._key(event)
            if key in self.events:
                existing = self.events[key]
                # 同地区同号：只接受同一来源事件的重复送达，返回既有记录，
                # 不重复建链、不重复审计。
                if existing.source == event.source and existing.occurred_at == event.occurred_at:
                    return existing
                raise Conflict("事件编号与来源不一致")
            # 同号事件出现在不同地区是另一起灾害：自然键 (region,event_id)
            # 已将其分开，允许登记，绝不合并。
            self.events[key] = event
            self._ids.setdefault(event.event_id, set()).add(event.region)
            self.audit.append("create_event", "event", event.event_id, request_id, {"region": event.region})
            if self.store is not None:
                self.store.upsert_event(event)
            return event

    def get(self, event_id, region=None):
        with self._lock:
            if region is not None:
                key = (region, event_id)
                if key not in self.events:
                    raise NotFound("事件不存在")
                return self.events[key]
            regions = self._ids.get(event_id)
            if not regions:
                raise NotFound("事件不存在")
            if len(regions) > 1:
                raise Conflict("事件编号在多个地区存在，必须指定地区")
            return self.events[(next(iter(regions)), event_id)]

    def change_status(self, event_id, status, request_id, region=None, effect_key=None):
        with self._lock:
            event = self.get(event_id, region)
            if self.store is not None and effect_key is not None:
                if self.store.effect_seen(request_id, effect_key):
                    # 同一请求的崩溃重放：副作用已生效，原样返回，不重复推进版本。
                    return event
            allowed = {
                "open": {"escalated", "closed"},
                "escalated": {"closed"},
                "closed": set(),
            }
            if status not in allowed.get(event.status, set()):
                raise InvalidTransition("事件状态不可转换")
            previous_status, previous_version = event.status, event.version
            event.status = status
            event.version += 1
            self.audit.append(
                "change_event", "event", event_id, request_id, {"status": status, "region": event.region}
            )
            if self.store is not None:
                if effect_key is not None:
                    applied = self.store.save_event_effect(event, request_id, effect_key)
                    if not applied:
                        event.status, event.version = previous_status, previous_version
                else:
                    self.store.upsert_event(event)
            return event

    def replay(self, events):
        """按发生时间顺序重放一批外部事件；重复事件幂等跳过。"""
        ordered = sorted(events, key=lambda item: item.occurred_at)
        count = 0
        for event in ordered:
            before = len(self.events)
            self.create(event, "replay-" + event.region + "-" + event.event_id)
            if len(self.events) > before:
                count += 1
        return count

    def restore(self, rows):
        """重启后从快照重建，不产生审计（审计链由 AuditLog.restore 还原）。"""
        with self._lock:
            for row in rows:
                event = self._from_row(row)
                self.events[(event.region, event.event_id)] = event
                self._ids.setdefault(event.event_id, set()).add(event.region)

    @staticmethod
    def _from_row(row):
        from .models import Event
        import json

        return Event(
            event_id=row["event_id"],
            region=row["region"],
            kind=row["kind"],
            severity=int(row["severity"]),
            occurred_at=parse_time(row["occurred_at"]),
            source=row["source"],
            status=row["status"],
            version=int(row["version"]),
            metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
        )
