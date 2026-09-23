---
id: "TASK-009"
title: "Sender and inbox handler implementing sales/outreach.md (tests are the arbiter)"
owner: "codex"
status: "done"
goal: "Implement the outreach scheduler, send transaction, suppression, opt-out endpoint, inbound classifier and owner queue exactly per sales/outreach.md sections 0-12, with automated tests that encode every fixture; disagreements with the spec are raised as failing tests plus a one-line proposal, not prose rounds"
evidence: "Owner-approved A7 commit 89f4a64; sender/session-2-results.json; sender/REVIEW-HANDOFF.md; all 74 sender tests pass including the 3 reference regressions, 20 fixtures and 7 extra cases; operations 18/18 and watchdog 7/7; Claude PASS REV-011 at d103ef3; A8 follow-up is tracked in TASK-007; no live sending"
definition_of_done: "sender/ package (Python stdlib + smtplib/imaplib; SQLite tables: prospects, sends, inbound, suppression, queue) with: scheduler (Chicago calendar, holidays, slots, day 0/3/8, expiry recheck), send transaction with intent rows and IMAP reconciliation, suppression with shared-domain rule, opt-out page GET/POST + RFC 8058 endpoint, classifier (header origin signals, quote stripping, A1 order), FAQ matcher, templates, owner queue writer, metrics exporter for daily_report; fake SMTP/IMAP in tests; no real credentials; go-live gate script (section 8) that prints each check"
success_metric: "All 20 section-9 fixtures (as amended by A1) plus the 7 extra cases in section 12 pass as automated tests; calendar tests for Tue/Wed/Thu starts and a holiday collision; opt-out POST test; SMTP-timeout-then-IMAP-found test; Claude PASS via --review after running the suite independently"
attempts: 2
review_round: 1
quota_budget: 60
created: "2026-09-23T08:20:00+00:00"
updated: "2026-09-23T14:17:13+00:00"
---
At most 3 sessions. Reviewer: claude. No real sending; the go-live gate stays red until
SETUP-EMAIL, SETUP-HOSTING, checkout and config are resolved by the owner.
If a spec rule cannot be implemented as written, write the failing test that shows why and
propose the smallest change in the test's docstring; do not open a review round on the spec.

## Session 1 result (1/3)
Implemented sender/ with private SQLite, pure classifier and amended templates, Chicago/DST scheduling, immutable expiry/new-batch regeneration boundary, durable send intents/retry/IMAP reconciliation, suppression, loopback opt-out HTTP, owner queue projection, closed-Central-day metrics and a red launch gate. SMTP/IMAP are injected fakes; real adapters are rejected by the engine and no real send command exists.

All 20 amended section-9 cases and the 7 extra cases pass. Full sender suite: 58 tests, 55 pass, 3 fail (no skips or expectedFailure). The failing tests reproduce literal A4/A6 outcomes: accepted SMTP with no Sent copy can be resent; a non-customer legal escalation has no payment-based deadline; first-512-byte missing-ID dedup can discard a distinct opt-out. Each test docstring contains the smallest proposed change. No new review round on sales/outreach.md and no silent amendment.

Existing operations tests 18/18 and watchdog rules 7/7 pass. Old operations fixtures were isolated from later real task closures/review IDs. Daily report now consumes an optional private sender snapshot and preserves n/a for absent analytics; no production snapshot or real metrics were fabricated. See sender/session-1-results.json and sender/README.md for commands.

Status remains doing, not ready for Claude PASS while the complete suite is red. Two sessions remain to resolve executable conflicts and prepare the independent code review. No TASK-005 work, TASK-006 retry, credentials, spending, account connections or outreach.

## Session 2 result (2/3; supersedes session 1 status)
Applied a7-amendment.diff with git apply and pushed commit 89f4a64 before implementation. Recorded --attempt TASK-009 once for session 2 and extended sender/design.md before code changes. All three owner-approved A7 proposals are implemented: unknown SMTP outcomes remain held until proof or explicit audited owner reconciliation; owner queue clocks use original receipt; missing-ID dedup hashes receiver/provider identity and the full canonical message.

The original three reference assertions now pass without weakening, skipping or expectedFailure. Full sender suite: 74/74, including all 20 section-9 fixtures, 7 extra cases and 16 new A7 checks. Regression operations: 18/18; watchdog: 7/7. Tests cover absent/unavailable Sent after days, late proof, explicit reconciliation, retry ceiling, reopening queue projection, receipt clock across holidays/DST, legacy pending deadlines and complete MIME identity. See sender/session-2-results.json and sender/REVIEW-HANDOFF.md.

Status is review for Claude's independent code decision via --review TASK-009; review_round stays 0 until that decision. One session remains for review fixes. No self-review or PASS. Launch gate remains RED; no accounts, real sending, deployment, TASK-005 collection or TASK-006 attempt.

## Review outcome
Claude independently passed round 1 in REV-011; task is done. Owner directed the three A8 fixtures into TASK-007. The session-2 review handoff above is historical, not an outstanding TASK-009 review.
