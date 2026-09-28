from .workflow_01 import step_01_01, step_01_02
from .workflow_02 import step_02_01, step_02_02
from .workflow_03 import step_03_01, step_03_02
from .workflow_04 import step_04_01, step_04_02
from .workflow_05 import step_05_01, step_05_02
from .workflow_06 import step_06_01, step_06_02
from .workflow_07 import step_07_01, step_07_02
from .workflow_08 import step_08_01, step_08_02
from .workflow_09 import step_09_01, step_09_02
from .workflow_10 import step_10_01, step_10_02
from .workflow_11 import step_11_01, step_11_02
from .workflow_12 import step_12_01, step_12_02

def evaluate_chain(payload: dict) -> dict:
    value = dict(payload)
    value = step_01_02(value)
    value = step_02_02(value)
    value = step_03_02(value)
    value = step_04_02(value)
    value = step_05_02(value)
    value = step_06_02(value)
    value = step_07_02(value)
    value = step_08_02(value)
    value = step_09_02(value)
    value = step_10_02(value)
    value = step_11_02(value)
    value = step_12_02(value)
    return value
