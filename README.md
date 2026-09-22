# Company OS v0

Day 1–2 operating memory and watchdog. Python 3.10+ standard library, Markdown,
SQLite, and cron; no LLM calls in monitoring or reports. This repository root is
the `company-os/` directory shown in CODEX-KICKOFF.md.

Read [design.md](design.md) first. It was written and checked at 15 lines before code.
Read [BLOCKERS.md](BLOCKERS.md) for the remaining live-operation inputs.

## Local verification

```sh
python scripts/watchdog.py --test
python scripts/test_operations.py
python scripts/watchdog.py
python scripts/daily_report.py
bash scripts/run_agent.sh codex execute --dry-run
bash scripts/run_agent.sh claude plan --dry-run
```

On Windows use `python scripts/run_agent.py codex execute --dry-run` if Bash has no
`python3`; alternatively set `PYTHON` to the Python executable when using Git Bash.
All tests use temporary storage, fake adapters, or mocked SMTP. No billable agent
work or real email is needed. TASK-LOOP is an intentional seed fixture retained
as blocked evidence. Revenue and pipeline seed data are zero, not sales activity.
The report has nine sections and 19 lines. Monetary currencies stay separate.

## Storage and task admission

Markdown is authoritative for tasks, roles, decisions, and approval entries.
SQLite indexes tasks and contains runs, reviews, leads, customers, and metrics.
The initial database is included as requested. Later runtime databases should be
backed up on the operating host, not merged across concurrent Git clones.
Do not commit actual customer data or secrets. Markdown changes made by adapters
must be committed explicitly; the runner does not automatically publish them.

Front matter is a flat YAML subset: one `key: value` per line; use JSON double
quotes for text (including timestamps), integer counters, no nested YAML or arrays.
Required task fields are shown in tasks/TASK-001.md. Missing/blank success_metric
is accepted only so the watchdog can persist a rejected (`blocked`) status.
Other malformed fields stop the operation with a nonzero exit.

To create a task, prepare a `todo` file outside tasks/ and run:

```sh
python scripts/watchdog.py --create /path/to/candidate.md
```

The command validates the task, checks for duplicates, and rejects a sixth open
task under a writer lock. Open means todo/doing/review/blocked. Resolve a task to
done/killed to free capacity. Agents must use this command; direct filesystem
writes cannot be policed as a security boundary. The watchdog reports admission
closed even when files are introduced manually. Attempt overflow takes precedence
over other rules: killed tasks remain killed. Repeated scans do not duplicate
approval entries or transition logs. Staleness begins at 24h; owner escalation is
strictly older than 48h using each approval's timestamp, not file modification time.

Approval format: `- [ ] ID | ISO-8601 UTC timestamp | description`.
Resolve by moving the whole entry from pending.md to done.md, change `[ ]` to `[x]`,
and retain its ID/timestamp. A resolved approval does not itself reset task state;
record the owner's decision and explicitly update the task counters/status.

## Quota and scheduled execution

Agents have 100 daily execution credits in agents/*.md. Claude reserves at most
30/run, twice/day; Codex 20/run, three times/day. These defaults are accounting
units, **not observed subscription or token limits**. Before production, map them
to a trustworthy provider budget and configure a hard-capped metered adapter.
The adapter must preflight remaining provider allowance and enforce its run cap
before/during requests, including retries and tools. A receipt alone is not a cap.
No generic unmetered agent command is configured or launched by this repository.

Configure `CLAUDE_METERED_COMMAND` / `CODEX_METERED_COMMAND` as a JSON array of
executable and arguments (no shell evaluation). Adapter contract:

- Read the startup context from stdin; obey the current goal, role, flags, and tasks.
- Read `COMPANY_MAX_CREDITS`, `COMPANY_AGENT`, `COMPANY_RUN_MODE`, and `COMPANY_RUN_ID`.
- Enforce the credit maximum using the chosen provider's actual accounting.
- Finish with one JSON object on stdout: `{"usage": 7, "summary": "Evidence and result"}`.
- Avoid detached child processes; clean up provider work on timeout/termination.

Reservation is durable before launch and is never refunded automatically, even on
failure. Runs that would cross 80% are refused; exactly 80% is permitted as the end
of a run, after which new launches stop. LOW-COMPUTE is true strictly above 80%,
with a separate RESERVE-REACHED flag at 80%. Day resets use Riyadh time. No overlapping
runs for the same agent are allowed. A reported budget breach charges the larger
usage, creates an owner approval, and quarantines that adapter across future days.
Only remove agents/<agent>-QUOTA-BREACH.md after the owner reviews a repaired adapter.
AGENT_TIMEOUT_SECONDS defaults to 900 (maximum 3600). POSIX timeouts kill the whole
process group; Windows is for local verification, not production cron execution.

The host must supply Python and cron with `CRON_TZ`, or use Riyadh as its host
timezone. Edit the deployment path in scripts/company.cron, provision a private
environment wrapper, then install with `crontab scripts/company.cron` on that host.
Do not put credentials in the committed crontab. Watchdog runs at :05 and :35;
email at 08:00; Claude at 09:00/17:00; Codex at 10:00/14:00/18:00 Riyadh.
Runs are finite invocations, never continuous loops. Nothing installs cron locally.

## Owner email

Set OWNER_EMAIL, SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD,
and SMTP_FROM in the private cron environment. `daily_report.py --email` uses
authenticated STARTTLS to send only to the configured owner. Without settings,
it still generates the report but returns an explicit email configuration error.
Daily successful-send markers avoid normal duplicate sends. SMTP cannot guarantee
exactly-once delivery after a crash between acceptance and the local sent marker.
No real SMTP delivery has been tested; the automated SMTP check is mocked.

## Recovery and review

All writers use .runtime/write.lock. If a process crashes, first ensure it and its
children have stopped, then remove only that empty lock directory. Never clear
a live lock. Review interrupted `running` rows and mark them failed with a finish
timestamp, retaining quota reservations. Markdown is re-indexed on the next scan;
if a crash interrupts a multi-file transition, rerun watchdog after inspection.
Do not run two hosts against the same workspace or database.

REV-001 is an open Markdown review request for Claude, not a completed review or
an already-delivered message. No Claude process or sub-agent was launched.
