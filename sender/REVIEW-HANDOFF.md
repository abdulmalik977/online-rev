# TASK-009 code review handoff - session 2/3

Reviewer: Claude. Status: review, attempts: 2, review_round: 0. This is an
implementation review under DEC-008; TASK-008 remains closed. Owner-approved A7
was applied and pushed in 89f4a64. One implementation session remains for fixes.

## Changes to assess

1. `engine.py`: unknown delivery never becomes failed just because Sent is absent
   or unavailable. The prospect remains held. The stable unknown-send owner item
   is closed by IMAP proof or explicit audited reconciliation; a failed decision
   permits the existing single retry, with suppression, payment, expiry and caps
   still enforced. A retry that becomes unknown reopens the same queue item.
2. `store.py`, `calendar.py`, `metrics.py`: receipt-based queue deadlines for all
   classes, legacy pending-row correction, Chicago business-day/DST handling,
   resolved/reopened queue projection and matching overdue identifiers.
3. `rules.py`, `Engine.receive`: missing-ID SHA-256 identity uses the configured
   receiver, provider UID when available and complete message bytes with line
   endings normalized. Original Message-ID dedup remains unchanged. Receiving
   account context is mandatory for the missing-ID path.
4. `transports.py`: explicit SMTP 4xx/5xx and connection refusal are definite
   failure; disconnected/ambiguous outcomes remain unknown. These adapters are
   still rejected by the offline engine. No provider connection was exercised.

## Reproduce independently

```powershell
python -W error::ResourceWarning -m unittest discover -s sender/tests -t . -v
python -m unittest sender.tests.test_spec_conflicts -v
python -W error::ResourceWarning -m unittest discover -s scripts -p 'test_*.py' -q
python scripts/watchdog.py --test
python -m sender gate
```

Observed: 74 sender tests pass, including all 20 fixtures, 7 extras, 3 original
reference regressions and 16 added A7 tests. Operations 18/18 and watchdog 7/7 pass.
No skip or expected-failure mechanism is used. The three reference assertions are
retained; their missing-ID calls now supply the required receiver context.
`gate` must exit 2 and print RED: local success is not launch authorization.

Record the independent code decision using `--review TASK-009` after inspection
and execution. No review decision or PASS has been recorded by Codex. If a new
rule cannot be implemented literally, encode its failure and minimal proposed
amendment in a test docstring, following the owner's existing instruction.

## Boundaries for the reviewer

The old failing run remains in session-1-results.json; session-2-results.json is
the new result. All mailbox/provider behavior is simulated; no real prospects,
credentials, messages, spend, deployment or provider integrations were used.
Production authentication, hosted opt-out/expiry, checkout, owner config and code
PASS remain launch gates. TASK-005 and TASK-006 remain deferred/blocked.
