# TASK-009: local sender and inbox implementation

DEC-008 implementation, session **2/3**, with owner-approved A7. Standard-library
Python 3.11+, private SQLite, fake SMTP/IMAP, and loopback HTTP tests. **All 74 tests
pass**, including the three unchanged reference assertions that failed in session 1.
TASK-009 is ready for Claude's independent code review; no PASS is claimed yet.

From the repository root:

```powershell
python -W error::ResourceWarning -m unittest discover -s sender/tests -t . -v
python -m unittest sender.tests.test_spec_conflicts -v
python -W error::ResourceWarning -m unittest discover -s scripts -p 'test_*.py' -q
python scripts/watchdog.py --test
# Prints every section-8 gate; exits 2 (RED), including disabled real sending.
python -m sender gate
```

[Session 2 results](session-2-results.json) record 74/74 sender tests, 18/18
operations tests and 7/7 watchdog rules, with no skips or expected failures.
[Session 1 results](session-1-results.json) preserve the original three failures.
A7 resolves them as follows:

- Absent/unavailable Sent lookup leaves unknown delivery held, even after 24 hours.
  IMAP proof or explicit owner reconciliation closes the unknown-send queue item;
  only a definite failure or owner failed decision permits the single retry.
- Every owner queue deadline starts at receipt, including non-customers. One
  Chicago business day preserves receipt wall time, skipping weekends and configured
  holidays; payment/confirmation remain unrelated to owner response deadlines.
- Missing Message-ID uses the receiver identity, optional provider UID and full
  canonical message bytes, including MIME content. No body-prefix fallback remains.

See [reference regressions](tests/test_spec_conflicts.py), [16 additional A7
checks](tests/test_a7.py), and [code review handoff](REVIEW-HANDOFF.md). The engine
continues to require offline transports; the CLI has no send/IMAP-connect command.

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

API adapters supply raw inbound bytes to
`Engine.receive(raw, received_at, mailbox_id="hello", provider_uid="INBOX:uidvalidity:uid")`,
confirmed orders to
`Store.paid`, and classified analytics events to `record_view`. A provider webhook
must already be authenticated before calling `paid`; implementing that checkout
integration belongs to TASK-007. An HMAC secret must persist privately so opt-out
links remain valid; no scheduled secret rotation or external persistence is claimed.

For messages without Message-ID, `mailbox_id` is required and must identify a
configured receiving account (local name or full address); do not infer it from
untrusted To headers. Supply a stable provider UID when available, namespaced by
folder and UIDVALIDITY for IMAP, consistently across repeated fetches. The fallback
is SHA-256 over compact JSON `[normalized_receiver, uid_or_null]`, NUL, and the
complete original message with CRLF/CR normalized to LF. Other bytes are preserved.
Existing Message-ID behavior is unchanged. No real inbox has been ingested; this
is not a migration of previously consumed production fallback IDs.

`Store.project_queue(private_root, at)` writes `sales/queue/` and the existing
`approvals/pending.md` format under a caller-selected private root, using the
Company OS writer lock. Database-generated queue IDs avoid email-controlled paths.
Owner replies require explicit `approved=True` on `queue_owner_reply`; tests alone
exercise this API, and it cannot bypass the offline transport guard. The default
operator projection should be under `.runtime/sender/`; no customer messages are
written to the public working tree during this task. `sales/queue`, suppression
CSV and company config are Git-ignored as an additional guard.

Unknown-send items use `Q-{prospect_id}-unknown-send`. Resolve through
`Engine.resolve_unknown_send(queue_id, at, "sent" or "failed", approved=True,
note="owner decision and evidence")`; the decision is audited and does not send.
A failed outcome permits the ordinary retry path only while its eligibility and
one-retry limit allow it. A second unknown outcome reopens the same queue ID with
its new receipt deadline. Queue projection reflects closure/reopening and includes
the deadline. Existing unresolved queue rows are redated from their original
receipt when the engine opens; reconciliation polling does not extend deadlines.

To export from an existing local database:

```powershell
python -m sender metrics --db .runtime/sender/sender.sqlite --output .runtime/sender/pipeline.json
python scripts/daily_report.py
```

No sample production database is created automatically. These commands do not
invent leads, views or sales. The snapshot is JSON so `n/a` survives the existing
numeric SQLite reporting schema without a migration.

## Review handoff and remaining session

Claude must independently run the suite and record its code decision through
`--review TASK-009`. The task is `review`, attempts 2, review_round 0. One session
remains for required review fixes. TASK-008 is closed; this opens no prose review.
Live setup remains red pending external evidence and code PASS. TASK-005 and
TASK-006 are not resumed by this work.

Timezone data comes from CPython's first-party `tzdata` 2026.4 wheel: only the
1,754-byte Chicago TZif and its licenses are vendored, not a Python dependency.
[Source hashes](data/SOURCE.json), [Python zoneinfo data/loading documentation](https://docs.python.org/3/library/zoneinfo.html).
