import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from emergency_service.auth import Principal
from emergency_service.errors import (
    CapacityExceeded, Conflict, InvalidTransition, PermissionDenied,
)
from emergency_service.models import Assignment, Event, SupplyLot, Team
from emergency_service.service import EmergencyPlatform


def event(event_id="e1", region="重庆", source="sensor-a", at=None):
    return Event(event_id, region, "rain", 3, at or datetime.now(timezone.utc), source)


class DuplicateEventTest(unittest.TestCase):
    def setUp(self):
        self.p = EmergencyPlatform()
        self.admin = Principal("a", frozenset({"commander", "dispatcher", "warehouse", "auditor"}), frozenset({"global"}))
        self.when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)

    def test_concurrent_same_disaster_keeps_single_chain(self):
        # 同一外部事件号的并发重复提交，只保留一条事件、一条审计
        e = event("e1", "重庆", "sensor-a", self.when)

        def submit(i):
            return self.p.create_event(self.admin, e, f"req-{i}")

        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(submit, range(16)))

        self.assertEqual(len(self.p.events.events), 1)
        self.assertTrue(all(r["event_id"] == "e1" and r["region"] == "重庆" for r in results))
        audit = self.p.audit_for(self.admin, "event", "e1")
        self.assertEqual(len(audit), 1)

    def test_same_event_id_different_regions_are_not_merged(self):
        self.p.create_event(self.admin, event("e1", "重庆", "sensor-a", self.when), "r-cq")
        self.p.create_event(self.admin, event("e1", "成都", "sensor-a", self.when), "r-cd")
        self.assertEqual(len(self.p.events.events), 2)
        self.assertEqual(self.p.events.get("e1", "重庆").region, "重庆")
        self.assertEqual(self.p.events.get("e1", "成都").region, "成都")
        with self.assertRaises(Conflict):
            self.p.events.get("e1")  # 不带地区无法消歧

    def test_same_id_and_region_but_different_source_conflicts(self):
        self.p.create_event(self.admin, event("e1", "重庆", "sensor-a", self.when), "r-1")
        with self.assertRaises(Conflict):
            self.p.create_event(self.admin, event("e1", "重庆", "sensor-b", self.when), "r-2")

    def test_idempotent_retry_returns_same_result(self):
        e = event("e1", "重庆", "sensor-a", self.when)
        first = self.p.create_event(self.admin, e, "req-1")
        again = self.p.create_event(self.admin, e, "req-1")
        self.assertEqual(first, again)


class AssignmentAndSupplyTest(unittest.TestCase):
    def setUp(self):
        self.p = EmergencyPlatform()
        self.admin = Principal("a", frozenset({"commander", "dispatcher", "warehouse", "auditor"}), frozenset({"global"}))
        self.when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
        self.p.create_event(self.admin, event("e1", "重庆", "sensor-a", self.when), "ev-1")

    def test_concurrent_duplicate_assignment_dispatches_once(self):
        self.p.teams.register(Team("t1", "重庆", {"rescue"}, 5), "team-1")
        a = Assignment("a1", "e1", "t1", quantity=2)

        def submit(i):
            return self.p.assign(self.admin, a, f"assign-{i}")

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(submit, range(12)))

        self.assertEqual(len(self.p.assignments.items), 1)
        # 能力只扣减一次
        self.assertEqual(self.p.teams.get("t1").capacity, 3)
        self.assertTrue(all(r["assignment_id"] == "a1" for r in results))
        self.assertEqual(results[0]["state"], "planned")
        self.assertEqual(results[0]["team_capacity"], 3)

    def test_concurrent_reserve_locks_once(self):
        self.p.add_supply(self.admin, SupplyLot("l1", "编织袋", 100), "lot-1")

        def submit(i):
            # 不同请求但同一处置链（同一灾害的物资锁定）
            return self.p.reserve(self.admin, "l1", 30, f"res-{i}", reservation_id="chain-e1")

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(submit, range(12)))

        lot = self.p.supplies.get("l1")
        self.assertEqual(lot.reserved, 30)
        self.assertEqual(lot.quantity - lot.reserved, 70)
        self.assertTrue(all(r["reserved"] == 30 and r["amount"] == 30 for r in results))

    def test_reserve_retry_same_request_id_is_idempotent(self):
        self.p.add_supply(self.admin, SupplyLot("l1", "编织袋", 100), "lot-1")
        first = self.p.reserve(self.admin, "l1", 40, "res-1")
        again = self.p.reserve(self.admin, "l1", 40, "res-1")
        self.assertEqual(first, again)
        self.assertEqual(self.p.supplies.get("l1").reserved, 40)

    def test_release_replay_does_not_over_release(self):
        self.p.add_supply(self.admin, SupplyLot("l1", "编织袋", 100), "lot-1")
        self.p.reserve(self.admin, "l1", 60, "res-1")
        self.p.release(self.admin, "l1", 20, "rel-1")
        self.p.release(self.admin, "l1", 20, "rel-1")  # 重试
        self.assertEqual(self.p.supplies.get("l1").reserved, 40)

    def test_cancel_restores_capacity_once(self):
        self.p.teams.register(Team("t1", "重庆", {"rescue"}, 3), "team-1")
        self.p.assign(self.admin, Assignment("a1", "e1", "t1", quantity=2), "assign-1")
        self.assertEqual(self.p.teams.get("t1").capacity, 1)
        first = self.p.cancel_assignment(self.admin, "a1", "cancel-1")
        again = self.p.cancel_assignment(self.admin, "a1", "cancel-1")
        self.assertEqual(first, again)
        self.assertEqual(self.p.teams.get("t1").capacity, 3)
        self.assertEqual(self.p.assignments.get("a1").state, "cancelled")

    def test_same_team_dispatch_twice_to_same_disaster_conflicts(self):
        self.p.teams.register(Team("t1", "重庆", {"rescue"}, 5), "team-1")
        self.p.assign(self.admin, Assignment("a1", "e1", "t1", quantity=1), "assign-1")
        # 换一个派单号再次把同一队伍派往同一灾害 -> 拒绝，能力不重复扣减
        with self.assertRaises(Conflict):
            self.p.assign(self.admin, Assignment("a2", "e1", "t1", quantity=1), "assign-2")
        self.assertEqual(self.p.teams.get("t1").capacity, 4)
        # 另一支队伍驰援同一灾害仍然允许
        self.p.teams.register(Team("t2", "重庆", {"rescue"}, 4), "team-2")
        second = self.p.assign(self.admin, Assignment("a3", "e1", "t2", quantity=1), "assign-3")
        self.assertEqual(second["assignment_id"], "a3")

    def test_same_event_id_assignment_scoped_by_team_region(self):
        # 成都也有同号事件和队伍；两单各自挂在本区处置链上，不串单
        self.p.create_event(self.admin, event("e1", "成都", "sensor-a", self.when), "ev-2")
        self.p.teams.register(Team("t-cq", "重庆", {"rescue"}, 3), "team-cq")
        self.p.teams.register(Team("t-cd", "成都", {"rescue"}, 3), "team-cd")
        cq = self.p.assign(self.admin, Assignment("a-cq", "e1", "t-cq", quantity=1), "a-cq")
        cd = self.p.assign(self.admin, Assignment("a-cd", "e1", "t-cd", quantity=1), "a-cd")
        self.assertEqual(cq["region"], "重庆")
        self.assertEqual(cd["region"], "成都")
        self.assertEqual(self.p.assignments.get("a-cq").event_id, "e1")
        self.assertEqual(self.p.assignments.get("a-cd").event_id, "e1")


class EscalationAndPermissionsTest(unittest.TestCase):
    def setUp(self):
        self.p = EmergencyPlatform()
        self.admin = Principal("a", frozenset({"commander", "dispatcher", "warehouse", "auditor"}), frozenset({"global"}))
        self.when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
        self.p.create_event(self.admin, event("e1", "重庆", "sensor-a", self.when), "ev-1")

    def test_escalate_then_close_semantics_kept(self):
        esc = self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        self.assertEqual(esc["status"], "escalated")
        self.assertEqual(esc["version"], 2)
        closed = self.p.close(self.admin, "e1", "close-1", region="重庆")
        self.assertEqual(closed["status"], "closed")
        self.assertEqual(closed["version"], 3)
        with self.assertRaises(InvalidTransition):
            self.p.escalate(self.admin, "e1", "esc-2", region="重庆")

    def test_escalate_retry_is_idempotent(self):
        first = self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        again = self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        self.assertEqual(first, again)
        self.assertEqual(self.p.events.get("e1", "重庆").version, 2)

    def test_permission_checks_still_enforced(self):
        dispatcher = Principal("d", frozenset({"dispatcher"}), frozenset({"global"}))
        with self.assertRaises(PermissionDenied):
            self.p.escalate(dispatcher, "e1", "esc-x", region="重庆")
        outsider = Principal("o", frozenset({"commander"}), frozenset({"成都"}))
        with self.assertRaises(PermissionDenied):
            self.p.escalate(outsider, "e1", "esc-y", region="重庆")

    def test_audit_query_shows_single_chain(self):
        self.p.escalate(self.admin, "e1", "esc-1", region="重庆")
        entries = self.p.audit_for(self.admin, "event", "e1", region="重庆")
        actions = [e.action for e in entries]
        self.assertEqual(actions, ["create_event", "change_event"])
        # 异地同号事件的审计不混进本地区处置链
        self.p.create_event(self.admin, event("e1", "成都", "sensor-a", self.when), "ev-2")
        cq_entries = self.p.audit_for(self.admin, "event", "e1", region="重庆")
        self.assertTrue(all(e.detail.get("region") == "重庆" for e in cq_entries))
        all_entries = self.p.audit_for(self.admin, "event", "e1")
        self.assertEqual({e.detail["region"] for e in all_entries}, {"重庆", "成都"})


class RestartReplayTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_restart_rebuilds_state_without_double_side_effects(self):
        p = EmergencyPlatform(self.path)
        admin = Principal("a", frozenset({"commander", "dispatcher", "warehouse", "auditor"}), frozenset({"global"}))
        when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
        p.create_event(admin, event("e1", "重庆", "sensor-a", when), "ev-1")
        p.teams.register(Team("t1", "重庆", {"rescue"}, 5), "team-1")
        p.assign(admin, Assignment("a1", "e1", "t1", quantity=2), "assign-1")
        p.add_supply(admin, SupplyLot("l1", "编织袋", 100), "lot-1")
        p.reserve(admin, "l1", 30, "res-1")
        p.escalate(admin, "e1", "esc-1", region="重庆")
        before_entries = len(p.audit.export())

        # 全新进程视角：领域内存清空，仅从 SQLite 重建
        p2 = EmergencyPlatform(self.path)
        self.assertEqual(len(p2.events.events), 1)
        self.assertEqual(p2.events.get("e1", "重庆").status, "escalated")
        self.assertEqual(p2.events.get("e1", "重庆").version, 2)
        self.assertEqual(p2.teams.get("t1").capacity, 3)
        self.assertEqual(len(p2.assignments.items), 1)
        self.assertEqual(p2.assignments.get("a1").state, "planned")
        self.assertEqual(p2.supplies.get("l1").reserved, 30)
        # 重建不产生新的审计条目
        self.assertEqual(len(p2.audit.export()), before_entries)
        # 未决日志已排空
        self.assertEqual(p2.journal.pending, [])

        # 同一 request_id 重试仍然幂等
        again = p2.reserve(admin, "l1", 30, "res-1")
        self.assertEqual(again["reserved"], 30)

    def test_pending_journal_entry_is_replayed_then_cleared(self):
        # 模拟崩溃：pending 已落盘但结果未保存，且审计中有此前的事件
        p = EmergencyPlatform(self.path)
        admin = Principal("a", frozenset({"commander", "dispatcher", "warehouse"}), frozenset({"global"}))
        when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
        p.create_event(admin, event("e1", "重庆", "sensor-a", when), "ev-1")
        p.teams.register(Team("t1", "重庆", {"rescue"}, 5), "team-1")
        # 直接写一条未决派单（相当于动作已开始、结果未落盘时崩溃）
        p.store.save_pending("assign-x", "assign",
                             {"assignment_id": "a9", "event_id": "e1", "team_id": "t1",
                              "quantity": 2, "region": "重庆"})

        p2 = EmergencyPlatform(self.path)  # 启动即重放
        self.assertEqual(p2.assignments.get("a9").state, "planned")
        self.assertEqual(p2.teams.get("t1").capacity, 3)
        self.assertEqual(p2.journal.pending, [])
        # 再重启一次也不会重复扣减
        p3 = EmergencyPlatform(self.path)
        self.assertEqual(p3.teams.get("t1").capacity, 3)
        self.assertEqual(len(p3.assignments.items), 1)

    def test_event_replay_is_idempotent(self):
        p = EmergencyPlatform(self.path)
        when = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
        events = [event("e1", "重庆", "sensor-a", when), event("e2", "成都", "sensor-b", when)]
        self.assertEqual(p.events.replay(events), 2)
        self.assertEqual(p.events.replay(events), 2)  # 再放一遍
        self.assertEqual(len(p.events.events), 2)


if __name__ == "__main__":
    unittest.main()
