# TASK-007 - sales page and order flow, session 2/2 - ready for code review

The portable sales page and local order lifecycle are implemented and submitted to Claude for code review, as requested by the owner. A8 fixtures
21-23 are green and run inside `orders.launch_gate`. TASK-009 is PASS in REV-011;
this work does not reopen its review or consume another TASK-009 attempt.

```powershell
python site/build.py --output .runtime/sales-public
python -m http.server 8777 --bind 127.0.0.1 --directory .runtime/sales-public
python -m orders.demo --output .runtime/order-demo --lifecycle
python -W error::ResourceWarning -m unittest discover -s orders/tests -t . -v
python -W error::ResourceWarning -m unittest discover -s sender/tests -t . -v
python -m orders.launch_gate
```

Choose fresh build/demo directories. The demo uses a synthetic business and
`.invalid` email, signs a fake initial payment, records authenticated fixture
confirmation and prepares a local customer site. It takes no payment, sends no
email and deploys nothing. `result.json` points to the preview and customer page.

## Public page and configuration

`template.html` follows offer rev2: $119/month, no setup fee, five small updates
of at most 30 minutes, two-business-day delivery, exact later(payment,
confirmation) launch/refund clock, cancellation/export terms, exclusions and FAQ.
Original CSS artwork, system fonts, no JS/fonts/images loaded externally. Privacy
and email-preferences pages are included. Missing identity remains visibly a
placeholder, not an invented company/address. Checkout is disabled by default.

Direct visitors can now use the exact concept-request sentence below the order
button as a mailto link. It reads `support_email` from the same configuration and
remains visible when checkout is enabled. No sales-page form, service integration
or automatic email was added. The example mailbox is reserved `.invalid`; the
owner's real mailbox is still required before public launch.

For real setup, merge the keys from `company/web-config.example.json` into the
single ignored `company/config.json`, alongside sender configuration. Do not
create another independent company identity file. Use `--config company/config.json`.
The builder renders only selected public fields; webhook secrets and mailbox
settings are never part of the output. The example is not production configuration.

Checkout also requires separate verification evidence: accepted provider/product,
commercial hosting, checkout HTTP 200, signed preview/order metadata and verified
order flow. An HTTPS string alone does not enable the button. The generic checkout
must let a buyer choose or retain their registered preview; the production adapter
must map provider metadata to the signed order schema, not trust a browser's paid
flag. No provider is selected or integrated yet.

## Publication boundary

Offer rev2 overrides the old TASK-007 GitHub Pages wording. GitHub Pages does not
permit this commercial sales use, rechecked 2026-09-23 against its
[official limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
Use the existing commercial-host path from `generator/hosting-handoff.md`.
Only upload the five files emitted by this builder. Never publish the repo root,
`orders/`, runtime database, drafts, fixtures, source config or test reports.

No new TASK-006 session is started. Existing SETUP-HOSTING/SETUP-CRON inputs remain
unresolved. No hosted URL or hosted performance result is claimed.

## A8 and the gate

`sender/tests/test_a8.py` tests Stop!/STOP. punctuation, the accepted Sue -> LEGAL
false positive, post-start invalid configuration, queued service replies and edits
between the durable intent and SMTP transaction. `sender.gate` now requires
`a8_21`, `a8_22`, `a8_23` as part of section 8.5. `orders.launch_gate` executes the
six A8 tests itself; supplied evidence cannot override a failure. All external
launch conditions and real sending remain RED. Exit code is 2 until all pass.

## Session 2 result and review boundary

TASK-007 is review at attempts 2/2, review_round 0. No self-PASS. See
`orders/REVIEW-HANDOFF.md` and `site/session-2-results.json` for review commands,
receipts, tests, scope and remaining external acceptance gaps.

Orders: 31 tests; sender: 80; operations: 18; generator: 11; watchdog: 7, all pass.
Twelve layout checks pass, including mailto visibility and absence of sales-page
forms. Local simulated-mobile Lighthouse performance/accessibility/best-practices
are 100 with LCP around 0.75 seconds; the actual hosted URL remains unmeasured.

Local paths now cover authenticated corrections and bounded maintenance,
versioned customer files, launch receipts, paid-to-sender crash recovery,
period-end cancellation/export, idempotent simulated refunds, enquiry forwarding,
weekly export retention and monthly reports with missing analytics as n/a.
Customer enquiries use a separate loopback-only HTTP handler; concept requests
remain mailto. The maintenance trial processes 7/10 bounded fixture requests,
with three requiring human review; it does not prove 70% real-world labor savings.

The owner requested code review now. Deployment and real-account requirements in
the definition of done remain open: provider eligibility/native webhook, identity
and real mailbox, public hosting/HTTPS/DNS, external SMTP/opt-out, receipt links,
scheduler, delivery and hosted performance. The existing setup records remain
unresolved. No live URL, real payment, email, refund or provider operation occurred.
The combined gate remains RED/exit 2 and refuses non-offline effect adapters.
