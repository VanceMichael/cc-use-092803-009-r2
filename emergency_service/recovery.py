from .clock import ensure_order

class RecoveryJournal:
    """记录"已开始但未确认完成"的动作。

    动作执行前写入 pending（同时落盘），执行并保存结果后清除。
    重启后把残留 pending 重放一遍：所有领域操作都按 request_id
    幂等，因此重放只会补做崩溃前未完成的副作用，不会重复派单或
    重复锁定物资。
    """

    def __init__(self, audit, store=None):
        self.audit = audit
        self.store = store
        self.checkpoints = {}
        self.pending = []
        if store is not None:
            self.pending = [tuple(item) for item in store.load_pending()]

    def record_pending(self, request_id, action, payload):
        if request_id not in {item[0] for item in self.pending}:
            entry = (request_id, action, dict(payload))
            self.pending.append(entry)
            if self.store is not None:
                self.store.save_pending(request_id, action, entry[2])
        return request_id

    def mark_done(self, request_id):
        self.pending = [item for item in self.pending if item[0] != request_id]
        if self.store is not None:
            self.store.clear_pending(request_id)

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
        remaining = []
        for request_id, action, payload in list(self.pending):
            try:
                handler(action, payload, request_id)
            except Exception:
                # 处理失败的条目保留下来，下次恢复继续尝试
                remaining.append((request_id, action, payload))
                continue
            completed.append(request_id)
            if self.store is not None:
                self.store.clear_pending(request_id)
        self.pending = remaining
        return completed
