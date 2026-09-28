"""第 15 组跨模块处置规则。"""
from dataclasses import dataclass

@dataclass
class Decision:
    accepted: bool
    code: str
    detail: dict

def rule_15_01(context: dict) -> Decision:
    """校验第 15 组的第 1 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1501-OK" if accepted else "R1501-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_02(context: dict) -> Decision:
    """校验第 15 组的第 2 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1502-OK" if accepted else "R1502-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_03(context: dict) -> Decision:
    """校验第 15 组的第 3 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R1503-OK" if accepted else "R1503-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_04(context: dict) -> Decision:
    """校验第 15 组的第 4 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R1504-OK" if accepted else "R1504-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_05(context: dict) -> Decision:
    """校验第 15 组的第 5 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R1505-OK" if accepted else "R1505-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_06(context: dict) -> Decision:
    """校验第 15 组的第 6 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1506-OK" if accepted else "R1506-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_07(context: dict) -> Decision:
    """校验第 15 组的第 7 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1507-OK" if accepted else "R1507-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_08(context: dict) -> Decision:
    """校验第 15 组的第 8 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R1508-OK" if accepted else "R1508-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_09(context: dict) -> Decision:
    """校验第 15 组的第 9 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R1509-OK" if accepted else "R1509-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_10(context: dict) -> Decision:
    """校验第 15 组的第 10 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R1510-OK" if accepted else "R1510-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_11(context: dict) -> Decision:
    """校验第 15 组的第 11 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R1511-OK" if accepted else "R1511-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_15_12(context: dict) -> Decision:
    """校验第 15 组的第 12 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R1512-OK" if accepted else "R1512-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)
