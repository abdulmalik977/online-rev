# Private order flow - TASK-007

Standard-library Python and SQLite. Everything is local; there is no public
webhook/confirmation endpoint or live payment/refund/mail adapter in session 1.
Run `python -m orders.demo --output .runtime/order-demo` for a reproducible fake
payment -> confirmation -> promoted customer artifact. Read `site/README.md` for
current launch gates and the second-session work.

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
true. Nonempty corrections hold the order for actual implementation.

The later of payment and confirmation starts two and five Chicago business-day
deadlines, preserving wall time across DST and configured holidays. Repeated
confirmation cannot extend the deadlines. A local prepared folder never sets
`live_at`; it continues to qualify for overdue refund if it is not hosted. No
refund is executed or labelled paid by the eligibility query.

Promotion renders the purchased record/style with trusted local templates and
assets into `customers/<slug>/`: no concept banner, no noindex, no preview expiry
script. The source preview is retained with its unchanged original expiry; host
publication must keep customer and preview deployments separate so the preview
expiry job cannot delete a paid customer site. Existing different customer files
are never overwritten. Private `orders.md` and `welcome/*.txt` are recoverable
projections of SQLite. Welcome/DNS messages are drafts: exact DNS values are
supplied by the host later, never guessed, and existing email DNS must be retained.

## Enquiries and opt-out

Form backend choice: the local Python order service's private enquiry outbox,
forwarded through the existing email boundary after hosting and SMTP verification.
Session 1 validates/stores/deduplicates enquiries through `Orders.enquiry`; it
does not expose HTTP, limit public abuse or send mail. Customer HTML does not
enable a form until an HTTPS action and verified delivery are supplied. Those
settings are claims needing actual tests, not proof by themselves; the launch gate
also requires abuse-control and delivery evidence.

Reuse `sender.optout.local_server` for token GET/POST and RFC 8058 semantics; do
not duplicate suppression logic. The static `unsubscribe.html` is guidance, not
an unauthenticated email-address removal endpoint. Visiting it changes nothing.
Private suppression export uses the existing `Store.export_suppression` schema:

```csv
key,kind,reason,added_at,source_message_id
```

`kind` is email/domain; multiple reasons are semicolon-separated and earliest
timestamp is retained. No real suppression file or customer list is committed.
