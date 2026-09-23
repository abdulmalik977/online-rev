# TASK-007 - sales page and order flow, session 1/2

The portable sales page and signed fake order flow are implemented. A8 fixtures
21-23 are green and run inside `orders.launch_gate`. TASK-009 is PASS in REV-011;
this work does not reopen its review or consume another TASK-009 attempt.

```powershell
python site/build.py --output .runtime/sales-public
python -m http.server 8777 --bind 127.0.0.1 --directory .runtime/sales-public
python -m orders.demo --output .runtime/order-demo
python -W error::ResourceWarning -m unittest orders.tests.test_flow -v
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

## Remaining session 2 work

The task remains doing (1/2 sessions), not ready for PASS. Session 2 must complete
and test the remaining local operational flow: applying confirmed corrections,
customer launch acknowledgement, cancellation/export and refund execution adapter
contracts, form HTTP validation/abuse controls and forwarding, and a timed bounded
maintenance trial. The current refund function reports eligibility only and the
form outbox does not deliver. Do not enable the public promises without these
behaviors and external launch evidence.

Provider eligibility, real signed-webhook mapping, verified customer confirmation
input, identity/domain/postal address, hosting/HTTPS, real SMTP, checkout, DNS and
scheduled expiry/export remain external dependencies. Re-run mobile performance
on the actual hosted URL, then request Claude's independent code review using the
existing protocol. No Claude decision or task completion is claimed here.
