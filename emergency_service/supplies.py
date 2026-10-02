from .errors import CapacityExceeded, Conflict, NotFound

class SupplyLedger:
    def __init__(self, audit):
        self.lots = {}
        self.audit = audit
        # request_id -> (lot_id, action, amount)，使锁定/释放请求可安全重试与重放
        self._requests = {}
        # 锁定单号 -> (lot_id, amount, active)，同一灾害的重复锁定只生效一次
        self._reservations = {}

    def _remember(self, request_id, lot_id, action, amount):
        previous = self._requests.get(request_id)
        signature = (lot_id, action, amount)
        if previous is not None and previous != signature:
            raise Conflict("重复请求编号对应不同操作")
        self._requests[request_id] = signature

    def add(self, lot, request_id):
        if lot.lot_id in self.lots:
            raise Conflict("物资批次已存在")
        if lot.quantity < 0:
            raise ValueError("数量不能为负")
        self.lots[lot.lot_id] = lot
        self.audit.append("add_supply", "lot", lot.lot_id, request_id,
                          {"quantity": lot.quantity, "item": lot.item})
        return lot

    def get(self, lot_id):
        if lot_id not in self.lots:
            raise NotFound("物资批次不存在")
        return self.lots[lot_id]

    def reserve(self, lot_id, amount, request_id, reservation_id=None):
        seen = self._requests.get(request_id)
        if seen is not None:
            if seen[:2] != (lot_id, "reserve"):
                raise Conflict("重复请求编号对应不同操作")
            return self.get(lot_id).reserved
        # 同一处置链（灾害/派单）的重复锁定，即使 request_id 不同也只生效一次
        dedup_key = (lot_id, reservation_id) if reservation_id is not None else None
        if dedup_key is not None and dedup_key in self._reservations:
            existing = self._reservations[dedup_key]
            if existing != amount:
                raise Conflict("同一处置链的锁定数量不一致")
            self._remember(request_id, lot_id, "reserve", amount)
            return self.get(lot_id).reserved
        lot = self.get(lot_id)
        if lot.frozen or amount <= 0 or lot.quantity - lot.reserved < amount:
            raise CapacityExceeded("物资不可用")
        lot.reserved += amount
        self._remember(request_id, lot_id, "reserve", amount)
        if dedup_key is not None:
            self._reservations[dedup_key] = amount
        self.audit.append("reserve_supply", "lot", lot_id, request_id,
                          {"amount": amount, "reservation_id": reservation_id})
        return lot.reserved

    def release(self, lot_id, amount, request_id, reservation_id=None):
        seen = self._requests.get(request_id)
        if seen is not None:
            if seen[:2] != (lot_id, "release"):
                raise Conflict("重复请求编号对应不同操作")
            return self.get(lot_id).reserved
        lot = self.get(lot_id)
        dedup_key = (lot_id, reservation_id) if reservation_id is not None else None
        if dedup_key is not None and dedup_key not in self._reservations:
            # 该处置链的锁定已释放过（重试/重放）：幂等返回当前值
            self._remember(request_id, lot_id, "release", amount)
            return lot.reserved
        if amount <= 0 or amount > lot.reserved:
            raise ValueError("释放量超过已锁定数量")
        lot.reserved -= amount
        self._remember(request_id, lot_id, "release", amount)
        if dedup_key is not None:
            del self._reservations[dedup_key]
        self.audit.append("release_supply", "lot", lot_id, request_id,
                          {"amount": amount, "reservation_id": reservation_id})
        return lot.reserved

    def freeze(self, lot_id, request_id):
        seen = self._requests.get(request_id)
        if seen is not None:
            return self.get(lot_id)
        lot = self.get(lot_id)
        lot.frozen = True
        self._remember(request_id, lot_id, "freeze", 0)
        self.audit.append("freeze_supply", "lot", lot_id, request_id, {})
        return lot
