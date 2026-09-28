"""第 22 组跨模块处置规则。"""
from dataclasses import dataclass

@dataclass
class Decision:
    accepted: bool
    code: str
    detail: dict

def rule_22_01(context: dict) -> Decision:
    """校验第 22 组的第 1 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2201-OK" if accepted else "R2201-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_02(context: dict) -> Decision:
    """校验第 22 组的第 2 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2202-OK" if accepted else "R2202-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_03(context: dict) -> Decision:
    """校验第 22 组的第 3 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2203-OK" if accepted else "R2203-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_04(context: dict) -> Decision:
    """校验第 22 组的第 4 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2204-OK" if accepted else "R2204-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_05(context: dict) -> Decision:
    """校验第 22 组的第 5 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2205-OK" if accepted else "R2205-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_06(context: dict) -> Decision:
    """校验第 22 组的第 6 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2206-OK" if accepted else "R2206-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_07(context: dict) -> Decision:
    """校验第 22 组的第 7 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2207-OK" if accepted else "R2207-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_08(context: dict) -> Decision:
    """校验第 22 组的第 8 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2208-OK" if accepted else "R2208-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_09(context: dict) -> Decision:
    """校验第 22 组的第 9 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2209-OK" if accepted else "R2209-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_10(context: dict) -> Decision:
    """校验第 22 组的第 10 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2210-OK" if accepted else "R2210-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_11(context: dict) -> Decision:
    """校验第 22 组的第 11 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2211-OK" if accepted else "R2211-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_22_12(context: dict) -> Decision:
    """校验第 22 组的第 12 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2212-OK" if accepted else "R2212-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)
