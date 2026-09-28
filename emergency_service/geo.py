from dataclasses import dataclass
from .errors import Conflict

@dataclass(frozen=True)
class RiskZone:
    zone_id: str
    region: str
    threshold: float
    active: bool = True

class RiskMap:
    def __init__(self, audit):
        self.audit = audit
        self.zones = {}
        self.observations = {}

    def add_zone(self, zone, request_id):
        if zone.zone_id in self.zones:
            raise Conflict("风险区已存在")
        if zone.threshold <= 0:
            raise ValueError("阈值必须为正")
        self.zones[zone.zone_id] = zone
        self.audit.append("add_zone", "zone", zone.zone_id, request_id, {"threshold": zone.threshold})
        return zone

    def observe(self, zone_id, rainfall, observed_at, request_id):
        if zone_id not in self.zones:
            raise KeyError(zone_id)
        if rainfall < 0:
            raise ValueError("雨量不能为负")
        previous = self.observations.get(zone_id)
        if previous and observed_at < previous[0]:
            raise ValueError("观测时间不能倒退")
        self.observations[zone_id] = (observed_at, rainfall)
        triggered = rainfall >= self.zones[zone_id].threshold
        self.audit.append("observe_rainfall", "zone", zone_id, request_id, {"rainfall": rainfall, "triggered": triggered})
        return triggered

    def active_zones(self, region=None):
        return [zone for zone in self.zones.values() if zone.active and (region is None or zone.region == region)]
