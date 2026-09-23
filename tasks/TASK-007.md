---
id: "TASK-007"
title: "Landing page and order flow (checkout provider pluggable)"
owner: "codex"
status: "review"
goal: "One-page site that sells the offer in company/offer.md sections 3-5 and a post-payment flow that promotes a preview to a live customer site, with the payment provider behind a single URL and webhook so an eligible owner-selected provider can be plugged in later"
evidence: "site/session-2-results.json; orders/REVIEW-HANDOFF.md; requested concept mailto; orders 31/31, sender 80/80, operations 18/18, generator 11/11, watchdog 7/7; local mobile Lighthouse 100; lifecycle and 7/10 bounded maintenance trial; external launch gates RED; owner-directed code review, no live deployment or self-PASS"
definition_of_done: "site/ with the landing page (headline, what is included, price, terms, refund rule, FAQ, physical address placeholder, privacy page); deployed on an eligible commercial host per approved offer rev2 (supersedes GitHub Pages); orders/ script that takes a webhook payload (provider-agnostic JSON: email, preview slug, plan) and promotes the preview (removes banner/noindex, records the order in db + orders.md); welcome email template with DNS instructions; unsubscribe/opt-out page and suppression list file format for TASK-008"
success_metric: "Landing page loads under 1 s on mobile (Lighthouse >= 90 performance); fake-webhook test promotes a preview end to end; Claude PASS via --review"
attempts: 2
review_round: 0
quota_budget: 40
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-23T15:29:59+00:00"
---
Starts after TASK-006 v1 exists (needs a preview to promote). At most 2 sessions.
Reviewer: claude. Company name, domain and postal address are owner inputs: use placeholders
read from one config file so they are changed in one place. No payment provider signup here.

## Session 1 result (1/2)
User-directed start after TASK-009 PASS (REV-011, patch commit 3123819). Recorded --attempt TASK-007 once; site/design.md precedes code. Offer rev2 hosting/payment rules override this task's original GitHub Pages/Paddle assumptions; no new infrastructure task or TASK-006 attempt.

Built the mobile sales page, price/scope/terms/FAQ, privacy and email-preferences pages from one config; public build is five allowlisted files with disabled checkout until evidence exists. Signed provider-neutral initial payment checks identity, plan/amount/currency, expiry, timestamp and idempotency. Customer confirmation starts the two/five Chicago business-day clocks; unresolved corrections hold promotion. Fake end-to-end promotion renders a separate customer artifact without the concept banner/noindex, retains source preview expiry, and writes private orders.md and unsent welcome/DNS drafts. Local preparation never records a hosted launch or executed refund.

A8 is implemented here: punctuation-normalized whole-body matching, Sue -> LEGAL, and validation in both send transactions. Six A8 tests pass, including the three fixtures, service replies, mid-transaction mutation and gate enforcement. orders.launch_gate executes A8 rather than accepting supplied PASS flags. Gate remains RED/exit 2.

Verification: sender 80/80, orders 12/12, operations 18/18, generator 11/11, watchdog 7/7. Mobile/desktop layout 12/12 at 320/390/430/1440. Local Lighthouse mobile: performance/accessibility/best-practices 100, LCP below one second; hosted performance is unverified. Details and hashes in site/session-1-results.json.

One session remains. Finish local correction/launch/cancellation/refund/form-forwarding contracts, paid-to-sender integration and bounded maintenance trial; then verify available external inputs and prepare independent Claude code review. No live payment, sending, deployment or TASK-005 collection. Status remains doing; no self-PASS or review round consumed.

## Session 2 result (2/2; submitted to review at owner request)
Added the exact requested concept-request sentence as mailto below checkout, using support_email from the one company config. It remains visible in both checkout states. No sales-page form, external form service or automatic email; the real mailbox is still an owner input.

Completed local correction/maintenance, versioned artifacts, verified simulated launch receipts, first-month refund even after late launch, receipt-time reconciliation, period-end cancellation/export, weekly 30-day exports, welcome/enquiry forwarding and monthly reporting. Added the authoritative paid-ledger guard in both sender transactions, including cross-database crash recovery and cancellation of queued sales replies. The separate customer-site HTTP enquiry handler is loopback-only with signed expiring tokens, strict schema/origin/size checks, persistent limits and bounded reads. All external effects remain offline-only simulations.

Validation: orders 31/31; sender 80/80; operations 18/18; generator 11/11; watchdog 7/7; no skips/expected failures. Layout 12/12, mailto visible on mobile, no sales forms. Local Lighthouse performance/accessibility/best-practices 100, LCP about 0.75 seconds. Bounded maintenance trial: 7/10 automated, 3 manual-review cases; this excludes human verification/support/network work and does not establish 70% overall labor automation.

Status review, attempts 2/2 and review_round 0. Reviewer handoff: orders/REVIEW-HANDOFF.md. Claude must independently inspect/run and record the decision; no self-PASS. The owner requested submission now; public deployment and real-provider acceptance criteria remain unmet/unverified and the combined gate remains RED/exit 2. Existing identity, email, hosting, provider and scheduler inputs remain necessary. No real payment, email, refund, deployment, TASK-005 work or TASK-006 attempt. No further implementation session starts automatically.
