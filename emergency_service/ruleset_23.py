"""第 23 组跨模块处置规则。"""
from dataclasses import dataclass

@dataclass
class Decision:
    accepted: bool
    code: str
    detail: dict

def rule_23_01(context: dict) -> Decision:
    """校验第 23 组的第 1 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2301-OK" if accepted else "R2301-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_02(context: dict) -> Decision:
    """校验第 23 组的第 2 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2302-OK" if accepted else "R2302-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_03(context: dict) -> Decision:
    """校验第 23 组的第 3 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2303-OK" if accepted else "R2303-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_04(context: dict) -> Decision:
    """校验第 23 组的第 4 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2304-OK" if accepted else "R2304-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_05(context: dict) -> Decision:
    """校验第 23 组的第 5 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2305-OK" if accepted else "R2305-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_06(context: dict) -> Decision:
    """校验第 23 组的第 6 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2306-OK" if accepted else "R2306-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_07(context: dict) -> Decision:
    """校验第 23 组的第 7 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2307-OK" if accepted else "R2307-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_08(context: dict) -> Decision:
    """校验第 23 组的第 8 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2308-OK" if accepted else "R2308-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_09(context: dict) -> Decision:
    """校验第 23 组的第 9 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2309-OK" if accepted else "R2309-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_10(context: dict) -> Decision:
    """校验第 23 组的第 10 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2310-OK" if accepted else "R2310-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_11(context: dict) -> Decision:
    """校验第 23 组的第 11 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2311-OK" if accepted else "R2311-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_23_12(context: dict) -> Decision:
    """校验第 23 组的第 12 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2312-OK" if accepted else "R2312-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)
