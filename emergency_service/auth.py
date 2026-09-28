from dataclasses import dataclass
from .errors import PermissionDenied

@dataclass(frozen=True)
class Principal:
    actor_id: str
    roles: frozenset[str]
    regions: frozenset[str]

ROLE_ACTIONS = {
    "dispatcher": {"assign", "release", "plan"},
    "commander": {"close", "escalate", "freeze", "plan"},
    "auditor": {"read_audit", "read"},
    "warehouse": {"reserve", "release", "read"},
}

def can(principal: Principal, action: str, region: str) -> bool:
    if principal.regions and region not in principal.regions and "global" not in principal.regions:
        return False
    return any(action in ROLE_ACTIONS.get(role, set()) for role in principal.roles)

def require(principal: Principal, action: str, region: str) -> None:
    if not can(principal, action, region):
        raise PermissionDenied(f"{principal.actor_id} 无权执行 {action}")
