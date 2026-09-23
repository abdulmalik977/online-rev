# Private order flow - TASK-007

Standard-library Python and SQLite. The final local implementation is ready for
Claude's code review. All provider, hosting and mail effects use offline adapters;
no real external operation is enabled. Customer enquiry HTTP binds to loopback.
The sales-page concept request is a mailto link and has no form or new service.

Run `python -m orders.demo --output .runtime/order-demo --lifecycle` for a synthetic
payment -> confirmation -> launch -> maintenance -> cancellation/export simulation.
The demo's receipts are fake and cannot be used as production launch evidence.
See `REVIEW-HANDOFF.md` for independent review commands and acceptance limits.

## Normalized initial-payment contract

An eventual provider adapter must first verify that provider's native signature,
event type, settled payment, amount/currency and trusted checkout metadata. Only
then may it call the internal normalized interface. Never sign arbitrary browser
JSON or treat this HMAC scheme as a provider's native signature protocol.

```json
{
  "event_id": "provider-event-id",
  "type": "order.paid",
  "order_id": "stable-initial-order-id",
  "email": "buyer@example.invalid",
  "preview_slug": "registered-preview-slug",
  "plan": "website-monthly-119",
  "amount_minor": 11900,
  "currency": "USD",
  "paid_at": "2026-09-23T14:00:00+00:00"
}
```

Signature: lowercase HMAC-SHA256 with a private >=32-byte secret, over ASCII Unix
seconds, a literal period, then the exact UTF-8 payload bytes. Timestamp tolerance
is five minutes relative to receipt. A provider retry needs a fresh signature,
while its stable event ID and original body remain unchanged. Body limit: 16 KiB.
Signature is checked before parsing/writing. A reused event ID with changed body
is rejected; duplicate original payment has no second provisioning effect. Plan,
amount, currency, IDs, registered email/preview and payment-time expiry are checked.
Renewals, cancellations and refunds are not accepted as `order.paid` events.

The preview is registered from the generator's private `records.json` and original
expiry before checkout. An expired preview cannot be re-registered with a new age.
One initial order may own each preview. Payment must precede its original expiry;
a delayed authentic event for an already-paid valid preview can arrive later.

## Operator/API boundary

The CLI reads a secret from the process environment, not arguments or tracked
configuration. Example operations (all paths private):

```powershell
python -m orders --root .runtime/orders --config company/config.json register --bundle .runtime/preview-build --slug REGISTERED-SLUG --email CUSTOMER-EMAIL
python -m orders --root .runtime/orders --config company/config.json payment --payload .runtime/event.json --headers .runtime/event-headers.json
python -m orders --root .runtime/orders --config company/config.json project
python -m orders --root .runtime/orders --config company/config.json promote --order ORDER-ID
python -m orders --root .runtime/orders --config company/config.json refund-candidates
```

Headers JSON has integer `timestamp` and hex `signature`. CLI output omits message
content and customer email. `Orders.confirm(..., verified=True)` is a trusted
operator/authenticated-inbox API; that boolean must never be mapped directly from
an unauthenticated HTTP request. Confirmation must match the registered customer
and explicitly provide domain choice, corrections and media permission. No
customer-supplied media is used by the current renderer, even when permission is
true. Nonempty corrections hold the order until a verified `apply_change(..., correction=True)` implements the structured customer request.

The later of payment and confirmation starts two and five Chicago business-day
deadlines, preserving wall time across DST and configured holidays. Repeated
confirmation cannot extend the deadlines. A local prepared folder never sets
`live_at`; it continues to qualify for overdue refund if it is not hosted. The eligibility query itself executes nothing. `refund_overdue` runs the idempotent simulated refund adapter; a late launch still owes the first-month refund.

Promotion renders the purchased record/style with trusted local templates and
assets into `customers/<slug>/`: no concept banner, no noindex, no preview expiry
script. The source preview is retained with its unchanged original expiry; host
publication must keep customer and preview deployments separate so the preview
expiry job cannot delete a paid customer site. Existing different customer files
are never overwritten. Each confirmed change gets a new immutable revision folder;
the launch receipt must match its exact allowlisted artifact digest. Private `orders.md` and `welcome/*.txt` are recoverable
projections of SQLite. Welcome/DNS messages are drafts: exact DNS values are
supplied by the host later, never guessed, and existing email DNS must be retained.

## Final local operations

- `apply_change`: requires a verified customer request, <=30 minutes and at most
  five maintenance requests per subscription month. Structured text, hours, phone,
  service additions/removals, prices and a permitted local PNG are automated.
  Unstructured instructions, other image formats or missing rights need human
  handling. Launch corrections do not consume the monthly maintenance allowance.
- `launch`: validates the prepared artifact, host HTTPS/200 proof and actual
  completion time. Fake receipts set simulated live state only. Lost responses
  reconcile by stable effect key without a blind repeat.
- `set_period_end` and `cancel`: require authenticated provider/customer evidence.
  Cancellation fixes the provider-confirmed paid-period end. `finish_cancel`
  exports the allowlisted ZIP, delivers it through the simulated mail adapter and
  removes the site through the simulated host adapter at/after that end. Early
  cancellation cannot bypass launch confirmation, but still receives an export.
- `weekly_exports`: exports no more often than weekly, retaining weekly copies for
  30 days. Deletes only known files after verifying they resolve under the private
  root. ZIPs include no databases, drafts, customer ledgers or credentials.
- `send_welcome`, `forward_enquiries`, `monthly_report`: durable mail effects with
  idempotent IDs. Internal draft annotations never enter the mail body. Monthly
  reports use a closed Central month and retain n/a when analytics are absent.
- `tick`: bounded invocation for pending paid projections, launch reconciliation,
  refunds, enquiries, due cancellations and exports. Unresolved effects and overdue
  updates are returned and surfaced in private orders.md. Existing SETUP-CRON must
  supply real scheduling; no desktop timer or external cron was installed.

Effects have at most two dispatch attempts. A fresh inflight effect is held for
five minutes; stale/unknown effects require lookup. Lookup None must mean proven
absence; unavailable lookup raises and holds. After the bound, explicit operator
reconciliation is required. Real adapters must implement native authentication,
proof and idempotency before an independently reviewed activation change.

`Orders.wire_sender(engine)` is required on each startup. It checks the authoritative
paid ledger in both sender transactions, suppresses a paid prospect idempotently
and closes the cross-database crash window. Queued ORDER/NO_CALL_ORDER replies are
cancelled after payment; refund acknowledgements remain available. Do not run the
sender without the wiring. The new launch gate requires its verification.

## Enquiries and opt-out

Form backend: the local Python order service, no external form provider. Start
`orders.http.local_server(store)` in the deployment adapter after creating its
private order store. The current helper is loopback-only and opens a dedicated
SQLite connection per request. Customer contact links open this separate page;
the sales landing page still contains no form.

GET issues a one-hour HMAC token. POST enforces exact Origin, receiver slug,
strict form fields, 8 KiB body limit, five-second read timeout, no header injection,
and persistent per-IP/per-site limits. SQLite stores only an HMAC of the IP for
rate limits. A repeated form ID cannot enqueue or forward twice. Forwarding uses
the private outbox and an offline mail adapter in tests. The public reverse proxy,
trusted client-IP handling, TLS and actual delivery remain unverified launch gates.

Reuse `sender.optout.local_server` for token GET/POST and RFC 8058 semantics;
do not duplicate suppression logic. The static `unsubscribe.html` is guidance,
not an unauthenticated email-address removal endpoint. Visiting it changes nothing.
Private `Store.export_suppression` CSV columns remain:

```csv
key,kind,reason,added_at,source_message_id
```

`kind` is email/domain; multiple reasons are semicolon-separated and earliest
timestamp is retained. No real suppression file or customer list is committed.
