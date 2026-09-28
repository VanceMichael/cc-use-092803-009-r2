from .clock import ensure_order

class RecoveryJournal:
    def __init__(self, audit):
        self.audit = audit
        self.checkpoints = {}
        self.pending = []

    def record_pending(self, request_id, action, payload):
        if request_id not in {item[0] for item in self.pending}:
            self.pending.append((request_id, action, dict(payload)))
        return request_id

    def checkpoint(self, name, sequence):
        previous = self.checkpoints.get(name, 0)
        if sequence < previous:
            raise ValueError("检查点不能倒退")
        self.checkpoints[name] = sequence
        return sequence

    def replayable(self, name):
        boundary = self.checkpoints.get(name, 0)
        return [entry for entry in self.audit.after(boundary)]

    def drain(self, handler):
        completed = []
        for request_id, action, payload in list(self.pending):
            handler(action, payload, request_id)
            completed.append(request_id)
        self.pending = [item for item in self.pending if item[0] not in completed]
        return completed
