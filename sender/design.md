# TASK-009 design before code (session 1 of at most 3)

1. Implement DEC-008: outreach sections 0-12, with A1-A6 overriding earlier rules; no new text review.
2. Standard-library Python package; private SQLite under ignored .runtime, no credentials or real sending.
3. Keep prospects, sends, inbound, suppression and queue in one transactional store; record additional orders/mailbox events for metrics and pauses.
4. Parse RFC email using email.parser; deduplicate before side effects and correlate DSNs before unknown-sender handling.
5. Pure classifier extracts authored text, applies A1 spans/negation, then A2 terminal state/reply precedence and A5 origin/suppression headers.
6. Store suppression reasons as a set per key, retaining earliest timestamp; produce a private CSV projection compatible with the specified columns.
7. Use America/Chicago via zoneinfo, including DST; Windows needs a pinned TZif data fallback, not a hand-coded fixed offset.
8. Scheduler supports 0/3/8 calendar offsets, holidays, immutable generated expiry, and actual send-time checks; stale batches require regeneration/removal evidence.
9. Write durable sending intents before invoking an injected transport; stable Message-ID, one retry, holds on unknown outcomes and IMAP reconciliation.
10. Production SMTP/IMAP interfaces stay disabled in this task; fake transports exercise success, definitive failure, timeout and process-loss recovery.
11. Local opt-out HTTP GET shows a button; authenticated opaque-token POST is idempotent, cookie-free and never sends mail.
12. Render fixed templates with validated placeholders/headers; keep outreach and service eligibility separate while applying common caps and reply priority.
13. Persist/deduplicate owner queue first, project sanitized Markdown to the existing queue/approvals paths, and export closed-Central-day metrics without turning missing views into zero.
14. A read-only go-live command prints every gate and remains red without real external evidence and review; no send command is exposed.
15. Encode all twenty amended cases plus seven extras and calendar/failure tests. A rule that cannot be honored gets a failing test with the smallest proposal in its docstring; do not silently amend it or hide a failure as a pass.

## Session 2 plan (before edits; A7 approved)
Keep unknown SMTP outcomes held indefinitely when Sent lookup is absent/unavailable. Create the stable Q-{prospect_id}-unknown-send owner item, allow explicit audited sent/failed reconciliation only, and close it when IMAP proves acceptance. Preserve the single retry limit, suppression, expiry and caps. Start every owner queue deadline at its original receipt time, including pending rows from session 1. Replace prefix hashing with a JSON-framed mailbox/provider-UID identity plus the complete message with normalized line endings; require receiver mailbox context for missing Message-ID. Keep all three reference assertions and add tests for late reconciliation, retries, queue projection, holidays, full MIME content and receiver identity. Run the complete suite and prepare Claude code-review handoff; no live send capability or new prose review.
