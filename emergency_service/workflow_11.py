def step_11_01(context: dict) -> dict:
    """处理第 11 组流程中的第 1 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-01"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_02(context: dict) -> dict:
    """处理第 11 组流程中的第 2 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-02"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_03(context: dict) -> dict:
    """处理第 11 组流程中的第 3 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-03"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_04(context: dict) -> dict:
    """处理第 11 组流程中的第 4 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-04"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_05(context: dict) -> dict:
    """处理第 11 组流程中的第 5 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-05"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_06(context: dict) -> dict:
    """处理第 11 组流程中的第 6 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-06"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_07(context: dict) -> dict:
    """处理第 11 组流程中的第 7 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-07"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_08(context: dict) -> dict:
    """处理第 11 组流程中的第 8 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-08"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_09(context: dict) -> dict:
    """处理第 11 组流程中的第 9 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-09"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_10(context: dict) -> dict:
    """处理第 11 组流程中的第 10 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-10"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_11(context: dict) -> dict:
    """处理第 11 组流程中的第 11 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-11"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_11_12(context: dict) -> dict:
    """处理第 11 组流程中的第 12 个确定性检查。"""
    result = dict(context)
    result["policy"] = "11-12"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result
