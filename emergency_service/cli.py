import json
import sys
from .auth import Principal
from .models import Event
from .service import EmergencyPlatform

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return 2
    item = json.loads(raw)
    platform = EmergencyPlatform(item.get("db", ":memory:"))
    principal = Principal(str(item.get("actor", "operator")), frozenset(item.get("roles", ["commander"])), frozenset(item.get("regions", ["global"])))
    if item.get("action") == "create_event":
        from .clock import parse_time
        event = Event(str(item["event_id"]), str(item["region"]), str(item.get("kind", "rain")), int(item.get("severity", 1)), parse_time(item["occurred_at"]), str(item.get("source", "manual")))
        result = platform.create_event(principal, event, str(item["request_id"]))
    else:
        result = {"error": "unsupported action"}
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
