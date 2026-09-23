# Current goal — Phase 2: build the product and the sales path (no external accounts yet)

Owner decision 2026-09-22: build fundamentals first; external accounts (Outscraper, Reoon,
payment provider, sending mailboxes) come last. TASK-005 (200-prospect CSV) waits; it is not killed.
Pilot per DEC-007: US plumbing/HVAC, Houston; 60-day time-box starts at first outreach email.

Order of work:
1. Codex: review TASK-003 (offer.md) via --review. Then TASK-006 (generator v1, 10 hand-collected test prospects, previews on an eligible commercial host per offer rev2).
2. Claude: TASK-008 (outreach sequence + compliance kit) in parallel.
3. Codex: TASK-007 (landing page + provider-agnostic order flow) after TASK-006.
4. Then owner inputs, all at once: sending domain + mailboxes (SETUP-EMAIL), payment provider, Outscraper/Reoon → TASK-005 → first emails.

Exit condition for phase 2: 10 live previews, landing page live, outreach kit passed, order flow tested with a fake webhook.
Revenue target unchanged: 10,000 SAR/month.

## Execution status 2026-09-23
TASK-003 is done (REV-008 final PASS). TASK-008 round 1 requires changes (REV-009; sales/outreach-review.md). TASK-006 reached session 3/3 and is blocked on hosting access and expiry execution, with zero live previews; Netlify Free is the selected candidate (generator/hosting-handoff.md). The owner explicitly requested commercial publication; SETUP-HOSTING records missing access, not a new spending approval. TASK-005 remains deferred, and TASK-007 has not started.
