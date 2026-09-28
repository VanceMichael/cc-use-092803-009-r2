from .clock import utc_now, ensure_order
from .errors import Conflict, InvalidTransition, NotFound

class EventRegister:
    def __init__(self, audit):
        self.events = {}
        self.audit = audit

    def create(self, event, request_id):
        if event.event_id in self.events:
            existing = self.events[event.event_id]
            if existing.source == event.source and existing.occurred_at == event.occurred_at:
                return existing
            raise Conflict("事件编号与来源不一致")
        self.events[event.event_id] = event
        self.audit.append("create_event", "event", event.event_id, request_id, {"region": event.region})
        return event

    def get(self, event_id):
        if event_id not in self.events:
            raise NotFound("事件不存在")
        return self.events[event_id]

    def change_status(self, event_id, status, request_id):
        event = self.get(event_id)
        allowed = {"open": {"escalated", "closed"}, "escalated": {"closed"}, "closed": set()}
        if status not in allowed.get(event.status, set()):
            raise InvalidTransition("事件状态不可转换")
        event.status = status
        event.version += 1
        self.audit.append("change_event", "event", event_id, request_id, {"status": status})
        return event

    def replay(self, events):
        ordered = sorted(events, key=lambda item: item.occurred_at)
        for event in ordered:
            self.create(event, "replay-" + event.event_id)
        return len(ordered)
