# Pending owner approvals / missing inputs

Each entry is one line: `- [ ] ID | UTC timestamp | description`.
Resolve by moving the entire entry to done.md and changing `[ ]` to `[x]`.
Keep the original timestamp; watchdog deduplicates against both files.
- [ ] LOOP-TASK-LOOP | 2026-09-22T06:19:09+00:00 | TASK-LOOP: review_round > 2; resolve loop
- [ ] SETUP-EMAIL | 2026-09-22T06:26:40+00:00 | Provide owner email and private SMTP configuration; no mail sent
- [ ] SETUP-CRON | 2026-09-22T06:26:40+00:00 | Specify Linux cron host and deployment path; schedule not installed
- [ ] SPEND-PROSPECTS | 2026-09-22T08:42:02+00:00 | Approve up to $25 for prospect data (Outscraper/Apify scrape + Reoon verification) to build the 200-email CSV for TASK-002; vertical: US plumbing/HVAC, one metro
- [ ] DEC-001-AMEND | 2026-09-22T08:42:02+00:00 | Amend DEC-001: UK limited to Ltd/LLP verified via Companies House (PECR treats sole traders as individuals); evidence in research/markets/dec-001-validation.md
- [ ] FINAL-REVIEW-TASK-002 | 2026-09-22T09:49:57+00:00 | TASK-002 final round 2 CHANGES (REV-006): resolve F1 pipeline/F2 ranking; accept bounded pilot or change/stop. Details: research/markets/dec-001-challenge-round2.md. No third review; SPEND-PROSPECTS separate.
