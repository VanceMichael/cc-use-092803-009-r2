from dataclasses import dataclass, field
from .errors import Conflict, InvalidTransition

@dataclass
class ActionPlan:
    plan_id: str
    region: str
    dependencies: dict[str, set[str]] = field(default_factory=dict)
    state: str = "draft"
    completed: set[str] = field(default_factory=set)

class PlanBook:
    def __init__(self, audit):
        self.audit = audit
        self.plans = {}

    def create(self, plan, request_id):
        if plan.plan_id in self.plans:
            raise Conflict("行动计划已存在")
        self._validate_graph(plan.dependencies)
        self.plans[plan.plan_id] = plan
        self.audit.append("create_plan", "plan", plan.plan_id, request_id, {"region": plan.region})
        return plan

    def _validate_graph(self, graph):
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting:
                raise ValueError("行动依赖存在环")
            if node in visited:
                return
            visiting.add(node)
            for parent in graph.get(node, set()):
                visit(parent)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)

    def ready(self, plan_id):
        plan = self.plans[plan_id]
        return [node for node, parents in plan.dependencies.items() if node not in plan.completed and parents <= plan.completed]

    def start(self, plan_id, request_id):
        plan = self.plans[plan_id]
        if plan.state not in {"draft", "paused"}:
            raise InvalidTransition("计划不能启动")
        plan.state = "running"
        self.audit.append("start_plan", "plan", plan_id, request_id, {"ready": self.ready(plan_id)})
        return plan

    def complete_step(self, plan_id, step, request_id):
        plan = self.plans[plan_id]
        if step not in plan.dependencies or step in plan.completed or step not in self.ready(plan_id):
            raise InvalidTransition("步骤当前不能完成")
        plan.completed.add(step)
        if len(plan.completed) == len(plan.dependencies):
            plan.state = "completed"
        self.audit.append("complete_step", "plan", plan_id, request_id, {"step": step})
        return self.ready(plan_id)

    def pause(self, plan_id, request_id):
        plan = self.plans[plan_id]
        if plan.state != "running":
            raise InvalidTransition("只有执行中的计划可暂停")
        plan.state = "paused"
        self.audit.append("pause_plan", "plan", plan_id, request_id, {})
        return plan
