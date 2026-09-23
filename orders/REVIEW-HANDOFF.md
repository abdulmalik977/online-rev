# TASK-007 - round 2 code review handoff

Status: review for Claude's second and final decision. REV-012 is round-1 CHANGES.
Owner explicitly authorized its bounded correction after the two build sessions;
--attempt recorded attempts=3. review_round=1 counts completed decisions, so Claude
must record the next decision with --review TASK-007. Codex records no self-PASS.
TASK-009 remains done in REV-011; its counters are unchanged.

## REV-012 correction and fresh evidence

Applied task007-review1.diff with git apply and pushed commit 69f6a00 first.
The signed payment transaction checks the preview slug before order insertion.
A second charge records audit action duplicate_payment against the new order ID
and one durable owner_queue row, class refund, containing duplicate and original
order IDs. The existing private orders.md projects this owner refund queue.
Event replay returns the original order, without a second order/welcome or another
queue/audit entry. This queues owner refund work; it does not execute a refund.

Implementation is 15 added + 3 removed lines in orders/flow.py. One new regression:

```powershell
python -W error::ResourceWarning -m unittest orders.tests.test_flow.Flow.test_duplicate_payment_queues_refund_and_returns_existing_order -v
```

Before the fix it failed with sqlite3.IntegrityError: UNIQUE constraint failed:
orders.slug. After the fix it passes: two distinct order IDs on the same slug,
original return value, one order, one refund item with both IDs, audit of the new
ID and no duplicate welcome. It also retries the same event and a fresh event ID
for the same second charge. The existing conflict test now checks a real order-ID
conflict instead of expecting the old defect. Full fresh suites: orders 32/32,
sender 80/80, no skips/expected failures. Use the full-suite commands below.

The remaining sections retain session-2 evidence and its external launch limits;
visual/generator/operations results below were not rerun for this payment-only fix.

## Owner-visible change

Under the order button, the sales page now has exactly this linked sentence:

> Don't have a concept yet? Email {mailbox} with your business name and city and we'll build one

The mailbox comes from `support_email` in the one company configuration. The
sentence remains in both checkout states. It uses only mailto, with no sales-page
form, JavaScript, external form service or automatic email. The config example
still contains `support@example.invalid`; a real company config is absent, and
launch validation rejects the example. No working mailbox is invented.

## Inspect and reproduce

```powershell
python -W error::ResourceWarning -m unittest discover -s orders/tests -t . -v
python -W error::ResourceWarning -m unittest discover -s sender/tests -t . -v
python -W error::ResourceWarning -m unittest discover -s scripts -p 'test_*.py' -q
python -W error::ResourceWarning -m unittest discover -s generator -p 'test_*.py' -q
python scripts/watchdog.py --test
python -m orders.launch_gate
python -m orders.maintenance_trial --output .runtime/maintenance-review.json
python site/build.py --output .runtime/sales-review
python -m orders.demo --output .runtime/order-review
```

Use fresh build/demo paths. The gate must exit 2 and show all three A8 fixtures
GREEN while real launch remains RED. Results: orders 31/31, sender 80/80,
operations 18/18, generator 11/11, watchdog 7/7; no skips or expected failures.
Local mobile Lighthouse: 100 performance/accessibility/best-practices, LCP about
0.75 seconds. Twelve layout checks cover three pages at four viewport widths.
See `site/session-2-results.json` and `site/qa/session-2/`.

Review the signed payment, authenticated confirmation and immutable preview
expiry from session 1, then focus on:

- `orders/lifecycle.py`: verified corrections, subscription-month allowance,
  immutable customer revisions, explicit host artifact/receipt/time matching,
  period-end cancellation, export mail/removal, first-month refund, monthly
  reports, weekly exports retained 30 days and bounded tick.
- Durable effect keys, payload-conflict refusal, two-attempt bound, five-minute
  stale-intent recovery and lookup reconciliation after an unknown result.
  A late receipt uses the adapter's actual completion timestamp. A late launch
  still owes the first-month refund; a timely launch with a lost response does not.
- `Orders.wire_sender(engine)`: authoritative paid-ledger check in both sender
  transactions, idempotent suppression and refusal of queued sales replies after
  payment. Refund/unsubscribe service replies remain allowed. Startup wiring is
  mandatory; missing/broken ledger reads fail closed.
- `orders/http.py`: the separate customer-site enquiry handler, bound to loopback,
  one-hour HMAC tokens, strict origin/schema/size/header checks, five-second socket
  timeout, persistent limits and a private forwarding outbox. This is unrelated
  to concept requests on the sales page.
- File boundaries: safe slugs, receiver binding, escaped customer text, permitted
  local PNG with explicit consent, exact ZIP allowlist, no DB/drafts/secrets in
  public bundles, no recursive cleanup. Original previews retain original expiry.

## Adapter contracts and scheduling

All effect adapters must be offline in this implementation. `FakeAdapter` simulates
receipts; it never publishes, sends mail, charges, cancels a real subscription or
refunds money. `perform(key, kind, payload, at)` must be idempotent on `key`.
`lookup(key)` returns a receipt if accepted, None only for proven absence, and
raises if unknown/unavailable. A future provider adapter must satisfy this contract
and its native signature/settlement verification; an arbitrary SMTP Sent absence
is not proof of non-delivery. See A7. Do not simply set `offline=True` on a real client.

An effect still failed/unknown after the bound is surfaced in private orders.md
and tick results for explicit reconciliation. It is not silently called successful
or retried forever. Public configuration/evidence must not contain fake receipts.

Call `Orders.wire_sender(engine)` on every runtime startup before sender ticks.
Call the bounded lifecycle tick on the owner's existing scheduler; mail/refund/
removal/weekly export effects are idempotent. Monthly analytics has a separate
closed-Central-month method; absent visit data remains n/a. Public deployment,
trusted proxy/client-IP policy, HTTPS, actual delivery and scheduled execution
must be verified independently before changing any launch evidence.

## Acceptance boundary still open

The owner explicitly requested code review now. Public deployment and real-account
acceptance criteria are not fulfilled: company identity/mailbox/postal address,
eligible payment provider, actual native webhook, hosting/subdomain/DNS, SMTP,
external opt-out, provider receipt/cancellation links, scheduler and hosted mobile
performance are still unverified. No live URL or deployed customer is claimed.
These external gates remain RED, using existing SETUP-HOSTING/SETUP-EMAIL/
SETUP-CRON records; no new infrastructure task or TASK-006 session was created.

The maintenance trial completes 7/10 deliberately bounded fixture requests; three
require human review. It measures local processing of structured verified input,
not customer communication, rights checking, manual work or real deployment.
It does not establish 70% automation of overall maintenance labor.

Record the independent decision using `--review TASK-007` after reading/running the
code. Do not mark the entire commercial launch ready from these local results.
