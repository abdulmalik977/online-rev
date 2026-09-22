"""Seven deterministic rules. Run every 30 minutes; never calls an LLM."""
import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

from common import (ROOT, OPEN, add_approval, agent_config, approvals, atomic_write,
                    database, local_day, locked, now, parse_time, quota, read_front,
                    seed, stamp, sync_tasks, tasks, validate, write_front)


def rule_1_review_loop(task):
    return task["review_round"] > 2


def rule_2_stale(task, at):
    return task["status"] in {"doing", "review"} and at - parse_time(task["updated"]) >= timedelta(hours=24)


def rule_3_attempts(task):
    return task["attempts"] > 3


def rule_4_missing_metric(task):
    return not task.get("success_metric", "").strip()


def rule_5_capacity(records, agent):
    """At five open tasks, the proposed sixth is disallowed."""
    return sum(t["owner"] == agent and t["status"] in OPEN for t in records) >= 5


def rule_6_low_compute(used, budget):
    return used * 5 > budget * 4


def rule_7_old_approval(approval, at):
    return at - parse_time(approval["created"]) > timedelta(hours=48)


def counter_state(root, task):
    path = root / f"reviews/counters-{task['id']}.md"
    entries = [json.loads(line[11:]) for line in path.read_text(encoding="utf-8").splitlines()
               if line.startswith("- COUNTERS ")] if path.exists() else []
    return entries[-1]["counters"] if entries else {"attempts": 0, "review_round": 0}


def counter_event(root, task, action, note):
    path = root / f"reviews/counters-{task['id']}.md"
    previous = path.read_text(encoding="utf-8") if path.exists() else "# Script-owned counter history\n"
    event = dict(at=stamp(), action=action, note=note,
                 counters={key: task[key] for key in ("attempts", "review_round")})
    atomic_write(path, previous + "- COUNTERS " + json.dumps(event, ensure_ascii=False) + "\n")


def record_counter(ident, action, note, result=None, root=ROOT):
    if not note or not note.strip() or (action == "review" and result not in {"pass", "changes", "reject"}):
        raise ValueError("A note and valid review result are required")
    with locked(root), database(root) as conn:
        matches = [record for record in tasks(root) if record[1]["id"] == ident]
        if not matches:
            raise ValueError("Unknown task")
        path, task, body = matches[0]
        if counter_state(root, task) != {k: task[k] for k in ("attempts", "review_round")}:
            raise ValueError("Counter protocol violation; run watchdog and inspect history")
        if task["status"] in {"blocked", "done", "killed"} or (action == "review" and task["status"] != "review"):
            raise ValueError("Task is not eligible for this action")
        if action == "review" and result == "changes" and task["review_round"] >= 2:
            raise ValueError("Two review rounds exhausted; escalate to owner")
        task["attempts" if action == "attempt" else "review_round"] += 1
        task["updated"] = stamp()
        if action == "review":
            task["status"] = {"pass": "done", "changes": "doing", "reject": "killed"}[result]
            ids = [p.stem for p in (root / "reviews").glob("REV-*.md")]
            ids += [row[0] for row in conn.execute("SELECT id FROM reviews")]
            number = max([int(i[4:]) for i in ids if i.startswith("REV-") and i[4:].isdigit()], default=0) + 1
            review_id = f"REV-{number:03d}"
            review_path = root / f"reviews/{review_id}.md"
            conn.execute("INSERT INTO reviews VALUES(?,?,?,?)", (review_id, ident, result, f"reviews/{review_id}.md"))
            write_front(review_path, dict(id=review_id, task_id=ident, result=result,
                        review_round=task["review_round"], created=task["updated"]), note)
        counter_event(root, task, action, note)
        write_front(path, task, body)
        sync_tasks(conn, tasks(root))
    return task


def scan(root=ROOT, at=None):
    at = at or now()
    findings = {"stale": [], "loops": [], "killed": [], "missing_metrics": [],
                "capacity": [], "low_compute": [], "old_approvals": [], "protocol_violations": []}
    with locked(root), database(root) as conn:
        records = tasks(root)  # Validate every task before any mutation.
        reviews = [(p, read_front(p)[0]) for p in sorted((root / "reviews").glob("REV-*.md"))]
        if any(p.stem != review["id"] for p, review in reviews):
            raise ValueError("Review filename disagrees with ID")
        approvals(root)
        approvals(root, True)
        for agent in ("claude", "codex"):
            agent_config(root, agent)
        for path, task, body in records:
            reasons = []
            if counter_state(root, task) != {k: task[k] for k in ("attempts", "review_round")}:
                findings["protocol_violations"].append(task["id"])
                reasons.append("counter protocol violation; inspect script-owned history")
                add_approval(root, "COUNTERS-" + task["id"], reasons[-1], at)
            if rule_2_stale(task, at):
                findings["stale"].append(task["id"])
            if rule_1_review_loop(task):
                findings["loops"].append(task["id"])
                reasons.append("review_round > 2; owner decision required")
                add_approval(root, "LOOP-" + task["id"], f"{task['id']}: review_round > 2; resolve loop", at)
            if rule_4_missing_metric(task):
                findings["missing_metrics"].append(task["id"])
                reasons.append("missing success_metric; rejected")
            # A killed task remains killed even when other rules also match.
            desired = task["status"]
            if reasons and desired != "killed":
                desired = "blocked"
            if rule_3_attempts(task):
                findings["killed"].append(task["id"])
                reasons.append("attempts > 3; killed")
                desired = "killed"
            if desired != task["status"]:
                task["status"], task["updated"] = desired, stamp(at)
                body += f"\n\nWatchdog {stamp(at)}: " + "; ".join(reasons)
                write_front(path, task, body)
                atomic_write(root / f"logs/runs/watchdog-{task['id']}-{at.strftime('%Y%m%dT%H%M%S%fZ')}.md",
                             f"# Watchdog transition\n{task['id']} → {desired}\n" + "; ".join(reasons) + "\n")
        sync_tasks(conn, records)
        seed(conn, at)
        conn.execute("DELETE FROM reviews")
        conn.executemany("INSERT INTO reviews VALUES(?,?,?,?)", [
            (r["id"], r["task_id"], r.get("result", r.get("status", "open")), f"reviews/{p.name}") for p, r in reviews])
        for agent in ("claude", "codex"):
            if rule_5_capacity([t for _, t, _ in records], agent):
                findings["capacity"].append(agent)
            used, budget = quota(conn, root, agent, at)
            low = rule_6_low_compute(used, budget)
            if low:
                findings["low_compute"].append(agent)
            atomic_write(root / f"agents/{agent}-LOW-COMPUTE.md",
                         f"# Quota flag — {agent}\nDay: {local_day(at)}\n"
                         f"LOW-COMPUTE: {'true' if low else 'false'}\n"
                         f"RESERVE-REACHED: {'true' if used * 5 >= budget * 4 else 'false'}\n"
                         f"Usage: {used}/{budget} credits ({used / budget:.0%})\n")
        findings["old_approvals"] = [a["id"] for a in approvals(root) if rule_7_old_approval(a, at)]
        atomic_write(root / "logs/watchdog.json", json.dumps({"checked": stamp(at), **findings}, indent=2) + "\n")
    return findings


def create_task(source, root=ROOT):
    task, body = read_front(source)
    validate(task)
    if task["status"] != "todo" or task["attempts"] or task["review_round"]:
        raise ValueError("New tasks must start in todo with zero counters")
    if rule_4_missing_metric(task) or rule_1_review_loop(task) or rule_3_attempts(task):
        raise ValueError("New task rejected: success metric or attempt/review limits")
    with locked(root), database(root) as conn:
        records = tasks(root)
        target = root / f"tasks/{task['id']}.md"
        if target.exists():
            raise ValueError("Task already exists")
        if rule_5_capacity([t for _, t, _ in records], task["owner"]):
            raise ValueError("Five open tasks already exist; creation blocked")
        counter_event(root, task, "create", "Admitted with zero counters")
        write_front(target, task, body)
        sync_tasks(conn, tasks(root))
    return target


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.at = parse_time("2026-09-22T12:00:00+00:00")
        for agent in ("claude", "codex"):
            write_front(self.root / f"agents/{agent}.md", {"quota_budget": 100, "run_budget": 20}, "test")
        self.task = dict(id="TASK-TEST", title="Test", owner="codex", status="doing", goal="Test",
                         evidence="Fixture", definition_of_done="Assert", success_metric="One passing assertion",
                         attempts=3, review_round=2, quota_budget=20,
                         created=stamp(self.at - timedelta(days=3)), updated=stamp(self.at))

    def save(self, **changes):
        self.task.update(changes)
        path = self.root / f"tasks/{self.task['id']}.md"
        counter_event(self.root, self.task, "fixture", "Explicit test baseline")
        write_front(path, self.task, "Fixture")
        return path

    def test_1_review_loop_persists_and_deduplicates(self):
        self.assertFalse(rule_1_review_loop(self.task))
        path = self.save(review_round=3)
        scan(self.root, self.at)
        scan(self.root, self.at + timedelta(minutes=30))
        self.assertEqual(read_front(path)[0]["status"], "blocked")
        self.assertEqual(len(approvals(self.root)), 1)
        with database(self.root) as conn:
            self.assertEqual(conn.execute("SELECT status FROM tasks").fetchone()[0], "blocked")

    def test_2_staleness_boundary(self):
        self.task["updated"] = stamp(self.at - timedelta(hours=24))
        self.assertTrue(rule_2_stale(self.task, self.at))
        self.assertFalse(rule_2_stale(self.task, self.at - timedelta(seconds=1)))
        self.task["status"] = "blocked"
        self.assertFalse(rule_2_stale(self.task, self.at))

    def test_3_attempts_kill_precedence_and_log(self):
        self.assertFalse(rule_3_attempts(self.task))
        path = self.save(attempts=4, review_round=3, success_metric="")
        scan(self.root, self.at)
        scan(self.root, self.at)
        self.assertEqual(read_front(path)[0]["status"], "killed")
        self.assertIn("attempts > 3", path.read_text(encoding="utf-8"))
        self.assertEqual(len(list((self.root / "logs/runs").glob("*.md"))), 1)

    def test_4_missing_metric_rejects(self):
        self.assertFalse(rule_4_missing_metric(self.task))
        self.task.pop("success_metric")
        path = self.save()
        scan(self.root, self.at)
        self.assertEqual(read_front(path)[0]["status"], "blocked")

    def test_5_capacity_enforced_on_creation(self):
        source = self.root / "candidate.md"
        for number in range(5):
            self.task.update(id=f"TASK-{number}", status="todo", attempts=0, review_round=0)
            write_front(source, self.task, "Candidate")
            create_task(source, self.root)
        self.task["id"] = "TASK-SIX"
        write_front(source, self.task, "Candidate")
        with self.assertRaisesRegex(ValueError, "Five open"):
            create_task(source, self.root)
        self.assertFalse((self.root / "tasks/TASK-SIX.md").exists())
        self.assertFalse(rule_5_capacity([self.task] * 4, "codex"))
        self.assertFalse(rule_5_capacity([self.task] * 6, "claude"))

    def test_6_quota_flag_threshold_and_day_reset(self):
        self.assertFalse(rule_6_low_compute(80, 100))
        self.assertTrue(rule_6_low_compute(81, 100))
        with database(self.root) as conn:
            conn.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)",
                         ("fixture", "codex", stamp(self.at), stamp(self.at), local_day(self.at), 81, "failed", "test"))
        self.assertIn("codex", scan(self.root, self.at)["low_compute"])
        self.assertNotIn("codex", scan(self.root, self.at + timedelta(days=1))["low_compute"])
        self.assertIn("LOW-COMPUTE: false", (self.root / "agents/codex-LOW-COMPUTE.md").read_text())

    def test_7_approval_age_not_file_mtime(self):
        approval = {"created": stamp(self.at - timedelta(hours=48))}
        self.assertFalse(rule_7_old_approval(approval, self.at))
        self.assertTrue(rule_7_old_approval(approval, self.at + timedelta(seconds=1)))
        add_approval(self.root, "OLD", "Old approval", self.at - timedelta(hours=49))
        add_approval(self.root, "NEW", "New approval", self.at)
        self.assertEqual(scan(self.root, self.at)["old_approvals"], ["OLD"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--test", action="store_true")
    group.add_argument("--create", type=Path, help="Admit a task file from outside tasks/")
    group.add_argument("--review", metavar="TASK-ID")
    group.add_argument("--attempt", metavar="TASK-ID")
    parser.add_argument("--result", choices=("pass", "changes", "reject"))
    parser.add_argument("--note")
    args = parser.parse_args()
    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RuleTests))
        return 0 if result.wasSuccessful() else 1
    try:
        if args.review or args.attempt:
            print(json.dumps(record_counter(args.review or args.attempt, "review" if args.review else "attempt", args.note, args.result)))
        else:
            print(create_task(args.create) if args.create else json.dumps(scan(), indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"WATCHDOG ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
