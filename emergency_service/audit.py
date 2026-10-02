import threading

from .clock import parse_time, utc_now
from .models import AuditEntry


class AuditLog:
    def __init__(self, store=None):
        self.entries = []
        self._sequence = 0
        self._lock = threading.RLock()
        self.store = store

    def append(self, action, entity, entity_id, request_id, detail, actor="system"):
        with self._lock:
            self._sequence += 1
            entry = AuditEntry(
                self._sequence, actor, action, entity, entity_id, request_id, dict(detail), utc_now()
            )
            if self.store is not None:
                inserted = self.store.append_audit(entry)
                if not inserted:
                    # 崩溃重放：该审计已落库（启动时已还原），不重复计数、不入内存。
                    self._sequence -= 1
                    for old in self.entries:
                        if (
                            old.request_id == request_id
                            and old.action == action
                            and old.entity == entity
                            and old.entity_id == entity_id
                        ):
                            return old
                    return entry
            self.entries.append(entry)
            return entry

    def for_entity(self, entity, entity_id):
        with self._lock:
            return [
                entry
                for entry in self.entries
                if entry.entity == entity and entry.entity_id == entity_id
            ]

    def after(self, sequence):
        with self._lock:
            return [entry for entry in self.entries if entry.sequence > sequence]

    def restore(self, rows):
        """重启后按序列号还原审计链，不重复追加已持久化的条目。"""
        with self._lock:
            known = {entry.sequence for entry in self.entries}
            for row in rows:
                if row["sequence"] in known:
                    continue
                entry = AuditEntry(
                    row["sequence"],
                    row.get("actor", "system"),
                    row["action"],
                    row["entity"],
                    row["entity_id"],
                    row["request_id"],
                    dict(row["detail"]),
                    parse_time(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
                )
                self.entries.append(entry)
                known.add(entry.sequence)
            self.entries.sort(key=lambda e: e.sequence)
            self._sequence = max((e.sequence for e in self.entries), default=0)

    def export(self):
        with self._lock:
            return [
                {
                    "sequence": e.sequence,
                    "action": e.action,
                    "entity": e.entity,
                    "entity_id": e.entity_id,
                    "request_id": e.request_id,
                    "detail": e.detail,
                    "created_at": e.created_at.isoformat(),
                }
                for e in self.entries
            ]
