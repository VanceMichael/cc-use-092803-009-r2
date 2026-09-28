from .clock import utc_now
from .models import AuditEntry

class AuditLog:
    def __init__(self):
        self.entries = []
        self._sequence = 0

    def append(self, action, entity, entity_id, request_id, detail):
        self._sequence += 1
        entry = AuditEntry(self._sequence, "system", action, entity, entity_id, request_id, dict(detail), utc_now())
        self.entries.append(entry)
        return entry

    def for_entity(self, entity, entity_id):
        return [entry for entry in self.entries if entry.entity == entity and entry.entity_id == entity_id]

    def after(self, sequence):
        return [entry for entry in self.entries if entry.sequence > sequence]

    def export(self):
        return [{"sequence": e.sequence, "action": e.action, "entity": e.entity, "entity_id": e.entity_id, "request_id": e.request_id, "detail": e.detail, "created_at": e.created_at.isoformat()} for e in self.entries]
