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
TASK-003 is done (REV-008 final PASS). TASK-008 is done by DEC-008; binding specification is rev2 plus A1-A8. TASK-009 passed Claude review in REV-011 (round 1) at d103ef3. A8 was implemented within TASK-007 session 1/2: sender 80/80 and orders 31/31 pass; portable sales page and signed fake order-to-promotion flow exist. Local mobile Lighthouse performance is 100; no hosted result is claimed. No further prose review. TASK-006 reached session 3/3 and is blocked on hosting access and expiry execution, with zero live previews; Netlify Free is the selected candidate (generator/hosting-handoff.md). The owner explicitly requested commercial publication; SETUP-HOSTING records missing access, not a new spending approval. TASK-005 remains deferred, and TASK-007 completed local session 2/2 and is in review per owner request; concept mailto, local lifecycle and review evidence are ready. Public deployment and real-account acceptance remain unverified; no automatic extra session.

Current owner-directed work: independent Claude code review of TASK-007 (orders/REVIEW-HANDOFF.md); owner-requested concept mailto and session-2 lifecycle implementation are submitted. Sender remains local/offline; no launch until external gates and TASK-007 code review pass. See site/README.md and orders/README.md. TASK-LOOP was killed by the DEC-008 package; its historical evidence is retained.
