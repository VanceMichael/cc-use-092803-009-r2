"""第 9 类应急协同策略。"""
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class PolicyDecision:
    policy_id: str
    accepted: bool
    reason: str
    evidence: dict

def evaluate_09(payload: dict) -> PolicyDecision:
    policy_id = "policy-09"
    amount = int(payload.get("amount", 0))
    priority = int(payload.get("priority", 0))
    region = str(payload.get("region", ""))
    if not region:
        return PolicyDecision(policy_id, False, "缺少区域", {})
    if amount < 0 or priority < 0:
        return PolicyDecision(policy_id, False, "数值不能为负", {"amount": amount, "priority": priority})
    accepted = priority >= 1 and amount <= 140
    return PolicyDecision(policy_id, accepted, "通过" if accepted else "需要复核", {"checked_at": datetime.now(timezone.utc).isoformat(), "region": region, "amount": amount, "priority": priority})
