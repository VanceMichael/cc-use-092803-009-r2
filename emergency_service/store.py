import json
import sqlite3
import threading
from pathlib import Path


def _dumps(value):
    return json.dumps(value, ensure_ascii=False, default=str)


class StateStore:
    """SQLite 持久化。

    运行期内存对象是事实来源，这里保存三类数据：
    - requests：请求先占与返回值，保证同一 request_id 只生效一次；
    - 领域快照（events/teams/lots/assignments）：重启后重建内存；
    - effects/pending/audit：崩溃恢复时去重副作用、重放未决请求、还原审计链。
    """

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        # 平台可能多线程提交，SQLite 连接随平台锁串行使用。
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS requests "
            "(request_id TEXT PRIMARY KEY, status TEXT NOT NULL, action TEXT, result TEXT)"
        )
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoints (name TEXT PRIMARY KEY, sequence INTEGER NOT NULL)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events "
            "(region TEXT NOT NULL, event_id TEXT NOT NULL, kind TEXT, severity INTEGER, "
            "occurred_at TEXT, source TEXT, status TEXT NOT NULL, version INTEGER NOT NULL, "
            "metadata TEXT, PRIMARY KEY(region, event_id))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS teams "
            "(team_id TEXT PRIMARY KEY, region TEXT, skills TEXT, capacity INTEGER, active INTEGER)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS lots "
            "(lot_id TEXT PRIMARY KEY, item TEXT, quantity INTEGER, reserved INTEGER, frozen INTEGER)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS assignments "
            "(assignment_id TEXT PRIMARY KEY, event_id TEXT, region TEXT, team_id TEXT, "
            "state TEXT, quantity INTEGER, updated_at TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS effects "
            "(request_id TEXT NOT NULL, effect_key TEXT NOT NULL, PRIMARY KEY(request_id, effect_key))"
        )
        self.db.execute("CREATE TABLE IF NOT EXISTS pending (request_id TEXT PRIMARY KEY, action TEXT NOT NULL, payload TEXT NOT NULL)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS movements "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, lot_id TEXT, event_id TEXT, "
            "direction TEXT, amount INTEGER)"
        )
        # 上次进程崩溃时停在 processing 的先占已失效；其已落库的 effects 保留，
        # 重放 pending 意图时据此跳过已生效的副作用。
        self.db.execute("DELETE FROM requests WHERE status='processing'")
        self.db.commit()
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS audit_log "
            "(sequence INTEGER PRIMARY KEY, actor TEXT, action TEXT, entity TEXT, entity_id TEXT, "
            "request_id TEXT, detail TEXT, created_at TEXT)"
        )
        # 同一请求对同一实体的同一动作只审计一次；崩溃重放据此去重。
        self.db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_request_action "
            "ON audit_log(request_id, action, entity, entity_id)"
        )
        self.db.commit()

    # ---- 请求先占 ----

    def claim_request(self, request_id, action):
        """先占 request_id。

        返回：
        - {"status": "new"}：本线程抢到，可执行业务；
        - {"status": "processing"}：同号请求正在另一路执行（并发/重试）；
        - {"status": "done", "result": ...}：同号请求已完成，直接回灌结果。
        """
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO requests(request_id,status,action) VALUES(?,?,?)",
                    (request_id, "processing", action),
                )
                self.db.commit()
                return {"status": "new"}
            except sqlite3.IntegrityError:
                row = self.db.execute(
                    "SELECT status,result FROM requests WHERE request_id=?", (request_id,)
                ).fetchone()
                if row["status"] == "done":
                    return {"status": "done", "result": json.loads(row["result"])}
                return {"status": "processing"}

    def finish_request(self, request_id, result):
        with self._lock:
            self.db.execute(
                "UPDATE requests SET status='done', result=? WHERE request_id=?",
                (_dumps(result), request_id),
            )
            self.db.execute("DELETE FROM pending WHERE request_id=?", (request_id,))
            self.db.commit()
        return result

    def abandon_request(self, request_id):
        """业务执行失败，释放先占并移除未决记录，允许调用方原样重试。"""
        with self._lock:
            self.db.execute("DELETE FROM requests WHERE request_id=? AND status='processing'", (request_id,))
            self.db.execute("DELETE FROM pending WHERE request_id=?", (request_id,))
            self.db.commit()

    def get_request(self, request_id):
        with self._lock:
            row = self.db.execute(
                "SELECT result FROM requests WHERE request_id=? AND status='done'", (request_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def save_request(self, request_id, result):
        # 兼容旧入口：直接落一个已完成的结果。
        with self._lock:
            self.db.execute(
                "INSERT OR IGNORE INTO requests(request_id,status,result) VALUES(?,'done',?)",
                (request_id, _dumps(result)),
            )
            self.db.commit()
            return self.get_request(request_id)

    # ---- 副作用去重（崩溃重放用）----

    def effect_seen(self, request_id, effect_key):
        with self._lock:
            row = self.db.execute(
                "SELECT 1 FROM effects WHERE request_id=? AND effect_key=?", (request_id, effect_key)
            ).fetchone()
            return row is not None

    def mark_effect(self, request_id, effect_key):
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO effects(request_id,effect_key) VALUES(?,?)", (request_id, effect_key)
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def save_team_effect(self, team, request_id, effect_key):
        """原子地落队伍快照并登记副作用；返回 True 表示首次生效。"""
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO effects(request_id,effect_key) VALUES(?,?)", (request_id, effect_key)
                )
            except sqlite3.IntegrityError:
                return False
            self.db.execute(
                "INSERT INTO teams(team_id,region,skills,capacity,active) VALUES(?,?,?,?,?) "
                "ON CONFLICT(team_id) DO UPDATE SET region=excluded.region,skills=excluded.skills,"
                "capacity=excluded.capacity,active=excluded.active",
                (team.team_id, team.region, _dumps(sorted(team.skills)), team.capacity, 1 if team.active else 0),
            )
            self.db.commit()
            return True

    def save_lot_effect(self, lot, request_id, effect_key, movement=None):
        """原子地落物资快照、物资变动轨迹并登记副作用。"""
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO effects(request_id,effect_key) VALUES(?,?)", (request_id, effect_key)
                )
            except sqlite3.IntegrityError:
                return False
            self.db.execute(
                "INSERT INTO lots(lot_id,item,quantity,reserved,frozen) VALUES(?,?,?,?,?) "
                "ON CONFLICT(lot_id) DO UPDATE SET item=excluded.item,quantity=excluded.quantity,"
                "reserved=excluded.reserved,frozen=excluded.frozen",
                (lot.lot_id, lot.item, lot.quantity, lot.reserved, 1 if lot.frozen else 0),
            )
            if movement is not None:
                event_id, direction, amount = movement
                self.db.execute(
                    "INSERT INTO movements(request_id,lot_id,event_id,direction,amount) VALUES(?,?,?,?,?)",
                    (request_id, lot.lot_id, event_id, direction, amount),
                )
            self.db.commit()
            return True

    def save_event_effect(self, event, request_id, effect_key):
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO effects(request_id,effect_key) VALUES(?,?)", (request_id, effect_key)
                )
            except sqlite3.IntegrityError:
                return False
            self._upsert_event_inner(event)
            self.db.commit()
            return True

    def save_assignment_effect(self, item, request_id, effect_key):
        with self._lock:
            try:
                self.db.execute(
                    "INSERT INTO effects(request_id,effect_key) VALUES(?,?)", (request_id, effect_key)
                )
            except sqlite3.IntegrityError:
                return False
            self._upsert_assignment_inner(item)
            self.db.commit()
            return True


    # ---- 未决意图（崩溃时重放）----

    def add_pending(self, request_id, action, payload):
        with self._lock:
            self.db.execute(
                "INSERT OR IGNORE INTO pending(request_id,action,payload) VALUES(?,?,?)",
                (request_id, action, _dumps(payload)),
            )
            self.db.commit()

    def list_pending(self):
        with self._lock:
            rows = self.db.execute("SELECT request_id,action,payload FROM pending ORDER BY rowid").fetchall()
            return [(r["request_id"], r["action"], json.loads(r["payload"])) for r in rows]

    def clear_pending(self, request_id):
        with self._lock:
            self.db.execute("DELETE FROM pending WHERE request_id=?", (request_id,))
            self.db.commit()

    # ---- 物资变动（处置链物资轨迹）----

    def add_movement(self, request_id, lot_id, event_id, direction, amount):
        with self._lock:
            self.db.execute(
                "INSERT INTO movements(request_id,lot_id,event_id,direction,amount) VALUES(?,?,?,?,?)",
                (request_id, lot_id, event_id, direction, amount),
            )
            self.db.commit()

    def movements_for_event(self, event_id):
        with self._lock:
            rows = self.db.execute(
                "SELECT lot_id,direction,amount,request_id FROM movements WHERE event_id=? ORDER BY id",
                (event_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- 检查点（语义保持不变）----

    def save_checkpoint(self, name, sequence):
        self.db.execute(
            "INSERT INTO checkpoints(name,sequence) VALUES(?,?) "
            "ON CONFLICT(name) DO UPDATE SET sequence=excluded.sequence",
            (name, sequence),
        )
        self.db.commit()

    def load_checkpoint(self, name):
        row = self.db.execute("SELECT sequence FROM checkpoints WHERE name=?", (name,)).fetchone()
        return int(row[0]) if row else 0

    # ---- 领域快照 ----

    def upsert_event(self, event):
        with self._lock:
            self._upsert_event_inner(event)
            self.db.commit()

    def _upsert_event_inner(self, event):
        self.db.execute(
            "INSERT INTO events(region,event_id,kind,severity,occurred_at,source,status,version,metadata) "
            "VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(region,event_id) DO UPDATE SET "
            "kind=excluded.kind,severity=excluded.severity,occurred_at=excluded.occurred_at,"
            "source=excluded.source,status=excluded.status,version=excluded.version,metadata=excluded.metadata",
            (
                event.region,
                event.event_id,
                event.kind,
                event.severity,
                event.occurred_at.isoformat(),
                event.source,
                event.status,
                event.version,
                _dumps(event.metadata),
            ),
        )

    def list_events(self):
        with self._lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM events ORDER BY occurred_at").fetchall()]

    def upsert_team(self, team):
        with self._lock:
            self.db.execute(
                "INSERT INTO teams(team_id,region,skills,capacity,active) VALUES(?,?,?,?,?) "
                "ON CONFLICT(team_id) DO UPDATE SET region=excluded.region,skills=excluded.skills,"
                "capacity=excluded.capacity,active=excluded.active",
                (team.team_id, team.region, _dumps(sorted(team.skills)), team.capacity, 1 if team.active else 0),
            )
            self.db.commit()

    def list_teams(self):
        with self._lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM teams").fetchall()]

    def upsert_lot(self, lot):
        with self._lock:
            self.db.execute(
                "INSERT INTO lots(lot_id,item,quantity,reserved,frozen) VALUES(?,?,?,?,?) "
                "ON CONFLICT(lot_id) DO UPDATE SET item=excluded.item,quantity=excluded.quantity,"
                "reserved=excluded.reserved,frozen=excluded.frozen",
                (lot.lot_id, lot.item, lot.quantity, lot.reserved, 1 if lot.frozen else 0),
            )
            self.db.commit()

    def list_lots(self):
        with self._lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM lots").fetchall()]

    def upsert_assignment(self, item):
        with self._lock:
            self._upsert_assignment_inner(item)
            self.db.commit()

    def _upsert_assignment_inner(self, item):
        self.db.execute(
            "INSERT INTO assignments(assignment_id,event_id,region,team_id,state,quantity,updated_at) "
            "VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(assignment_id) DO UPDATE SET event_id=excluded.event_id,region=excluded.region,"
            "team_id=excluded.team_id,state=excluded.state,quantity=excluded.quantity,"
            "updated_at=excluded.updated_at",
            (
                item.assignment_id,
                item.event_id,
                item.region,
                item.team_id,
                item.state,
                item.quantity,
                item.updated_at.isoformat() if item.updated_at else None,
            ),
        )

    def list_assignments(self):
        with self._lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM assignments").fetchall()]

    # ---- 审计持久化 ----

    def append_audit(self, entry):
        with self._lock:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO audit_log(sequence,actor,action,entity,entity_id,request_id,detail,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    entry.sequence,
                    entry.actor,
                    entry.action,
                    entry.entity,
                    entry.entity_id,
                    entry.request_id,
                    _dumps(entry.detail),
                    entry.created_at.isoformat(),
                ),
            )
            self.db.commit()
            return cur.rowcount == 1

    def list_audit(self):
        with self._lock:
            rows = self.db.execute("SELECT * FROM audit_log ORDER BY sequence").fetchall()
            return [
                {
                    "sequence": r["sequence"],
                    "actor": r["actor"],
                    "action": r["action"],
                    "entity": r["entity"],
                    "entity_id": r["entity_id"],
                    "request_id": r["request_id"],
                    "detail": json.loads(r["detail"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def close(self):
        with self._lock:
            self.db.close()
