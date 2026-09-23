# Locked decisions

- DEC-001: US/UK local service businesses; USD/GBP pricing. Exclude AU/CA/DE and Saudi.
  This is a market hypothesis for Claude to validate on days 1–5; reversal requires evidence.
  The kickoff's outreach-law assumptions are not legal clearance; validate eligibility before outreach.
- DEC-002: Self-serve, fixed-price sales; no human sales, calls, or demos.
- DEC-003: Dedicated sending domain; 3–5 mailboxes; at most 40 emails/mailbox/day;
  unsubscribe, plain text, company-team signature. Paid social inbound later.
  No WhatsApp or automated DMs. No sending infrastructure in this build.
- DEC-004: Markdown-in-Git + SQLite + cron until the first paid customer.
- DEC-005: At most two review rounds, then escalate to the owner.
- DEC-006: Pick ONE monthly done-for-you product by day 5, $99–$300/month,
  at least 70% automated by Codex, with a prospect-specific sample before contact.
  Evaluate GBP/review management, website+maintenance, missed-lead follow-up,
  and monthly local-SEO content. Claude proposes; Codex challenges.
- DEC-007 (owner, resolves FINAL-REVIEW-TASK-002): desk research cannot produce demand
  evidence before selling; TASK-002 is accepted as a bounded pilot hypothesis, not a proven
  ranking. Pilot: US plumbing/HVAC, Houston metro; fallback US cleaning; dental deprioritized
  for its demo-led buying norm. Demand evidence = pilot metrics (emails → replies → sample
  views → paid), thresholds in research/markets/dec-001-validation.md §6.
  SPEND-PROSPECTS approved at a $25 cap. DEC-001 amended: UK = corporate subscribers only,
  implemented as Ltd/LLP verified via Companies House.
  TASK-002 closed by owner decision (counters exhausted); its CSV metric moves to TASK-005.
  Owner approval given 2026-09-22 with a time-box: the pilot runs 60 days from the first
  outreach email. Checkpoint at day 30 (reply rate, sample views); at day 60 with no paid
  customer, the target vertical changes (fallback: US cleaning) — the product and pipeline
  stay. Owner is not asked again inside the time-box unless a spend or legal decision arises.
- DEC-008 (owner, resolves FINAL-REVIEW-TASK-008): sales/outreach.md rev 2 plus the §12
  amendments (A1–A6, answering REV-010 F1–F5) is the binding outreach specification.
  Email-3 cadence is day 8 (not the task text's day 10). TASK-008 is closed by owner decision;
  remaining disagreements are settled by automated tests in TASK-009 (sender implementation,
  Codex builds, Claude reviews), not by a further prose round. General rule from now: a
  specification gets at most two review rounds; after that, implementation with tests is the
  arbiter and the reviewer's remaining findings become test cases.
