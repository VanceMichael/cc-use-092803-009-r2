from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("时间必须包含时区")
    return parsed.astimezone(timezone.utc)

def ensure_order(previous: datetime | None, current: datetime) -> None:
    if previous and current < previous:
        raise ValueError("事件时间不能倒退")
