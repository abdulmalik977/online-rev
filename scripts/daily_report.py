"""Nine ordered sections, at most 30 lines; optional owner-only SMTP delivery."""
import argparse
import json
from datetime import timedelta
from email.message import EmailMessage
import os
import smtplib
import ssl
import sys

from common import (ROOT, approvals, atomic_write, database, local_day, locked,
                    now, quota, stamp)
from watchdog import scan

SECTIONS = ("Revenue", "Pipeline", "Yesterday", "Problems", "Today", "Needs owner approval",
            "Agent health", "Loops detected", "Critical")


def short(items):
    text = "; ".join(str(item) for item in items) or "None"
    return " ".join(text.split())[:900]


def sender_pipeline(root, at):
    path = root / '.runtime/sender/pipeline.json'
    if not path.exists():
        return None
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from sender.calendar import local_day as central_day
    data = json.loads(path.read_text(encoding='utf-8'))
    expected = str(central_day(at) - timedelta(days=1))
    if data.get('schema_version') != 1 or data.get('timezone') != 'America/Chicago' or data.get('report_day') != expected:
        raise ValueError('Sender pipeline snapshot is stale or invalid')
    for key in ('emails_sent', 'replies', 'paid'):
        if type(data.get(key)) is not int or data[key] < 0:
            raise ValueError('Invalid sender pipeline counter')
    views = data.get('sample_views')
    if views is not None and (type(views) is not int or views < 0):
        raise ValueError('Invalid sender views counter')
    return data


def generate(root=ROOT, at=None):
    at = at or now()
    sender = sender_pipeline(root, at)
    findings = scan(root, at)
    day = local_day(at)
    yesterday = local_day(at - timedelta(days=1))
    with locked(root), database(root) as conn:
        pending = approvals(root)
        revenue = conn.execute("SELECT unit,SUM(value) FROM metrics WHERE name='revenue' AND day BETWEEN ? AND ? GROUP BY unit",
                               (day[:8] + "01", day)).fetchall()
        pipeline = {row[0]: row[1] for row in conn.execute(
            "SELECT name,SUM(value) FROM metrics WHERE day=? AND unit='count' GROUP BY name", (day,))}
        previous = [f"{r['agent']} {r['status']} ({r['id']})" for r in conn.execute(
            "SELECT * FROM runs WHERE day=? ORDER BY started", (yesterday,))]
        today = []
        health = []
        for agent in ("claude", "codex"):
            ids = [r[0] for r in conn.execute("SELECT id FROM tasks WHERE owner=? AND status IN ('todo','doing','review') ORDER BY id", (agent,))]
            today.append(f"{agent}: {', '.join(ids) or 'no actionable tasks'}")
            used, budget = quota(conn, root, agent, at)
            health.append(f"{agent}: {used / budget:.0%} ({used}/{budget} execution credits)")
        blocked = [r[0] for r in conn.execute("SELECT id FROM tasks WHERE status='blocked'")]
        issues = ([f"STALE 24h: {x}" for x in findings["stale"]]
                  + [f"missing success_metric: {x}" for x in findings["missing_metrics"]]
                  + [f"blocked: {x}" for x in blocked]
                  + [f"task admission closed: {x}" for x in findings["capacity"]]
                  + [f"failed run: {r[0]}" for r in conn.execute(
                      "SELECT id FROM runs WHERE day=? AND status IN ('failed','timeout','quota_breach')", (day,))])
        critical = ([f"ESCALATE >48h: {x}" for x in findings["old_approvals"]]
                    + [f"LOW-COMPUTE: {x}" for x in findings["low_compute"]]
                    + [f"attempt limit killed: {x}" for x in findings["killed"]])
        values = [short([f"{r[0]} {r[1]:.2f} MTD" for r in revenue]) + "; target SAR 10,000/month",
                  " / ".join(f"{label}: {pipeline.get(key, 0):g}" for label, key in (
                      ("emails sent", "emails_sent"), ("replies", "replies"),
                      ("sample views", "sample_views"), ("paid", "paid"))),
                  short(previous) if previous else "No recorded runs yesterday",
                  short(issues), short(today), short([f"{a['id']}: {a['description']}" for a in pending]),
                  short(health), short(findings["loops"]), short(critical)]
        if sender is not None:
            values[1] = f"Central closed {sender['report_day']}: " + " / ".join(
                f"{label}: {'n/a' if sender[key] is None else sender[key]}" for label, key in (
                    ('emails sent', 'emails_sent'), ('replies', 'replies'), ('sample views', 'sample_views'), ('paid', 'paid')))
            values[8] = short(critical + sender.get('critical', []))
        lines = [f"# Daily report — {day} (Asia/Riyadh)"]
        for title, value in zip(SECTIONS, values):
            lines.extend([f"## {title}", value])
        assert len(lines) <= 30
        path = root / f"logs/daily/{day}.md"
        atomic_write(path, "\n".join(lines) + "\n")
    return path


def send_report(path, root=ROOT):
    required = ("OWNER_EMAIL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError("Email not configured: " + ", ".join(missing))
    owner, sender = os.environ["OWNER_EMAIL"], os.environ["SMTP_FROM"]
    if any(c in owner + sender for c in "\r\n,;") or "@" not in owner or "@" not in sender:
        raise ValueError("Configure one owner address and one sender address")
    marker = root / f".runtime/report-sent-{path.stem}"
    with locked(root):
        if marker.exists():
            return "Already emailed for this day"
        message = EmailMessage()
        message["From"], message["To"] = sender, owner
        message["Subject"] = f"Company OS — {path.stem}"
        message.set_content(path.read_text(encoding="utf-8"))
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            smtp.send_message(message)
        atomic_write(marker, stamp() + "\n")
    return "Emailed to owner"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", action="store_true", help="Send via environment-configured SMTP")
    args = parser.parse_args()
    try:
        path = generate()
        print(path)
        if args.email:
            print(send_report(path))
        return 0
    except (ValueError, OSError, RuntimeError, smtplib.SMTPException) as error:
        print(f"REPORT ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
