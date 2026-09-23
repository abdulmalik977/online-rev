# TASK-009: local sender and inbox implementation

DEC-008 implementation, session **1/3**. Standard-library Python 3.11+, private
SQLite, fake SMTP/IMAP, and loopback HTTP tests. No credentials, provider connection,
outreach, or deployment. **The complete test suite is red**: three executable
specification conflicts remain visible, with proposed amendments in their test
docstrings. TASK-008 remains closed; this does not open another prose review.

From the repository root:

```powershell
# Complete suite: currently returns nonzero for three explicit spec conflicts.
python -W error::ResourceWarning -m unittest discover -s sender/tests -v

# The twenty numbered cases, seven extra cases, and operational/integration tests.
python -m unittest sender.tests.test_acceptance sender.tests.test_operations sender.tests.test_integration -v

# Execute just the unresolved rules and read each test's proposed amendment.
python -m unittest sender.tests.test_spec_conflicts -v

# Prints every section-8 gate; exits 2 (RED), including disabled real sending.
python -m sender gate
```

Results are recorded in [session-1-results.json](session-1-results.json). There are
no skipped or `expectedFailure` tests hiding the remaining failures:

- A4 retries after IMAP absence even when SMTP accepted the first message without
  a Sent copy. The fake proves duplicate acceptance. The test proposes retaining
  unknown status until definitive reconciliation.
- A6 gives non-paying prospects no payment/confirmation timestamp for the owner
  response deadline. The test proposes receipt time for owner responses only.
- A6's first-512-byte fallback ID can collide for distinct messages and drop an
  opt-out. The test proposes hashing the full canonical message/provider identity.

See [test descriptions](tests/test_spec_conflicts.py) for exact reproductions and
the smallest proposed changes. Runtime follows these disputed amendments literally
for demonstration; **do not use it to send real mail**. The engine enforces offline
transports, and the CLI has no send/IMAP-connect command.

## Components and data boundary

- `calendar.py`: pinned America/Chicago TZif, DST, holidays, 0/3/8 offsets and
  immutable generation-based expiry. `scheduler.tick` is one bounded fake tick;
  it reconciles at most every 30 minutes and prioritizes service replies.
- `rules.py`: email/DSN parsing, quote stripping, A1 matching/negation, A2 terminal
  states and reply arbitration, A5 origin versus response-suppression signals.
- `store.py`, `engine.py`: prospects, durable intents, inbound dedup, suppression
  with all reasons retained, queue, orders, complaint/bounce events and mailboxes.
  Intent commits precede transport; a second SQLite write transaction serializes
  the final check and transport. Five-minute stale intents become unknown at the
  next reconciliation tick; definite failures allow one retry.
- `optout.py`: GET never suppresses; token POST is idempotent and sends nothing.
  The test server binds **127.0.0.1 only**. Public HTTPS hosting is not installed.
- `templates.py`: fixed plain text, stable subject/mailbox hashing, safe headers,
  real thread references, unsubscribe headers and unresolved-placeholder refusal.
- `transports.py`: no connection constructors or credentials. SMTP/IMAP adapters
  describe the protocol boundary but are rejected by this task's offline engine.
- `metrics.py`: closed-Central-day export, unique-prospect rates, deduped orders,
  filtered view events, test/internal exclusions and missing analytics as null.
  The current report reads `.runtime/sender/pipeline.json` if explicitly exported;
  it labels the Central day and displays `n/a` for absent analytics. Stale snapshots
  fail validation instead of silently showing old traction.
- `gate.py`: config and section-8 evidence checks; missing inputs never imply PASS.
  Real mailbox authentication, DKIM coverage, remote expiry, provider checkout,
  hosted opt-out and Claude code review remain unverified.

Use `.runtime/sender/sender.sqlite` for local runtime data. Create its parent
directory explicitly; `Store` takes a path and does not guess an external location.
Construct `Engine(store, config, secret)` with a private >=32-byte HMAC secret.
Configuration keys are in `gate.validate` and the binding specification; the
fully fake fixture in `tests/support.py` uses reserved `.invalid` addresses and
must not be copied as real company identity. Configuration and tokens are not
printed or committed. No real business prospect list was imported.

API adapters supply raw inbound bytes to `Engine.receive`, confirmed orders to
`Store.paid`, and classified analytics events to `record_view`. A provider webhook
must already be authenticated before calling `paid`; implementing that checkout
integration belongs to TASK-007. An HMAC secret must persist privately so opt-out
links remain valid; no scheduled secret rotation or external persistence is claimed.

`Store.project_queue(private_root, at)` writes `sales/queue/` and the existing
`approvals/pending.md` format under a caller-selected private root, using the
Company OS writer lock. Database-generated queue IDs avoid email-controlled paths.
Owner replies require explicit `approved=True` on `queue_owner_reply`; tests alone
exercise this API, and it cannot bypass the offline transport guard. The default
operator projection should be under `.runtime/sender/`; no customer messages are
written to the public working tree during this task. `sales/queue`, suppression
CSV and company config are Git-ignored as an additional guard.

To export from an existing local database:

```powershell
python -m sender metrics --db .runtime/sender/sender.sqlite --output .runtime/sender/pipeline.json
python scripts/daily_report.py
```

No sample production database is created automatically. These commands do not
invent leads, views or sales. The snapshot is JSON so `n/a` survives the existing
numeric SQLite reporting schema without a migration.

## Remaining session work

Resolve the three failing test proposals through the DEC-008 implementation
workflow; do not silently change section 12. Then independently rerun the complete
suite and prepare the code handoff for Claude. At most two sessions remain. No
TASK-009 review or PASS is recorded yet. Live setup stays red independently of
local test success; TASK-005 and TASK-006 are not resumed by this work.

Timezone data comes from CPython's first-party `tzdata` 2026.4 wheel: only the
1,754-byte Chicago TZif and its licenses are vendored, not a Python dependency.
[Source hashes](data/SOURCE.json), [Python zoneinfo data/loading documentation](https://docs.python.org/3/library/zoneinfo.html).
