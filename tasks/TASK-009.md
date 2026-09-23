---
id: "TASK-009"
title: "Sender and inbox handler implementing sales/outreach.md (tests are the arbiter)"
owner: "codex"
status: "todo"
goal: "Implement the outreach scheduler, send transaction, suppression, opt-out endpoint, inbound classifier and owner queue exactly per sales/outreach.md sections 0-12, with automated tests that encode every fixture; disagreements with the spec are raised as failing tests plus a one-line proposal, not prose rounds"
evidence: "DEC-008; sales/outreach.md rev 2 + section 12 amendments; sales/outreach-review-round2.md (F1-F5, extra cases); sales/qa/task008-rev2-check.py"
definition_of_done: "sender/ package (Python stdlib + smtplib/imaplib; SQLite tables: prospects, sends, inbound, suppression, queue) with: scheduler (Chicago calendar, holidays, slots, day 0/3/8, expiry recheck), send transaction with intent rows and IMAP reconciliation, suppression with shared-domain rule, opt-out page GET/POST + RFC 8058 endpoint, classifier (header origin signals, quote stripping, A1 order), FAQ matcher, templates, owner queue writer, metrics exporter for daily_report; fake SMTP/IMAP in tests; no real credentials; go-live gate script (section 8) that prints each check"
success_metric: "All 20 section-9 fixtures (as amended by A1) plus the 7 extra cases in section 12 pass as automated tests; calendar tests for Tue/Wed/Thu starts and a holiday collision; opt-out POST test; SMTP-timeout-then-IMAP-found test; Claude PASS via --review after running the suite independently"
attempts: 0
review_round: 0
quota_budget: 60
created: "2026-09-23T08:20:00+00:00"
updated: "2026-09-23T08:20:00+00:00"
---
At most 3 sessions. Reviewer: claude. No real sending; the go-live gate stays red until
SETUP-EMAIL, SETUP-HOSTING, checkout and config are resolved by the owner.
If a spec rule cannot be implemented as written, write the failing test that shows why and
propose the smallest change in the test's docstring; do not open a review round on the spec.
