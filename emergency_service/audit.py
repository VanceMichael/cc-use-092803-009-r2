from contextlib import contextmanager
from datetime import datetime
from .clock import utc_now
from .models import AuditEntry

class AuditLog:
    def __init__(self):
        self.entries = []
        self._sequence = 0
        # 持久化回调（落盘到 SQLite），重启后据此重建
        self._sink = None
        # 重放历史流水期间只重建状态，不再新增审计条目
        self._restoring = False

    def set_sink(self, sink):
        self._sink = sink

    @contextmanager
    def rewriting(self):
        previous = self._restoring
        self._restoring = True
        try:
            yield
        finally:
            self._restoring = previous

    def append(self, action, entity, entity_id, request_id, detail):
        if self._restoring:
            # 重建回放期间不新增审计、不自增序号（序号已由 restore 设定）
            return None
        self._sequence += 1
        entry = AuditEntry(self._sequence, "system", action, entity, entity_id, request_id, dict(detail), utc_now())
        self.entries.append(entry)
        if self._sink is not None:
            self._sink(entry)
        return entry

    def for_entity(self, entity, entity_id):
        return [entry for entry in self.entries if entry.entity == entity and entry.entity_id == entity_id]

    def after(self, sequence):
        return [entry for entry in self.entries if entry.sequence > sequence]

    def restore(self, rows):
        """用持久化的审计流水重建内存审计，保持原有序号与时间。"""
        self.entries = [
            AuditEntry(r["sequence"], r["actor"], r["action"], r["entity"], r["entity_id"],
                       r["request_id"], r["detail"], datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]
        self._sequence = max((r["sequence"] for r in rows), default=0)

    def export(self):
        return [{"sequence": e.sequence, "action": e.action, "entity": e.entity, "entity_id": e.entity_id, "request_id": e.request_id, "detail": e.detail, "created_at": e.created_at.isoformat()} for e in self.entries]
