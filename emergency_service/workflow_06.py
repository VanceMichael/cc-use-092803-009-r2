def step_06_01(context: dict) -> dict:
    """处理第 6 组流程中的第 1 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-01"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_02(context: dict) -> dict:
    """处理第 6 组流程中的第 2 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-02"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_03(context: dict) -> dict:
    """处理第 6 组流程中的第 3 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-03"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_04(context: dict) -> dict:
    """处理第 6 组流程中的第 4 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-04"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_05(context: dict) -> dict:
    """处理第 6 组流程中的第 5 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-05"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_06(context: dict) -> dict:
    """处理第 6 组流程中的第 6 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-06"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_07(context: dict) -> dict:
    """处理第 6 组流程中的第 7 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-07"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_08(context: dict) -> dict:
    """处理第 6 组流程中的第 8 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-08"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_09(context: dict) -> dict:
    """处理第 6 组流程中的第 9 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-09"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 1
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_10(context: dict) -> dict:
    """处理第 6 组流程中的第 10 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-10"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 2
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_11(context: dict) -> dict:
    """处理第 6 组流程中的第 11 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-11"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 3
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result

def step_06_12(context: dict) -> dict:
    """处理第 6 组流程中的第 12 个确定性检查。"""
    result = dict(context)
    result["policy"] = "06-12"
    result["valid"] = bool(result.get("region")) and int(result.get("priority", 0)) >= 0
    result["reason"] = "通过" if result["valid"] else "等待补充材料"
    return result
