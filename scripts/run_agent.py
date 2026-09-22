"""Finite scheduled run with conservative upfront budget reservation.

Built-in CLI adapters consume context on stdin and report observable turns/tokens.
One credit is one CLI-reported turn, not a hard cap on provider rolling quotas.
"""
import argparse
import json
import math
import os
import signal
import shutil
import subprocess
import sys
from uuid import uuid4

from common import (ROOT, OPEN, add_approval, agent_config, atomic_write, database, local_day,
                    locked, now, quota, stamp, tasks)
from watchdog import scan


def reserve(conn, root, agent, ident, at):
    if (root / f"agents/{agent}-QUOTA-BREACH.md").exists():
        raise ValueError("Adapter quarantined after quota breach; owner must review before resuming")
    config = agent_config(root, agent)
    used, budget = quota(conn, root, agent, at)
    cost = config["run_budget"]
    if used * 5 >= budget * 4 or (used + cost) * 5 > budget * 4:
        raise ValueError("Quota reserve reached or next run would consume the 20% reserve")
    if conn.execute("SELECT 1 FROM runs WHERE agent=? AND status='running'", (agent,)).fetchone():
        raise ValueError("Agent already running; inspect interrupted runs before recovery")
    count = conn.execute("SELECT COUNT(*) FROM runs WHERE agent=? AND day=? AND quota_reserved>0",
                         (agent, local_day(at))).fetchone()[0]
    if count >= (2 if agent == "claude" else 3):
        raise ValueError("Daily scheduled-run limit reached")
    conn.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)",
                 (ident, agent, stamp(at), None, local_day(at), cost, "running", "reserved before launch"))
    return cost


def invoke(command, prompt, root, environment, timeout):
    # POSIX cron deployment: terminate the entire process group on timeout.
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", cwd=root, env=environment,
                               start_new_session=(os.name == "posix"))
    try:
        output, _ = process.communicate(prompt, timeout=timeout)
    except BaseException:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.communicate()
        raise
    return process.returncode, output


def context(root, agent):
    paths = [root / "company/current-goal.md", root / "company/metrics.md",
             root / f"agents/{agent}.md", root / f"agents/{agent}-LOW-COMPUTE.md"]
    paths += [path for path, task, _ in tasks(root) if task["status"] in OPEN]
    return "\n\n".join(f"# {path.relative_to(root).as_posix()}\n{path.read_text(encoding='utf-8')}" for path in paths)


def run(agent, mode, root=ROOT, dry_run=False):
    at = now()
    ident = f"{agent}-{at.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:6]}"
    log = root / f"logs/runs/{ident}.md"
    status, detail, reserved, prompt = "blocked", "Run not started", False, ""
    code, telemetry = 1, {}
    try:
        scan(root, at)
        prompt = context(root, agent)
        if dry_run:
            status, detail, code = "dry-run", "Context loaded; no agent launched and no quota charged", 0
            return code
        raw_command = os.environ.get(f"{agent.upper()}_METERED_COMMAND")
        if not raw_command and not shutil.which(agent):
            raise ValueError(f"Missing {agent} CLI; install and authenticate it on the operating host")
        command = json.loads(raw_command) if raw_command else [sys.executable, str(ROOT / f"scripts/adapters/{agent}_adapter.py")]
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise ValueError("Metered command must be a JSON array of executable and arguments")
        timeout = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "900"))
        if not 1 <= timeout <= 3600:
            raise ValueError("AGENT_TIMEOUT_SECONDS must be 1..3600")
        with locked(root), database(root) as conn:
            maximum = reserve(conn, root, agent, ident, at)
        reserved = True
        # Refresh the flag immediately after reservation, before handing context to the adapter.
        scan(root, at)
        prompt = context(root, agent)
        environment = dict(os.environ, COMPANY_MAX_CREDITS=str(maximum), COMPANY_AGENT=agent,
                           COMPANY_RUN_MODE=mode, COMPANY_RUN_ID=ident)
        # Do not hand email credentials to an agent adapter.
        for key in list(environment):
            if key.startswith("SMTP_") or key == "OWNER_EMAIL":
                environment.pop(key)
        returncode, output = invoke(command, prompt, root, environment, timeout)
        receipt = json.loads(output) if output.strip() else {}
        telemetry = {k: receipt[k] for k in ("usage", "tokens") if k in receipt} if isinstance(receipt, dict) else {}
        usage = receipt.get("usage") if isinstance(receipt, dict) else None
        if type(usage) not in (float, int) or not math.isfinite(usage) or usage < 0:
            raise ValueError("Adapter must return a finite nonnegative usage receipt")
        if usage > maximum:
            status = "quota_breach"
            with locked(root), database(root) as conn:
                conn.execute("UPDATE runs SET quota_reserved=? WHERE id=?", (math.ceil(usage), ident))
                atomic_write(root / f"agents/{agent}-QUOTA-BREACH.md",
                             f"# Adapter quarantined\nRun: {ident}\nUsage: {usage}; cap: {maximum}\n")
                add_approval(root, f"QUOTA-{agent}", "Quota adapter exceeded cap; review before re-enabling", now())
            raise ValueError("Adapter violated its hard cap; disable adapter and inspect provider usage")
        if returncode:
            status = "failed"
            raise ValueError(f"Adapter exited {returncode}; reservation retained")
        if not isinstance(receipt.get("summary"), str):
            raise ValueError("Adapter must return a summary string")
        status, detail, code = "done", receipt["summary"][:4000], 0
    except subprocess.TimeoutExpired:
        status, detail = "timeout", "Adapter timed out; reservation retained (POSIX process group terminated)"
    except (ValueError, RuntimeError, OSError) as error:
        detail = str(error)
        if reserved and status == "blocked":
            status = "failed"
    finally:
        atomic_write(log, f"# {agent} run — {mode}\nStarted: {stamp(at)}\nFinished: {stamp()}\n"
                     f"Status: {status}\nCLI usage: {json.dumps(telemetry)}\n{detail}\n\n## Startup context\n{prompt or 'Unavailable; see failure above'}\n")
        if reserved:
            with locked(root), database(root) as conn:
                conn.execute("UPDATE runs SET status=?,finished=?,detail=? WHERE id=?",
                             (status, stamp(), detail, ident))
            scan(root)
        print(f"{status}: {log}")
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", choices=("claude", "codex"))
    parser.add_argument("mode", choices=("plan", "review", "execute"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if (args.agent == "claude" and args.mode == "execute") or (args.agent == "codex" and args.mode != "execute"):
        parser.error("Claude uses plan/review; Codex uses execute")
    return run(args.agent, args.mode, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
