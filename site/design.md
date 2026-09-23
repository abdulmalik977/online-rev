# TASK-007 design before code - session 1 of at most 2

1. Follow approved offer rev2, DEC-008 and A8. TASK-009 stays PASS; A8 work belongs to TASK-007.
2. Build a fast English mobile sales page for Houston trade owners: clear $119/month offer, scope, exact launch/refund clock, cancellation and FAQ; no invented customers or claims.
3. Use static HTML/CSS, system fonts and original CSS illustration; no frameworks, external images, cookies or tracking scripts.
4. Read company identity, postal address, contact and provider URLs from one private company/config.json; a committed example has explicit placeholders and checkout disabled.
5. Keep checkout visibly unavailable until both complete configuration and verified launch evidence exist; no payment/signup or reply-to-order workaround.
6. Offer rev2 overrides TASK-007's old GitHub Pages wording. Prepare a narrow public bundle for the existing commercial-host choice; no repository-root deployment.
7. Store order/customer/event state in a private SQLite database; orders.md and welcome messages are private projections, never public build assets.
8. Use a provider-neutral initial-payment event with timestamped HMAC over raw bytes, replay bounds, stable event/order IDs, amount/currency/plan validation and idempotency. Real providers require their own verified adapter later.
9. Register an existing unexpired generated preview and its intended customer's email before accepting payment; reject forged paths, mismatched customers, expired/unknown previews and duplicate ownership.
10. Payment creates an awaiting-confirmation order and a welcome draft. Explicit authenticated confirmation supplies domain choice, corrections and media consent. The later timestamp starts the two/five Chicago business-day clocks.
11. Promote locally only after payment and confirmation, by rendering the purchased preview's factual record/style into a customer template without concept banner/noindex/expiry controls. Stage an immutable public bundle; local promotion is not hosted publication.
12. Keep live confirmation, DNS values, refunds and welcome delivery explicit: no fabricated live URL, DNS records, refund or sent email. Produce actionable private drafts and overdue refund eligibility.
13. Reuse sender opt-out handler and suppression CSV contract. Choose the local Python form inbox/outbox boundary; external HTTPS/SMTP activation stays a separate red launch gate.
14. Implement A8 punctuation-normalized whole-body matches, preserve Sue -> LEGAL, revalidate config in both send transactions, and require fixtures 21-23 at the launch gate.
15. Test signed fake payment through local promotion plus refusal/replay/confirmation/clock cases, run sender and existing regressions, and inspect mobile layout. Record actual performance only; leave external deployment and provider claims unverified.

Scope challenge: GitHub Pages is ineligible for this sales site, as reconfirmed
2026-09-23 against its official limits. Hosting access and payment-provider eligibility
are still external dependencies. This session can finish the portable page and fake
order flow; it cannot honestly demonstrate a hosted launch, live payment, delivery
or a real refund without those inputs. No new infrastructure task is created.

Source: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits


## Session 2 plan (before code; final implementation session)

Use support_email from the one company config for the exact owner-requested
concept-request mailto line below checkout; keep it in both checkout states and
add no sales-page form, script or external service. The example remains explicitly
reserved .invalid until the owner supplies real identity.

Complete the local lifecycle with verified correction/maintenance changes,
versioned customer artifacts, explicit launch receipts, cancellation at the
provider-confirmed paid-period end, allowlisted ZIP exports, weekly retention,
and refund eligibility even after a late launch. Durable effect IDs and lookup
reconciliation protect simulated refunds, mail and removal from duplicate effects.
External adapters stay offline-only; missing external accounts remain RED.

Bridge paid orders idempotently to sender suppression before any subsequent send.
Customer enquiry HTTP is loopback-only (separate from the sales-page mailto), with
strict size/schema/origin checks, persistent rate limits and a private mail outbox.
Test these operational paths with fakes, crash/timeout replay and a bounded timed
maintenance mix. Recheck mobile layout, mailto and Lighthouse; document actual
limits, preserve session-1 evidence, and submit status=review at attempts=2,
review_round=0 for Claude. No self-review, real email/payment or new infrastructure.


## REV-012 bounded correction (before code)

The owner explicitly authorizes this correction after the two build sessions.
Keep the existing signed-event validation and immediate transaction. Before a new
order insert, find an order for the preview slug. For a second payment, atomically
record duplicate_payment against its new order ID and one durable owner_queue row
of class refund containing both order IDs. Project that queue into the existing
private orders.md. Map the event to the original order and return it, including on
replay, so a provider adapter can acknowledge success without a second order.
One regression test must first reproduce the UNIQUE failure, then verify the
original return value, one order, one refund item, audit identity and replay.
Limit implementation to <=30 changed lines plus one new test; no provider effect.
