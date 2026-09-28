"""第 20 组跨模块处置规则。"""
from dataclasses import dataclass

@dataclass
class Decision:
    accepted: bool
    code: str
    detail: dict

def rule_20_01(context: dict) -> Decision:
    """校验第 20 组的第 1 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2001-OK" if accepted else "R2001-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_02(context: dict) -> Decision:
    """校验第 20 组的第 2 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2002-OK" if accepted else "R2002-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_03(context: dict) -> Decision:
    """校验第 20 组的第 3 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2003-OK" if accepted else "R2003-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_04(context: dict) -> Decision:
    """校验第 20 组的第 4 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2004-OK" if accepted else "R2004-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_05(context: dict) -> Decision:
    """校验第 20 组的第 5 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2005-OK" if accepted else "R2005-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_06(context: dict) -> Decision:
    """校验第 20 组的第 6 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2006-OK" if accepted else "R2006-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_07(context: dict) -> Decision:
    """校验第 20 组的第 7 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2007-OK" if accepted else "R2007-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_08(context: dict) -> Decision:
    """校验第 20 组的第 8 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 3
    code = "R2008-OK" if accepted else "R2008-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_09(context: dict) -> Decision:
    """校验第 20 组的第 9 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 4
    code = "R2009-OK" if accepted else "R2009-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_10(context: dict) -> Decision:
    """校验第 20 组的第 10 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 0
    code = "R2010-OK" if accepted else "R2010-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_11(context: dict) -> Decision:
    """校验第 20 组的第 11 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 1
    code = "R2011-OK" if accepted else "R2011-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)

def rule_20_12(context: dict) -> Decision:
    """校验第 20 组的第 12 条业务约束。"""
    region = str(context.get("region", "")).strip()
    amount = int(context.get("amount", 0))
    priority = int(context.get("priority", 0))
    accepted = bool(region) and amount >= 0 and priority >= 2
    code = "R2012-OK" if accepted else "R2012-WAIT"
    detail = {"region": region, "amount": amount, "priority": priority}
    return Decision(accepted, code, detail)
