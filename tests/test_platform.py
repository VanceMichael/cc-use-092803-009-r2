import unittest
from datetime import datetime, timezone
from emergency_service.auth import Principal
from emergency_service.models import Event, Team, Assignment
from emergency_service.service import EmergencyPlatform

class PlatformTest(unittest.TestCase):
    def setUp(self):
        self.p = EmergencyPlatform()
        self.admin = Principal("a", frozenset({"commander", "dispatcher", "read_audit"}), frozenset({"global"}))
        self.event = Event("e1", "重庆", "rain", 3, datetime.now(timezone.utc), "sensor-a")

    def test_event_request_is_idempotent(self):
        first = self.p.create_event(self.admin, self.event, "req-1")
        again = self.p.create_event(self.admin, self.event, "req-1")
        self.assertEqual(first, again)
        self.assertEqual(len(self.p.events.events), 1)

    def test_assignment_consumes_and_acknowledges(self):
        self.p.create_event(self.admin, self.event, "req-2")
        self.p.teams.register(Team("t1", "重庆", {"rescue"}, 3), "team-1")
        item = self.p.assign(self.admin, Assignment("a1", "e1", "t1", quantity=2), "assign-1")
        self.assertEqual(item["state"], "planned")
        self.assertEqual(self.p.acknowledge(self.admin, "a1", "ack-1")["state"], "acknowledged")

if __name__ == "__main__":
    unittest.main()
