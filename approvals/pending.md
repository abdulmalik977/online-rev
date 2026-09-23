# Pending owner approvals / missing inputs

Each entry is one line: `- [ ] ID | UTC timestamp | description`.
Resolve by moving the entire entry to done.md and changing `[ ]` to `[x]`.
Keep the original timestamp; watchdog deduplicates against both files.
- [ ] LOOP-TASK-LOOP | 2026-09-22T06:19:09+00:00 | TASK-LOOP: review_round > 2; resolve loop
- [ ] SETUP-EMAIL | 2026-09-22T06:26:40+00:00 | Provide owner email and private SMTP configuration; no mail sent
- [ ] SETUP-CRON | 2026-09-22T06:26:40+00:00 | Specify Linux cron host and deployment path; schedule not installed
- [ ] SETUP-HOSTING | 2026-09-23T05:55:18+00:00 | TASK-006 blocked at session 3/3: configure owner-controlled Netlify Free access locally (NETLIFY_AUTH_TOKEN or CLI login; never paste secrets), or provide eligible Cloudflare access; resolve session budget before further work. Publishing already authorized. Expiry execution also needs the existing SETUP-CRON input; see generator/hosting-handoff.md. No purchase requested.
- [ ] FINAL-REVIEW-TASK-008 | 2026-09-23T06:21:53+00:00 | TASK-008 final CHANGES (REV-010), F1-F5: sales/outreach-review-round2.md. DEC-005: owner disposition, no third review. Include day-8 cadence decision.
