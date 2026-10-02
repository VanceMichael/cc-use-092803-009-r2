import os
import tempfile
import threading
import unittest
from datetime import datetime, timezone

from emergency_service.auth import Principal
from emergency_service.errors import Conflict, InvalidTransition, PermissionDenied
from emergency_service.models import Assignment, Event, SupplyLot, Team
from emergency_service.service import EmergencyPlatform


def now():
    return datetime.now(timezone.utc)


class NewPlatform:
    def __init__(self):
        self.p = EmergencyPlatform()
        self.admin = Principal(
            "a",
            frozenset({"commander", "dispatcher", "warehouse", "auditor"}),
            frozenset({"global"}),
        )
        self.cq_dispatcher = Principal("cq", frozenset({"dispatcher"}), frozenset({"重庆"}))
        self.sc_dispatcher = Principal("sc", frozenset({"dispatcher"}), frozenset({"四川"}))

    def event(self, eid="e1", region="重庆", source="sensor-a", at=None):
        return Event(eid, region, "rain", 3, at or now(), source)

    def seed_team(self, tid="t1", region="重庆", capacity=3):
        self.p.teams.register(Team(tid, region, {"rescue"}, capacity), "team-" + tid)


class DuplicateEventTests(unittest.TestCase):
    def setUp(self):
        self.helper = NewPlatform()
        self.p = self.helper.p
        self.admin = self.helper.admin

    def test_same_event_different_request_ids_keeps_single_chain(self):
        # 上游在暴雨中把同一外部事件号重复送达（不同 request_id）。
        at = now()
        first = self.p.create_event(self.admin, self.helper.event(at=at), "req-1")
        dup = self.p.create_event(self.admin, self.helper.event(at=at), "req-2")
        self.assertEqual(first, dup)
        self.assertEqual(len(self.p.events.events), 1)
        creates = [e for e in self.p.audit.entries if e.action == "create_event"]
        self.assertEqual(len(creates), 1)

    def test_concurrent_duplicate_assignments_dispatch_once(self):
        self.helper.seed_team(capacity=3)
        self.p.create_event(self.admin, self.helper.event(), "evt-1")
        errors, results = [], []
        barrier = threading.Barrier(8)

        def assign(request_id):
            barrier.wait()
            try:
                results.append(
                    self.p.assign(
                        self.admin,
                        Assignment("a1", "e1", "t1", region="重庆", quantity=2),
                        request_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        # 同一请求（同 request_id）并发重试：只有一路真正生效。
        threads = [threading.Thread(target=assign, args=("assign-same",)) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # 其它路要么拿到处理中冲突，要么回灌同一结果；无论哪种交错，副作用只有一次。
        self.assertTrue(all(isinstance(e, Conflict) for e in errors))
        self.assertTrue(all(r["assignment_id"] == "a1" for r in results))
        self.assertEqual(len(errors) + len(results), 8)
        self.assertEqual(self.p.teams.get("t1").capacity, 1)
        self.assertEqual(len(self.p.assignments.items), 1)
        self.assertEqual(
            len([e for e in self.p.audit.entries if e.action == "plan_assignment"]), 1
        )

        # 不同 request_id 但同派单编号的重复送达：收敛到同一条派单，不再扣减能力。
        again = self.p.assign(
            self.admin,
            Assignment("a1", "e1", "t1", region="重庆", quantity=2),
            "assign-redelivered",
        )
        self.assertEqual(again["assignment_id"], "a1")
        self.assertEqual(self.p.teams.get("t1").capacity, 1)
        self.assertEqual(len(self.p.assignments.items), 1)

    def test_concurrent_supply_reservation_locks_once(self):
        self.helper.seed_team()
        self.p.create_event(self.admin, self.helper.event(), "evt-1")
        self.p.supplies.add(SupplyLot("l1", "沙袋", 100), "lot-1")
        errors, results = [], []
        barrier = threading.Barrier(6)

        def reserve():
            barrier.wait()
            try:
                results.append(
                    self.p.reserve_supply(
                        self.admin, "l1", 30, "res-same", event_id="e1", region="重庆"
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=reserve) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(all(isinstance(e, Conflict) for e in errors))
        self.assertTrue(all(r["reserved"] == 30 for r in results))
        self.assertEqual(len(errors) + len(results), 6)
        self.assertEqual(self.p.supplies.get("l1").reserved, 30)
        # 事后重试：直接回灌原结果，不再锁定。
        again = self.p.reserve_supply(
            self.admin, "l1", 30, "res-same", event_id="e1", region="重庆"
        )
        self.assertEqual(again["reserved"], 30)
        self.assertEqual(self.p.supplies.get("l1").reserved, 30)

    def test_retry_same_request_returns_cached_result(self):
        event = self.helper.event()
        first = self.p.create_event(self.admin, event, "req-9")
        again = self.p.create_event(self.admin, event, "req-9")
        self.assertEqual(first, again)
        self.assertEqual(len(self.p.events.events), 1)

    def test_same_id_different_regions_are_separate_disasters(self):
        self.helper.seed_team("t1", "重庆", 3)
        self.helper.seed_team("t2", "四川", 3)
        at = now()
        r1 = self.p.create_event(self.admin, self.helper.event("x9", "重庆", at=at), "cq-1")
        r2 = self.p.create_event(self.admin, self.helper.event("x9", "四川", at=at), "sc-1")
        self.assertEqual(r1["event_id"], r2["event_id"])
        self.assertNotEqual(r1["region"], r2["region"])
        self.assertEqual(len(self.p.events.events), 2)
        # 不带地区查询同号事件必须报歧义，不能静默合并。
        with self.assertRaises(Conflict):
            self.p.events.get("x9")
        # 两个地区各自派单互不干扰。
        self.p.assign(
            self.helper.cq_dispatcher,
            Assignment("a-cq", "x9", "t1", region="重庆", quantity=1),
            "acq",
        )
        self.p.assign(
            self.helper.sc_dispatcher,
            Assignment("a-sc", "x9", "t2", region="四川", quantity=2),
            "asc",
        )
        self.assertEqual(self.p.teams.get("t1").capacity, 2)
        self.assertEqual(self.p.teams.get("t2").capacity, 1)

    def test_cross_region_dispatcher_cannot_assign_other_region(self):
        self.helper.seed_team("t1", "重庆", 3)
        self.p.create_event(self.admin, self.helper.event("x9", "重庆"), "cq-1")
        with self.assertRaises(PermissionDenied):
            self.p.assign(
                self.helper.sc_dispatcher,
                Assignment("a-x", "x9", "t1", region="重庆", quantity=1),
                "a-x",
            )

    def test_same_id_same_region_conflicting_source_rejected(self):
        self.p.create_event(self.admin, self.helper.event(source="sensor-a"), "r1")
        with self.assertRaises(Conflict):
            self.p.create_event(self.admin, self.helper.event(source="sensor-b"), "r2")


class LifecycleSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.helper = NewPlatform()
        self.p = self.helper.p
        self.admin = self.helper.admin
        self.helper.seed_team(capacity=3)
        self.p.create_event(self.admin, self.helper.event(), "evt")
        self.p.assign(
            self.admin,
            Assignment("a1", "e1", "t1", region="重庆", quantity=2),
            "asg",
        )

    def test_escalate_close_and_audit_keep_semantics(self):
        esc = self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        self.assertEqual(esc["status"], "escalated")
        self.assertEqual(esc["version"], 2)
        # 新请求不能重复升级。
        with self.assertRaises(InvalidTransition):
            self.p.escalate(self.admin, "e1", "esc-2", region="重庆")
        # 同一升级请求重放：原样返回，不推进版本。
        again = self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        self.assertEqual(again["version"], 2)
        closed = self.p.close(self.admin, "e1", "close-1", region="重庆")
        self.assertEqual(closed["status"], "closed")
        with self.assertRaises(InvalidTransition):
            self.p.close(self.admin, "e1", "close-2", region="重庆")
        entries = self.p.audit_for(self.admin, "event", "e1")
        actions = [e.action for e in entries]
        self.assertEqual(actions, ["create_event", "change_event", "change_event"])

    def test_cancel_restores_team_capacity(self):
        self.p.acknowledge(self.admin, "a1", "ack-1")
        self.assertEqual(self.p.teams.get("t1").capacity, 1)
        result = self.p.cancel_assignment(self.admin, "a1", "cancel-1")
        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(self.p.teams.get("t1").capacity, 3)
        with self.assertRaises(InvalidTransition):
            self.p.cancel_assignment(self.admin, "a1", "cancel-2")

    def test_cancel_replay_is_idempotent(self):
        self.p.acknowledge(self.admin, "a1", "ack-1")
        self.p.cancel_assignment(self.admin, "a1", "cancel-1")
        # 同 request_id 重放：能力不重复恢复。
        self.p.cancel_assignment(self.admin, "a1", "cancel-1")
        self.assertEqual(self.p.teams.get("t1").capacity, 3)

    def test_chain_view_shows_real_dispatch_and_supplies(self):
        self.p.acknowledge(self.admin, "a1", "ack-1")
        self.p.supplies.add(SupplyLot("l1", "沙袋", 100), "lot")
        self.p.reserve_supply(self.admin, "l1", 20, "rsv", event_id="e1", region="重庆")
        self.p.reserve_supply(self.admin, "l1", 5, "rsv2", event_id="e1", region="重庆")
        self.p.release_supply(self.admin, "l1", 5, "rel", event_id="e1", region="重庆")
        chain = self.p.event_chain(self.admin, "e1", region="重庆")
        self.assertEqual(len(chain["assignments"]), 1)
        self.assertEqual(chain["assignments"][0]["state"], "acknowledged")
        self.assertEqual(chain["supplies"][0]["lot_id"], "l1")
        self.assertEqual(chain["supplies"][0]["net_locked"], 20)
        self.assertEqual(len(chain["supplies"][0]["movements"]), 3)

    def test_audit_query_permission_unchanged(self):
        auditor = Principal("aud", frozenset({"auditor"}), frozenset({"global"}))
        entries = self.p.audit_for(auditor, "event", "e1")
        self.assertTrue(entries)
        dispatcher = Principal("d", frozenset({"dispatcher"}), frozenset({"global"}))
        with self.assertRaises(PermissionDenied):
            self.p.audit_for(dispatcher, "event", "e1")


class RestartReplayTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(self.path)

    def tearDown(self):
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(self.path + suffix)
            except FileNotFoundError:
                pass

    def _open(self):
        return EmergencyPlatform(self.path)

    def test_state_restarts_without_duplicating_chain(self):
        p = self._open()
        admin = Principal(
            "a", frozenset({"commander", "dispatcher", "warehouse"}), frozenset({"global"})
        )
        p.teams.register(Team("t1", "重庆", {"rescue"}, 3), "team")
        p.create_event(admin, Event("e1", "重庆", "rain", 3, now(), "sensor-a"), "evt")
        p.assign(admin, Assignment("a1", "e1", "t1", region="重庆", quantity=2), "asg")
        p.supplies.add(SupplyLot("l1", "沙袋", 100), "lot")
        p.reserve_supply(admin, "l1", 40, "rsv", event_id="e1", region="重庆")
        p.escalate(admin, "e1", "esc", region="重庆")
        p.store.close()

        # 重启：快照与审计链还原，无重复派单/锁定。
        p2 = self._open()
        self.assertEqual(len(p2.events.events), 1)
        self.assertEqual(len(p2.assignments.items), 1)
        self.assertEqual(p2.teams.get("t1").capacity, 1)
        self.assertEqual(p2.supplies.get("l1").reserved, 40)
        self.assertEqual(p2.events.get("e1", "重庆").status, "escalated")
        self.assertEqual(p2.events.get("e1", "重庆").version, 2)
        self.assertEqual(p2.journal.drain(), [])
        self.assertEqual(
            len([e for e in p2.audit.entries if e.action == "reserve_supply"]), 1
        )
        p2.store.close()

    def test_pending_intent_replayed_once_after_crash(self):
        p = self._open()
        admin = Principal(
            "a", frozenset({"commander", "dispatcher", "warehouse"}), frozenset({"global"})
        )
        p.teams.register(Team("t1", "重庆", {"rescue"}, 3), "team")
        p.create_event(admin, Event("e1", "重庆", "rain", 3, now(), "sensor-a"), "evt")
        p.supplies.add(SupplyLot("l1", "沙袋", 100), "lot")
        # 模拟崩溃：派单意图已写 pending，队伍扣减副作用已落库，
        # 但请求未完成（requests 仍为 processing）。
        p.journal.record_pending(
            "asg-crash",
            "assign",
            {
                "assignment_id": "a1",
                "event_id": "e1",
                "region": "重庆",
                "team_id": "t1",
                "quantity": 2,
            },
        )
        p.assignments.plan(
            Assignment("a1", "e1", "t1", region="重庆", quantity=2), "asg-crash"
        )
        self.assertEqual(p.teams.get("t1").capacity, 1)
        p.store.close()

        p2 = self._open()
        # 重放未决意图；副作用已登记，不能再次扣减。
        self.assertEqual(p2.teams.get("t1").capacity, 1)
        self.assertEqual(len(p2.assignments.items), 1)
        self.assertEqual(
            len([e for e in p2.audit.entries if e.action == "consume_team"]), 1
        )
        # pending 已清空，再次 recover 无操作。
        self.assertEqual(p2.recover(), [])
        p2.store.close()


if __name__ == "__main__":
    unittest.main()
