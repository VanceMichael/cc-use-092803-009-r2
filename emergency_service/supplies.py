import threading

from .errors import CapacityExceeded, Conflict, NotFound


class SupplyLedger:
    def __init__(self, audit, store=None):
        self.lots = {}
        self.audit = audit
        self.store = store
        self._lock = threading.RLock()

    def add(self, lot, request_id):
        with self._lock:
            if lot.lot_id in self.lots:
                raise Conflict("物资批次已存在")
            if lot.quantity < 0:
                raise ValueError("数量不能为负")
            self.lots[lot.lot_id] = lot
            self.audit.append("add_supply", "lot", lot.lot_id, request_id, {"quantity": lot.quantity})
            if self.store is not None:
                self.store.upsert_lot(lot)
            return lot

    def get(self, lot_id):
        with self._lock:
            if lot_id not in self.lots:
                raise NotFound("物资批次不存在")
            return self.lots[lot_id]

    def reserve(self, lot_id, amount, request_id, event_id=None, effect_key=None):
        with self._lock:
            effect_key = effect_key or f"reserve:{lot_id}:{request_id}"
            if self.store is not None and self.store.effect_seen(request_id, effect_key):
                return self.get(lot_id).reserved
            lot = self.get(lot_id)
            if lot.frozen or amount <= 0 or lot.quantity - lot.reserved < amount:
                raise CapacityExceeded("物资不可用")
            lot.reserved += amount
            self.audit.append(
                "reserve_supply", "lot", lot_id, request_id,
                {"amount": amount, "event_id": event_id},
            )
            if self.store is not None:
                applied = self.store.save_lot_effect(
                    lot, request_id, effect_key,
                    movement=(event_id, "reserve", amount) if event_id is not None else None,
                )
                if not applied:
                    lot.reserved -= amount
            return lot.reserved

    def release(self, lot_id, amount, request_id, event_id=None, effect_key=None):
        with self._lock:
            effect_key = effect_key or f"release:{lot_id}:{request_id}"
            if self.store is not None and self.store.effect_seen(request_id, effect_key):
                return self.get(lot_id).reserved
            lot = self.get(lot_id)
            if amount <= 0 or amount > lot.reserved:
                raise ValueError("释放量超过已锁定数量")
            lot.reserved -= amount
            self.audit.append(
                "release_supply", "lot", lot_id, request_id,
                {"amount": amount, "event_id": event_id},
            )
            if self.store is not None:
                applied = self.store.save_lot_effect(
                    lot, request_id, effect_key,
                    movement=(event_id, "release", amount) if event_id is not None else None,
                )
                if not applied:
                    lot.reserved += amount
            return lot.reserved

    def freeze(self, lot_id, request_id, effect_key=None):
        with self._lock:
            effect_key = effect_key or f"freeze:{lot_id}:{request_id}"
            if self.store is not None and self.store.effect_seen(request_id, effect_key):
                return self.get(lot_id)
            lot = self.get(lot_id)
            lot.frozen = True
            self.audit.append("freeze_supply", "lot", lot_id, request_id, {})
            if self.store is not None:
                applied = self.store.save_lot_effect(lot, request_id, effect_key)
                if not applied:
                    lot.frozen = False
            return lot

    def movements_for_event(self, event_id):
        if self.store is None:
            return []
        with self._lock:
            return self.store.movements_for_event(event_id)

    def load_snapshot(self, rows):
        with self._lock:
            from .models import SupplyLot

            for row in rows:
                self.lots[row["lot_id"]] = SupplyLot(
                    lot_id=row["lot_id"],
                    item=row["item"],
                    quantity=int(row["quantity"]),
                    reserved=int(row["reserved"]),
                    frozen=bool(row["frozen"]),
                )
