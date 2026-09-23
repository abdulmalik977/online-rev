---
id: "TASK-009"
title: "Sender and inbox handler implementing sales/outreach.md (tests are the arbiter)"
owner: "codex"
status: "doing"
goal: "Implement the outreach scheduler, send transaction, suppression, opt-out endpoint, inbound classifier and owner queue exactly per sales/outreach.md sections 0-12, with automated tests that encode every fixture; disagreements with the spec are raised as failing tests plus a one-line proposal, not prose rounds"
evidence: "DEC-008 commit 463ff83; sender/design.md; sender/README.md; sender/session-1-results.json; 20 amended fixtures + 7 extra cases pass; total 55 passing / 3 failing specification tests, proposals in sender/tests/test_spec_conflicts.py; no live sending"
definition_of_done: "sender/ package (Python stdlib + smtplib/imaplib; SQLite tables: prospects, sends, inbound, suppression, queue) with: scheduler (Chicago calendar, holidays, slots, day 0/3/8, expiry recheck), send transaction with intent rows and IMAP reconciliation, suppression with shared-domain rule, opt-out page GET/POST + RFC 8058 endpoint, classifier (header origin signals, quote stripping, A1 order), FAQ matcher, templates, owner queue writer, metrics exporter for daily_report; fake SMTP/IMAP in tests; no real credentials; go-live gate script (section 8) that prints each check"
success_metric: "All 20 section-9 fixtures (as amended by A1) plus the 7 extra cases in section 12 pass as automated tests; calendar tests for Tue/Wed/Thu starts and a holiday collision; opt-out POST test; SMTP-timeout-then-IMAP-found test; Claude PASS via --review after running the suite independently"
attempts: 1
review_round: 0
quota_budget: 60
created: "2026-09-23T08:20:00+00:00"
updated: "2026-09-23T09:12:08+00:00"
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
