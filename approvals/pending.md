# Pending owner approvals / missing inputs

Each entry is one line: `- [ ] ID | UTC timestamp | description`.
Resolve by moving the entire entry to done.md and changing `[ ]` to `[x]`.
Keep the original timestamp; watchdog deduplicates against both files.
- [ ] LOOP-TASK-LOOP | 2026-09-22T06:19:09+00:00 | TASK-LOOP: review_round > 2; resolve loop
- [ ] SETUP-EMAIL | 2026-09-22T06:26:40+00:00 | Provide owner email and private SMTP configuration; no mail sent
- [ ] SETUP-CRON | 2026-09-22T06:26:40+00:00 | Specify Linux cron host and deployment path; schedule not installed
- [ ] SETUP-QUOTA | 2026-09-22T06:26:40+00:00 | Provide provider quota mapping and hard-capped agent adapters before live runs
