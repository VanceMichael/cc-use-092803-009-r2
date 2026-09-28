from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Event:
    event_id: str
    region: str
    kind: str
    severity: int
    occurred_at: datetime
    source: str
    status: str = "open"
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Team:
    team_id: str
    region: str
    skills: set[str]
    capacity: int
    active: bool = True

@dataclass
class SupplyLot:
    lot_id: str
    item: str
    quantity: int
    reserved: int = 0
    frozen: bool = False

@dataclass
class Assignment:
    assignment_id: str
    event_id: str
    team_id: str
    state: str = "planned"
    quantity: int = 0
    updated_at: datetime | None = None

@dataclass
class AuditEntry:
    sequence: int
    actor: str
    action: str
    entity: str
    entity_id: str
    request_id: str
    detail: dict[str, Any]
    created_at: datetime
