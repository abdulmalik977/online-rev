"""Small shared storage layer; no third-party dependencies."""
import contextlib
import json
import os
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
LOCAL = timezone(timedelta(hours=3), "Asia/Riyadh")
OPEN = {"todo", "doing", "review", "blocked"}
FIELDS = {"id", "title", "owner", "status", "goal", "evidence", "definition_of_done",
          "success_metric", "attempts", "review_round", "quota_budget", "created", "updated"}


def now():
    return datetime.now(timezone.utc)


def stamp(value=None):
    return (value or now()).isoformat(timespec="seconds")


def parse_time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    return result


def local_day(value=None):
    return (value or now()).astimezone(LOCAL).date().isoformat()


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    os.replace(temp, path)


@contextlib.contextmanager
def locked(root):
    runtime = root / ".runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    lock = runtime / "write.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise RuntimeError("Writer already active or stale .runtime/write.lock; inspect before recovery")
    try:
        yield
    finally:
        lock.rmdir()


def read_front(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path}: missing front matter")
    end = lines.index("---", 1)
    data = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith("#"):
            continue
        key, separator, raw = line.partition(":")
        if not separator or not re.fullmatch(r"[a-z_]+", key) or key in data:
            raise ValueError(f"{path}: invalid/duplicate field {key}")
        raw = raw.strip()
        if raw.startswith('"') or re.fullmatch(r"-?\d+", raw):
            data[key] = json.loads(raw)
        elif raw in {"", "null", "~"}:
            data[key] = ""
        elif re.fullmatch(r"[A-Za-z0-9_./+ -]+", raw):
            data[key] = raw
        else:
            raise ValueError(f"{path}: quote scalar values with JSON double quotes")
    return data, "\n".join(lines[end + 1:]).strip()


def write_front(path, data, body):
    text = "---\n" + "".join(f"{key}: {json.dumps(value, ensure_ascii=False)}\n" for key, value in data.items())
    atomic_write(path, text + "---\n" + body.strip() + "\n")


def validate(task):
    missing = FIELDS - task.keys() - {"success_metric"}
    if missing:
        raise ValueError(f"Missing task fields: {sorted(missing)}")
    if not re.fullmatch(r"TASK-[A-Za-z0-9-]+", task["id"]):
        raise ValueError("Invalid task ID")
    if task["owner"] not in {"claude", "codex"} or task["status"] not in OPEN | {"done", "killed"}:
        raise ValueError("Invalid task owner/status")
    for key in ("attempts", "review_round", "quota_budget"):
        if type(task[key]) is not int or task[key] < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    for key in FIELDS - {"attempts", "review_round", "quota_budget", "success_metric"}:
        if not isinstance(task[key], str) or not task[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if not isinstance(task.get("success_metric", ""), str):
        raise ValueError("success_metric must be a string")
    if parse_time(task["updated"]) < parse_time(task["created"]):
        raise ValueError("Task updated precedes created")


def tasks(root):
    result = []
    for path in sorted((root / "tasks").glob("*.md")):
        data, body = read_front(path)
        validate(data)
        if path.stem != data["id"]:
            raise ValueError(f"Task filename disagrees with ID: {path}")
        result.append((path, data, body))
    return result


@contextlib.contextmanager
def database(root):
    (root / "db").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / "db/company.sqlite", timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, owner TEXT, status TEXT, updated TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, agent TEXT, started TEXT, finished TEXT,
            day TEXT, quota_reserved INTEGER, status TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, task_id TEXT, status TEXT, path TEXT);
        CREATE TABLE IF NOT EXISTS leads(id TEXT PRIMARY KEY, company TEXT, country TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY, lead_id TEXT, currency TEXT, monthly_amount REAL);
        CREATE TABLE IF NOT EXISTS metrics(day TEXT, name TEXT, value REAL, unit TEXT,
            PRIMARY KEY(day, name, unit));
    """)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def sync_tasks(conn, records):
    conn.execute("DELETE FROM tasks")
    conn.executemany("INSERT INTO tasks VALUES(?,?,?,?,?)", [
        (t["id"], t["owner"], t["status"], t["updated"], json.dumps(t)) for _, t, _ in records])


def agent_config(root, agent):
    data, _ = read_front(root / f"agents/{agent}.md")
    for key in ("quota_budget", "run_budget"):
        if type(data.get(key)) is not int or data[key] <= 0:
            raise ValueError(f"Invalid {agent} {key}")
    return data


def quota(conn, root, agent, at):
    budget = agent_config(root, agent)["quota_budget"]
    used = conn.execute("SELECT COALESCE(SUM(quota_reserved),0) FROM runs WHERE agent=? AND day=?",
                        (agent, local_day(at))).fetchone()[0]
    return used, budget


def approvals(root, resolved=False):
    path = root / ("approvals/done.md" if resolved else "approvals/pending.md")
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ["):
            match = re.fullmatch(r"- \[([ x])\] ([A-Za-z0-9_-]+) \| ([^|]+) \| (.+)", line)
            if not match:
                raise ValueError(f"Malformed approval: {line}")
            check, ident, created, description = match.groups()
            parse_time(created.strip())
            if check == " " or resolved:
                result.append({"id": ident, "created": created.strip(), "description": description})
    return result


def add_approval(root, ident, description, at):
    if ident in {a["id"] for a in approvals(root) + approvals(root, True)}:
        return
    path = root / "approvals/pending.md"
    previous = path.read_text(encoding="utf-8") if path.exists() else "# Pending approvals\n"
    atomic_write(path, previous.rstrip() + f"\n- [ ] {ident} | {stamp(at)} | {description}\n")


def seed(conn, at):
    for name in ("emails_sent", "replies", "sample_views", "paid", "revenue"):
        conn.execute("INSERT OR IGNORE INTO metrics VALUES(?,?,?,?)",
                     (local_day(at), name, 0, "SAR" if name == "revenue" else "count"))
    conn.execute("INSERT OR IGNORE INTO reviews VALUES(?,?,?,?)",
                 ("REV-001", "TASK-001", "open", "reviews/REV-001.md"))
