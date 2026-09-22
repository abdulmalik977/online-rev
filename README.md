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
SQLite, watchdog.json, LOW-COMPUTE flags, and .runtime/ are local and ignored by Git.
A scan creates the database and rebuilds the task index. Keep the local database
backed up on the operating host: sync_tasks does not restore historical runs or
metrics from Markdown. Ignored does not mean disposable. Audit Markdown in
logs/runs/ and logs/daily/ stays tracked and is committed at handoff.
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
record the owner's decision and update status as appropriate; never edit counters directly.

Use script-owned counter commands under the same writer lock:

```sh
python scripts/watchdog.py --attempt TASK-ID --note "Starting a bounded attempt"
python scripts/watchdog.py --review TASK-ID --result changes --note "Reviewer findings"
```

Attempts increment attempts and updated. Reviews require status=review, append a
REV-nnn.md decision, increment review_round, and set pass=done, changes=doing,
reject=killed. Submit the next review by setting status=review without changing
counters. Here review_round counts recorded review decisions, not merely opening
an invitation: REV-001 can invite round 2 while TASK-001 retains one completed
review. The third decision triggers rule 1 on the next scan. Counter snapshots in
reviews/counters-TASK-ID.md are script-owned Markdown audit lines. Initial legacy
values are explicitly migrated once; new tasks start at zero. Missing history
means zero, never permission to adopt edited counters. A mismatch is reported as
protocol_violations, creates an owner escalation, and blocks the task. A crash
between history and task writes also fails closed for inspection, not silent repair.

## Quota and scheduled execution

Agents have 100 daily credits. Claude reserves 30/run, twice/day; Codex 20/run,
three times/day. **1 credit = 1 observable CLI turn**, not a provider quota unit.
Built-in scripts/adapters/{claude,codex}_adapter.py are the defaults. Install and
authenticate the corresponding CLI on the host; missing CLIs fail before reservation.
Existing *_METERED_COMMAND JSON arrays remain optional adapter overrides.
CLAUDE_CLI_COMMAND / CODEX_CLI_COMMAND JSON arrays override CLI paths (also used by
fake-CLI tests). No shell evaluation or permission-bypass flags are used.

CLI verification on 2026-09-22:

- Codex installed: `codex-cli 0.154.0-alpha.6.2`; checked `codex exec --help` locally.
  Invocation: `codex exec --json --sandbox workspace-write -`, context through stdin.
  There is no --max-turns flag in this version. The adapter submits exactly one
  prompt with no resume/retry: cap=min(COMPANY_MAX_CREDITS, 1) conversation turn.
  It counts turn.completed events, requires matching turn.started and token usage,
  and rejects unexpected extra turns. This does not cap internal model/tool steps.
  [Official OpenAI JSONL documentation](https://developers.openai.com/codex/noninteractive).
- Claude is not installed here, so no installed Claude version was verified.
  Invocation: `claude -p --output-format json --max-turns N`, context through stdin;
  N=COMPANY_MAX_CREDITS. Flags checked in the
  [official Claude CLI reference](https://code.claude.com/docs/en/cli-reference).
  The adapter requires num_turns plus input_tokens/output_tokens in usage; verify
  the deployed version with `claude --version` and `claude --help` before activation.

The adapters run inside the existing runner timeout/process group. They return
usage, summary, and tokens; the runner writes token totals in each run log for
calibration, including receipts from unsuccessful CLI runs. Missing usage is an
error with the reservation retained. Claude agentic turns and Codex conversation
turns have different granularity; credits are local scheduling measures, not
proof of equivalent provider activity. Five-hour rolling-window throttling remains
an accepted residual risk under the 2+3 daily schedule. No subscription CLI can
provide an external hard cap on the provider allowance; SETUP-QUOTA is resolved
by this practical policy. No live provider work was launched during these tests.

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

REV-001 preserves Claude round 1 and opens round 2 for the bounded fixes.
No round-2 verdict is presumed. No Claude process or sub-agent was launched.
