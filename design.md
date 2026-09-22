# Company OS v0 — design before code
1. Limit this build to operating memory, seven deterministic watchdog rules, a daily report, and scheduled-run entry points.
2. Keep this workspace as the company-os repository root; use Python standard library, Markdown, SQLite, and cron only.
3. Preserve DEC-001 through DEC-006; product selection and market validation belong to Claude, not this implementation.
4. Challenge scope: outreach, customer delivery, product implementation, and mailbox provisioning are outside these two sessions.
5. Challenge missing inputs: Git remote, owner email, SMTP settings, Linux cron host, agent commands, and trustworthy quota metering.
6. Simpler storage: Markdown owns tasks and decisions; SQLite indexes tasks and stores run, review, lead, customer, and metric records.
7. Use a documented flat YAML subset with JSON-quoted scalars; reject malformed tasks rather than silently ignoring them.
8. Give each watchdog rule a pure predicate; persist blocked/killed transitions and deduplicated approvals with UTC timestamps.
9. Count todo, doing, review, and blocked as open; refuse creation of a sixth task through a transactional creation command.
10. Quota budgets use explicit daily execution credits; reserve a run's declared maximum before launch and stop at the 80% boundary.
11. Provider token quotas require a bounded metered adapter; do not claim that a generic CLI or timeout enforces provider consumption.
12. Generate nine ordered report sections within 30 lines; use Riyadh dates and authenticated SMTP for the authorized owner report only.
13. Supply cron configuration for two Claude runs, three Codex runs, watchdog every 30 minutes, and the owner report at 08:00.
14. Verify seven rule tests, persisted loop blocking, seed report, task capacity, quota boundaries, and safe runner failure behavior.
