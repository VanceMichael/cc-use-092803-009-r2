from .errors import CapacityExceeded, Conflict, NotFound

class SupplyLedger:
    def __init__(self, audit):
        self.lots = {}
        self.audit = audit

    def add(self, lot, request_id):
        if lot.lot_id in self.lots:
            raise Conflict("物资批次已存在")
        if lot.quantity < 0:
            raise ValueError("数量不能为负")
        self.lots[lot.lot_id] = lot
        self.audit.append("add_supply", "lot", lot.lot_id, request_id, {"quantity": lot.quantity})
        return lot

    def get(self, lot_id):
        if lot_id not in self.lots:
            raise NotFound("物资批次不存在")
        return self.lots[lot_id]

    def reserve(self, lot_id, amount, request_id):
        lot = self.get(lot_id)
        if lot.frozen or amount <= 0 or lot.quantity - lot.reserved < amount:
            raise CapacityExceeded("物资不可用")
        lot.reserved += amount
        self.audit.append("reserve_supply", "lot", lot_id, request_id, {"amount": amount})
        return lot.reserved

    def release(self, lot_id, amount, request_id):
        lot = self.get(lot_id)
        if amount <= 0 or amount > lot.reserved:
            raise ValueError("释放量超过已锁定数量")
        lot.reserved -= amount
        self.audit.append("release_supply", "lot", lot_id, request_id, {"amount": amount})
        return lot.reserved

    def freeze(self, lot_id, request_id):
        lot = self.get(lot_id)
        lot.frozen = True
        self.audit.append("freeze_supply", "lot", lot_id, request_id, {})
        return lot
