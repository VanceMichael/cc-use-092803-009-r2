from .errors import Conflict, InvalidTransition, NotFound

class EventRegister:
    """以 (地区, 外部事件号) 作为事件自然键。

    外部系统在不同地区可能复用同一个事件号，仅凭 event_id 判重会把
    异地同号事件误并，或把同一灾害的重复上报误判为冲突。
    """

    def __init__(self, audit):
        self.events = {}
        # event_id -> {(region, event_id): Event} 的索引，便于按号查找
        self._by_event_id = {}
        self.audit = audit
        # 已经生效的状态变更请求，保证重放时幂等
        self._status_requests = {}

    @staticmethod
    def key_of(event):
        return (event.region, event.event_id)

    def create(self, event, request_id):
        key = self.key_of(event)
        if key in self.events:
            existing = self.events[key]
            if existing.source != event.source:
                raise Conflict("事件编号与来源不一致")
            # 同一灾害的重复上报/重放：幂等返回既有事件，不再写审计
            return existing
        self.events[key] = event
        self._by_event_id.setdefault(event.event_id, {})[event.region] = event
        self.audit.append("create_event", "event", event.event_id, request_id,
                          {"region": event.region, "kind": event.kind, "severity": event.severity,
                           "occurred_at": event.occurred_at.isoformat(), "source": event.source})
        return event

    def get(self, event_id, region=None):
        if region is not None:
            event = self.events.get((region, event_id))
            if event is None:
                raise NotFound("事件不存在")
            return event
        candidates = self._by_event_id.get(event_id, {})
        if not candidates:
            raise NotFound("事件不存在")
        if len(candidates) > 1:
            raise Conflict("同一事件号分属多个地区，需要指定地区")
        return next(iter(candidates.values()))

    def change_status(self, event_id, status, request_id, region=None):
        event = self.get(event_id, region)
        seen = self._status_requests.get(request_id)
        if seen is not None:
            if seen != ((event.region, event_id), status):
                raise Conflict("重复请求编号对应不同操作")
            return event
        allowed = {"open": {"escalated", "closed"}, "escalated": {"closed"}, "closed": set()}
        # 目标态幂等：同一状态的重复提交/崩溃重放直接返回，不重复累加版本
        if event.status == status:
            self._status_requests[request_id] = ((event.region, event_id), status)
            return event
        if status not in allowed.get(event.status, set()):
            raise InvalidTransition("事件状态不可转换")
        event.status = status
        event.version += 1
        self._status_requests[request_id] = ((event.region, event_id), status)
        self.audit.append("change_event", "event", event_id, request_id, {"status": status, "region": event.region})
        return event

    def replay(self, events):
        ordered = sorted(events, key=lambda item: item.occurred_at)
        for event in ordered:
            # 确定性的请求编号：同一批事件重放任意次都只产生一条链
            self.create(event, "replay-" + event.region + "-" + event.event_id)
        return len(ordered)
