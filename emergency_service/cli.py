import json
import sys
from .auth import Principal
from .models import Assignment, Event, SupplyLot, Team
from .service import EmergencyPlatform

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return 2
    item = json.loads(raw)
    platform = EmergencyPlatform(item.get("db", ":memory:"))
    principal = Principal(str(item.get("actor", "operator")), frozenset(item.get("roles", ["commander"])), frozenset(item.get("regions", ["global"])))
    request_id = str(item["request_id"])
    action = item.get("action")
    if action == "create_event":
        from .clock import parse_time
        event = Event(str(item["event_id"]), str(item["region"]), str(item.get("kind", "rain")), int(item.get("severity", 1)), parse_time(item["occurred_at"]), str(item.get("source", "manual")))
        result = platform.create_event(principal, event, request_id)
    elif action == "escalate":
        result = platform.escalate(principal, str(item["event_id"]), request_id, item.get("region"))
    elif action == "close":
        result = platform.close(principal, str(item["event_id"]), request_id, item.get("region"))
    elif action == "register_team":
        platform.teams.register(Team(str(item["team_id"]), str(item["region"]), frozenset(item.get("skills", [])), int(item.get("capacity", 1))), request_id)
        result = {"team_id": item["team_id"], "registered": True}
    elif action == "assign":
        assignment = Assignment(str(item["assignment_id"]), str(item["event_id"]), str(item["team_id"]), quantity=int(item.get("quantity", 0)))
        result = platform.assign(principal, assignment, request_id)
    elif action == "acknowledge":
        result = platform.acknowledge(principal, str(item["assignment_id"]), request_id)
    elif action == "cancel_assignment":
        result = platform.cancel_assignment(principal, str(item["assignment_id"]), request_id)
    elif action == "add_supply":
        result = platform.add_supply(principal, SupplyLot(str(item["lot_id"]), str(item["item"]), int(item["quantity"])), request_id)
    elif action == "reserve":
        result = platform.reserve(principal, str(item["lot_id"]), int(item["amount"]), request_id, item.get("reservation_id"))
    elif action == "release":
        result = platform.release(principal, str(item["lot_id"]), int(item["amount"]), request_id, item.get("reservation_id"))
    else:
        result = {"error": "unsupported action"}
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
