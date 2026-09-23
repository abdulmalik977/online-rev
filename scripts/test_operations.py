"""Temporary storage, fake adapters, and mocked SMTP; no network/LLM calls."""
from datetime import timedelta
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from common import ROOT, add_approval, database, local_day, now, quota, read_front, stamp, write_front
from daily_report import SECTIONS, generate, send_report
from run_agent import reserve, run
from watchdog import scan, record_counter


class OperationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for directory in ("company", "agents", "approvals", "tasks", "reviews"):
            shutil.copytree(ROOT / directory, self.root / directory)
        # The original operations fixtures expect REV-001/002 and an open
        # TASK-004. Isolate them from later real company decisions/reviews.
        for review in (self.root / 'reviews').glob('REV-*.md'):
            assert review.resolve().is_relative_to(self.root.resolve())
            if review.stem not in {'REV-001', 'REV-002'}:
                review.unlink()
        fixture_path = self.root / 'tasks/TASK-004.md'
        fixture_task, fixture_body = read_front(fixture_path)
        fixture_task['status'] = 'doing'
        write_front(fixture_path, fixture_task, fixture_body)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        if os.name == "nt":
            os.environ["SystemRoot"] = "C:\\Windows"

    def adapter(self, code):
        path = self.root / "fake_adapter.py"
        path.write_text(code, encoding="utf-8")
        os.environ["CODEX_METERED_COMMAND"] = json.dumps([sys.executable, str(path)])

    def insert_run(self, used, status="done", agent="codex", at=None):
        at = at or now()
        with database(self.root) as conn:
            conn.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)",
                         ("existing", agent, stamp(at), stamp(at), local_day(at), used, status, "fixture"))

    def test_report_order_length_and_currency_separation(self):
        with database(self.root) as conn:
            for unit, value in (("USD", 99), ("GBP", 150)):
                conn.execute("INSERT INTO metrics VALUES(?,?,?,?)", (local_day(), "revenue", value, unit))
            conn.execute("INSERT INTO metrics VALUES(?,?,?,?)", (local_day(), "emails_sent", 5, "count"))
        content = generate(self.root).read_text(encoding="utf-8")
        self.assertEqual([line[3:] for line in content.splitlines() if line.startswith("## ")], list(SECTIONS))
        self.assertLessEqual(len(content.splitlines()), 30)
        self.assertIn("USD 99.00 MTD", content)
        self.assertIn("GBP 150.00 MTD", content)
        self.assertIn("emails sent: 5", content)
        self.assertIn("claude:", content)
        self.assertIn("codex:", content)

    def test_report_stale_task_and_48_hour_escalation(self):
        path = self.root / "tasks/TASK-001.md"
        task, body = read_front(path)
        task["status"] = "review"
        task["created"] = stamp(now() - timedelta(days=4))
        task["updated"] = stamp(now() - timedelta(days=2))
        write_front(path, task, body)
        add_approval(self.root, "OLDER", "Owner action", now() - timedelta(hours=49))
        content = generate(self.root).read_text(encoding="utf-8")
        self.assertIn("STALE 24h: TASK-001", content)
        self.assertIn("ESCALATE >48h: OLDER", content)

    def test_dry_run_reads_context_without_spending(self):
        self.assertEqual(run("codex", "execute", self.root, dry_run=True), 0)
        log = next((self.root / "logs/runs").glob("codex-*.md")).read_text(encoding="utf-8")
        for name in ("current-goal.md", "metrics.md", "agents/codex.md", "LOW-COMPUTE", "TASK-004"):
            self.assertIn(name, log)
        with database(self.root) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 0)

    def test_missing_adapter_fails_closed_and_logs(self):
        with patch("run_agent.shutil.which", return_value=None):
            self.assertEqual(run("codex", "execute", self.root), 1)
        self.assertEqual(len(list((self.root / "logs/runs").glob("codex-*.md"))), 1)
        with database(self.root) as conn:
            self.assertEqual(quota(conn, self.root, "codex", now())[0], 0)

    def test_adapter_budget_context_and_conservative_reservation(self):
        self.adapter("import json,os,sys\nprompt=sys.stdin.read()\nassert 'current-goal.md' in prompt\n"
                     "assert os.environ['COMPANY_MAX_CREDITS']=='20'\nassert 'SMTP_PASSWORD' not in os.environ\n"
                     "print(json.dumps({'usage': 7, 'summary': 'Fixture complete'}))\n")
        os.environ["SMTP_PASSWORD"] = "test-only-secret"
        self.assertEqual(run("codex", "execute", self.root), 0)
        with database(self.root) as conn:
            row = conn.execute("SELECT * FROM runs").fetchone()
            self.assertEqual((row["status"], row["quota_reserved"]), ("done", 20))

    def test_exact_reserve_boundary_then_stop(self):
        self.insert_run(60)
        with database(self.root) as conn:
            self.assertEqual(reserve(conn, self.root, "codex", "at-boundary", now()), 20)
            conn.execute("UPDATE runs SET status='done'")
        with database(self.root) as conn:
            with self.assertRaisesRegex(ValueError, "reserve"):
                reserve(conn, self.root, "codex", "too-much", now())

    def test_run_crossing_reserve_rejected(self):
        self.insert_run(61)
        with database(self.root) as conn:
            with self.assertRaisesRegex(ValueError, "reserve"):
                reserve(conn, self.root, "codex", "too-much", now())

    def test_concurrency_and_daily_schedule_limit(self):
        self.insert_run(1, "running")
        with database(self.root) as conn:
            with self.assertRaisesRegex(ValueError, "already running"):
                reserve(conn, self.root, "codex", "concurrent", now())
            conn.execute("UPDATE runs SET status='done'")
            reserve(conn, self.root, "codex", "second", now())
            conn.execute("UPDATE runs SET status='done'")
            reserve(conn, self.root, "codex", "third", now())
            conn.execute("UPDATE runs SET status='done'")
            with self.assertRaisesRegex(ValueError, "scheduled-run"):
                reserve(conn, self.root, "codex", "fourth", now())

    def test_quota_breach_recorded_and_quarantined(self):
        self.adapter("print('{\"usage\": 85, \"summary\": \"over cap\"}')")
        self.assertEqual(run("codex", "execute", self.root), 1)
        with database(self.root) as conn:
            self.assertEqual(quota(conn, self.root, "codex", now())[0], 85)
            with self.assertRaisesRegex(ValueError, "quarantined"):
                reserve(conn, self.root, "codex", "tomorrow", now() + timedelta(days=1))
        self.assertIn("LOW-COMPUTE: true", (self.root / "agents/codex-LOW-COMPUTE.md").read_text())

    def test_timeout_retains_reservation(self):
        self.adapter("import time\ntime.sleep(10)")
        os.environ["AGENT_TIMEOUT_SECONDS"] = "1"
        self.assertEqual(run("codex", "execute", self.root), 1)
        with database(self.root) as conn:
            self.assertEqual(tuple(conn.execute("SELECT status,quota_reserved FROM runs").fetchone()), ("timeout", 20))

    def test_invalid_receipt_fails_without_refund(self):
        self.adapter("print('not a usage receipt')")
        self.assertEqual(run("codex", "execute", self.root), 1)
        with database(self.root) as conn:
            self.assertEqual(tuple(conn.execute("SELECT status,quota_reserved FROM runs").fetchone()), ("failed", 20))

    def test_missing_mail_config_and_mocked_tls_deduplication(self):
        path = generate(self.root)
        with self.assertRaisesRegex(ValueError, "not configured"):
            send_report(path, self.root)
        os.environ.update(OWNER_EMAIL="owner@example.test", SMTP_HOST="smtp.example.test",
                          SMTP_USER="test", SMTP_PASSWORD="test", SMTP_FROM="team@example.test")
        with patch("daily_report.smtplib.SMTP") as smtp:
            self.assertEqual(send_report(path, self.root), "Emailed to owner")
            self.assertEqual(send_report(path, self.root), "Already emailed for this day")
            client = smtp.return_value.__enter__.return_value
            client.starttls.assert_called_once()
            client.login.assert_called_once()
            client.send_message.assert_called_once()
            self.assertEqual(client.send_message.call_args.args[0]["To"], "owner@example.test")

    def test_malformed_memory_aborts_before_execution(self):
        (self.root / "tasks/BAD.md").write_text("not front matter", encoding="utf-8")
        with self.assertRaises(ValueError):
            scan(self.root)
        self.assertEqual(run("codex", "execute", self.root), 1)


    def test_claude_adapter_with_fake_cli(self):
        fake = self.root / "fake_claude.py"
        fake.write_text("import sys,json\nassert sys.argv[1:]==['-p','--output-format','json','--max-turns','30']\n"
                        "assert 'current-goal.md' in sys.stdin.read()\n"
                        "print(json.dumps({'num_turns':3,'usage':{'input_tokens':17,'output_tokens':9},'result':'done'}))", encoding="utf-8")
        os.environ["CLAUDE_CLI_COMMAND"] = json.dumps([sys.executable, str(fake)])
        os.environ["CLAUDE_METERED_COMMAND"] = json.dumps([sys.executable, str(ROOT / "scripts/adapters/claude_adapter.py")])
        self.assertEqual(run("claude", "plan", self.root), 0)
        log = next((self.root / "logs/runs").glob("claude-*.md")).read_text(encoding="utf-8")
        self.assertIn('"usage": 3', log)
        self.assertIn('"input_tokens": 17', log)
        fake.write_text("print('{\"result\":\"missing usage\"}')", encoding="utf-8")
        self.assertEqual(run("claude", "review", self.root), 1)
        with database(self.root) as conn:
            self.assertEqual(quota(conn, self.root, "claude", now())[0], 60)

    def test_codex_adapter_with_fake_cli(self):
        fake = self.root / "fake_codex.py"
        events = [{"type": "turn.started"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 23, "cached_input_tokens": 2, "output_tokens": 5}}]
        fake.write_text("import sys\nassert sys.argv[1:]==['exec','--json','--sandbox','workspace-write','-']\n"
                        "assert 'current-goal.md' in sys.stdin.read()\nprint(" + repr("\n".join(json.dumps(e) for e in events)) + ")", encoding="utf-8")
        os.environ["CODEX_CLI_COMMAND"] = json.dumps([sys.executable, str(fake)])
        os.environ["CODEX_METERED_COMMAND"] = json.dumps([sys.executable, str(ROOT / "scripts/adapters/codex_adapter.py")])
        self.assertEqual(run("codex", "execute", self.root), 0)
        log = next((self.root / "logs/runs").glob("codex-*.md")).read_text(encoding="utf-8")
        self.assertIn('"usage": 1', log)
        self.assertIn('"output_tokens": 5', log)
        fake.write_text("print('{\"type\":\"turn.completed\"}')", encoding="utf-8")
        self.assertEqual(run("codex", "execute", self.root), 1)
        with database(self.root) as conn:
            self.assertEqual(quota(conn, self.root, "codex", now())[0], 40)

    def counter_task(self):
        task, _ = read_front(self.root / "tasks/TASK-001.md")
        task.update(id="TASK-COUNTER", attempts=0, review_round=0, status="review")
        path = self.root / "tasks/TASK-COUNTER.md"
        write_front(path, task, "Counter fixture")
        return path

    def test_counter_increments_persist_and_tampering_is_reported(self):
        path = self.counter_task()
        record_counter("TASK-COUNTER", "attempt", "Start work", root=self.root)
        task, body = read_front(path)
        self.assertEqual(task["attempts"], 1)
        self.assertEqual(record_counter("TASK-COUNTER", "review", "Fix findings", "changes", self.root)["status"], "doing")
        task, body = read_front(path)
        self.assertEqual(task["review_round"], 1)
        self.assertTrue((self.root / "reviews/REV-003.md").exists())
        task["attempts"] = 0
        write_front(path, task, body)
        self.assertIn("TASK-COUNTER", scan(self.root)["protocol_violations"])
        self.assertEqual(read_front(path)[0]["status"], "blocked")
        with self.assertRaises(ValueError):
            record_counter("TASK-COUNTER", "attempt", "Bypass", root=self.root)

    def test_reviews_rebuild_after_database_loss_and_avoid_restored_ids(self):
        path = self.counter_task()
        scan(self.root)
        with database(self.root) as conn:
            self.assertEqual({r[0] for r in conn.execute("SELECT id FROM reviews")}, {"REV-001", "REV-002"})
            conn.execute("INSERT INTO reviews VALUES('REV-050','TASK-COUNTER','changes','reviews/REV-050.md')")
        record_counter("TASK-COUNTER", "review", "Restored DB has a higher ID", "changes", self.root)
        self.assertTrue((self.root / "reviews/REV-051.md").exists())
        (self.root / "db/company.sqlite").unlink()
        scan(self.root)
        with database(self.root) as conn:
            self.assertEqual(conn.execute("SELECT status FROM reviews WHERE id='REV-051'").fetchone()[0], "changes")
            self.assertIsNone(conn.execute("SELECT id FROM reviews WHERE id='REV-050'").fetchone())
        task, body = read_front(path)
        task["status"] = "review"
        write_front(path, task, body)
        record_counter("TASK-COUNTER", "review", "Review after database rebuild", "pass", self.root)
        self.assertEqual(read_front(self.root / "reviews/REV-052.md")[0]["result"], "pass")

    def test_third_changes_review_is_refused_before_writes(self):
        path = self.counter_task()
        for index in range(3):
            task, body = read_front(path)
            task["status"] = "review"
            write_front(path, task, body)
            if index == 2:
                with self.assertRaisesRegex(ValueError, "Two review rounds"):
                    record_counter("TASK-COUNTER", "review", "Third changes", "changes", self.root)
            else:
                record_counter("TASK-COUNTER", "review", f"Round {index + 1}", "changes", self.root)
        self.assertEqual(read_front(path)[0]["review_round"], 2)
        self.assertFalse((self.root / "reviews/REV-005.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
