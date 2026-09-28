import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

class StateStore:
    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS requests (request_id TEXT PRIMARY KEY, result TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoints (name TEXT PRIMARY KEY, sequence INTEGER NOT NULL)")
        self.db.commit()

    def get_request(self, request_id):
        row = self.db.execute("SELECT result FROM requests WHERE request_id=?", (request_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_request(self, request_id, result):
        self.db.execute("INSERT OR IGNORE INTO requests(request_id,result) VALUES(?,?)", (request_id, json.dumps(result, ensure_ascii=False)))
        self.db.commit()
        return self.get_request(request_id)

    def save_checkpoint(self, name, sequence):
        self.db.execute("INSERT INTO checkpoints(name,sequence) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET sequence=excluded.sequence", (name, sequence))
        self.db.commit()

    def load_checkpoint(self, name):
        row = self.db.execute("SELECT sequence FROM checkpoints WHERE name=?", (name,)).fetchone()
        return int(row[0]) if row else 0

    def close(self):
        self.db.close()
