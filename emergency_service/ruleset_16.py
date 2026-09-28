"""第 16 组跨模块处置规则。"""
from dataclasses import dataclass

@dataclass
class Decision:
    accepted: bool
    code: str
    detail: dict

def rule_16_01(context: dict) -> Decision:
    """校验第 16 组的第 1 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1601-OK" if accepted else "R1601-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_02(context: dict) -> Decision:
    """校验第 16 组的第 2 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1602-OK" if accepted else "R1602-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_03(context: dict) -> Decision:
    """校验第 16 组的第 3 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R1603-OK" if accepted else "R1603-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_04(context: dict) -> Decision:
    """校验第 16 组的第 4 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R1604-OK" if accepted else "R1604-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_05(context: dict) -> Decision:
    """校验第 16 组的第 5 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R1605-OK" if accepted else "R1605-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_06(context: dict) -> Decision:
    """校验第 16 组的第 6 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1606-OK" if accepted else "R1606-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_07(context: dict) -> Decision:
    """校验第 16 组的第 7 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1607-OK" if accepted else "R1607-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_08(context: dict) -> Decision:
    """校验第 16 组的第 8 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R1608-OK" if accepted else "R1608-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_09(context: dict) -> Decision:
    """校验第 16 组的第 9 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R1609-OK" if accepted else "R1609-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_10(context: dict) -> Decision:
    """校验第 16 组的第 10 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R1610-OK" if accepted else "R1610-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_11(context: dict) -> Decision:
    """校验第 16 组的第 11 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1611-OK" if accepted else "R1611-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_16_12(context: dict) -> Decision:
    """校验第 16 组的第 12 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1612-OK" if accepted else "R1612-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)
