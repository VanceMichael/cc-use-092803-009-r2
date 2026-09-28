from .assignments import AssignmentBoard
from .audit import AuditLog
from .auth import Principal, require
from .events import EventRegister
from .models import Assignment, Event, SupplyLot, Team
from .plans import PlanBook
from .recovery import RecoveryJournal
from .store import StateStore
from .supplies import SupplyLedger
from .teams import TeamRegistry
from .geo import RiskMap

class EmergencyPlatform:
    def __init__(self, db_path=":memory:"):
        self.audit = AuditLog()
        self.store = StateStore(db_path)
        self.journal = RecoveryJournal(self.audit)
        self.events = EventRegister(self.audit)
        self.teams = TeamRegistry(self.audit)
        self.supplies = SupplyLedger(self.audit)
        self.assignments = AssignmentBoard(self.events, self.teams, self.audit)
        self.risks = RiskMap(self.audit)
        self.plans = PlanBook(self.audit)

    def create_event(self, principal, event, request_id):
        require(principal, "plan", event.region)
        cached = self.store.get_request(request_id)
        if cached is not None:
            return cached
        self.journal.record_pending(request_id, "create_event", {"event_id": event.event_id})
        result = self.events.create(event, request_id)
        payload = {"event_id": result.event_id, "status": result.status, "version": result.version}
        return self.store.save_request(request_id, payload)

    def assign(self, principal, assignment, request_id):
        event = self.events.get(assignment.event_id)
        require(principal, "assign", event.region)
        cached = self.store.get_request(request_id)
        if cached is not None:
            return cached
        result = self.assignments.plan(assignment, request_id)
        payload = {"assignment_id": result.assignment_id, "state": result.state}
        return self.store.save_request(request_id, payload)

    def acknowledge(self, principal, assignment_id, request_id):
        item = self.assignments.get(assignment_id)
        event = self.events.get(item.event_id)
        require(principal, "assign", event.region)
        result = self.assignments.acknowledge(assignment_id, request_id)
        return {"assignment_id": result.assignment_id, "state": result.state}

    def close(self, principal, event_id, request_id):
        event = self.events.get(event_id)
        require(principal, "close", event.region)
        result = self.events.change_status(event_id, "closed", request_id)
        return {"event_id": result.event_id, "status": result.status, "version": result.version}

    def recover(self):
        return self.journal.drain(lambda action, payload, request_id: None)

    def audit_for(self, principal, entity, entity_id):
        require(principal, "read_audit", "global")
        return self.audit.for_entity(entity, entity_id)
