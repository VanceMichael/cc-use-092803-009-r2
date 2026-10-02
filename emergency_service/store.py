import json
import sqlite3
import threading
from pathlib import Path

class StateStore:
    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        # 允许并发提交从不同线程访问，所有写操作由 _lock 串行化
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self.db.execute("CREATE TABLE IF NOT EXISTS requests (request_id TEXT PRIMARY KEY, result TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS checkpoints (name TEXT PRIMARY KEY, sequence INTEGER NOT NULL)")
            # 崩溃前未确认完成的动作，重启后据此重放
            self.db.execute("CREATE TABLE IF NOT EXISTS journal (request_id TEXT PRIMARY KEY, action TEXT NOT NULL, payload TEXT NOT NULL)")
            # 审计流水持久化，重启后据此重建领域状态
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS audit_entries ("
                "sequence INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, "
                "entity TEXT NOT NULL, entity_id TEXT NOT NULL, request_id TEXT NOT NULL, "
                "detail TEXT NOT NULL, created_at TEXT NOT NULL)")
            self.db.commit()

    def append_audit(self, entry):
        with self._lock:
            self.db.execute(
                "INSERT OR IGNORE INTO audit_entries(sequence,actor,action,entity,entity_id,request_id,detail,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (entry.sequence, entry.actor, entry.action, entry.entity, entry.entity_id,
                 entry.request_id, json.dumps(entry.detail, ensure_ascii=False), entry.created_at.isoformat()))
            self.db.commit()

    def load_audit(self):
        with self._lock:
            rows = self.db.execute(
                "SELECT sequence,actor,action,entity,entity_id,request_id,detail,created_at"
                " FROM audit_entries ORDER BY sequence").fetchall()
            return [{"sequence": r[0], "actor": r[1], "action": r[2], "entity": r[3],
                     "entity_id": r[4], "request_id": r[5], "detail": json.loads(r[6]),
                     "created_at": r[7]} for r in rows]

    def get_request(self, request_id):
        with self._lock:
            row = self.db.execute("SELECT result FROM requests WHERE request_id=?", (request_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def save_request(self, request_id, result):
        with self._lock:
            self.db.execute("INSERT OR IGNORE INTO requests(request_id,result) VALUES(?,?)", (request_id, json.dumps(result, ensure_ascii=False)))
            self.db.commit()
            return self.get_request(request_id)

    def save_pending(self, request_id, action, payload):
        with self._lock:
            self.db.execute("INSERT OR IGNORE INTO journal(request_id,action,payload) VALUES(?,?,?)", (request_id, action, json.dumps(payload, ensure_ascii=False)))
            self.db.commit()

    def clear_pending(self, request_id):
        with self._lock:
            self.db.execute("DELETE FROM journal WHERE request_id=?", (request_id,))
            self.db.commit()

    def load_pending(self):
        with self._lock:
            rows = self.db.execute("SELECT request_id, action, payload FROM journal ORDER BY rowid").fetchall()
            return [(row[0], row[1], json.loads(row[2])) for row in rows]

    def save_checkpoint(self, name, sequence):
        with self._lock:
            self.db.execute("INSERT INTO checkpoints(name,sequence) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET sequence=excluded.sequence", (name, sequence))
            self.db.commit()

    def load_checkpoint(self, name):
        with self._lock:
            row = self.db.execute("SELECT sequence FROM checkpoints WHERE name=?", (name,)).fetchone()
            return int(row[0]) if row else 0

    def close(self):
        with self._lock:
            self.db.close()
