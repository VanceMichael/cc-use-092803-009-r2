import threading


class RecoveryJournal:
    """未决意图日志。

    业务开始前登记意图（落 SQLite），请求正常完成后清除；进程崩溃时残留的
    pending 行在重启后由 drain 重新派发给各 action 的处理函数。处理函数全部
    基于 request_id 与 effect_key 幂等，因此重放不会重复派单或重复锁物资。
    """

    def __init__(self, audit, store=None):
        self.audit = audit
        self.store = store
        self.checkpoints = {}
        self._lock = threading.RLock()
        self.pending = []
        if store is not None:
            self.pending = [(*row,) for row in store.list_pending()]
        self._handlers = {}

    def register_handler(self, action, handler):
        self._handlers[action] = handler

    def record_pending(self, request_id, action, payload):
        with self._lock:
            if request_id not in {item[0] for item in self.pending}:
                self.pending.append((request_id, action, dict(payload)))
            if self.store is not None:
                self.store.add_pending(request_id, action, payload)
            return request_id

    def complete(self, request_id):
        with self._lock:
            self.pending = [item for item in self.pending if item[0] != request_id]
            if self.store is not None:
                self.store.clear_pending(request_id)

    def checkpoint(self, name, sequence):
        previous = self.checkpoints.get(name, 0)
        if sequence < previous:
            raise ValueError("检查点不能倒退")
        self.checkpoints[name] = sequence
        if self.store is not None:
            self.store.save_checkpoint(name, sequence)
        return sequence

    def replayable(self, name):
        boundary = self.checkpoints.get(name, 0)
        if self.store is not None:
            boundary = max(boundary, self.store.load_checkpoint(name))
        return [entry for entry in self.audit.after(boundary)]

    def drain(self, handler=None):
        """重放所有未决意图。

        handler 可选（兼容旧签名）；缺省时按 action 派发给 register_handler
        注册的处理函数。每个请求重放后清除 pending 记录。
        """
        completed = []
        for request_id, action, payload in list(self.pending):
            if handler is not None:
                handler(action, payload, request_id)
            elif action in self._handlers:
                self._handlers[action](payload, request_id)
            else:
                continue
            completed.append(request_id)
            self.complete(request_id)
        return completed
