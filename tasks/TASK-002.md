---
id: "TASK-002"
title: "Validate DEC-001 market hypothesis with evidence"
owner: "claude"
status: "blocked"
goal: "Confirm or reverse DEC-001 (US/UK local service businesses, email-reachable, done-for-you buyers) using evidence, not opinion"
evidence: "research/markets/dec-001-validation.md; research/markets/dec-001-challenge.md (round 1); research/markets/dec-001-challenge-round2.md; reviews/REV-006.md final CHANGES REQUESTED; FINAL-REVIEW-TASK-002 and SPEND-PROSPECTS pending; verified 200-business CSV absent"
definition_of_done: "research/markets/dec-001-validation.md with: 5 candidate verticals scored on (a) findable business emails per 100 Google Maps listings, (b) existing spend on done-for-you services with 3 priced competitor examples each, (c) cold-email legal status per country with source links, (d) sample-before-contact feasibility; one recommended vertical + one fallback; sources linked"
success_metric: "At least 200 real prospects with a valid business email located in the recommended vertical, stored in research/markets/prospects-sample.csv, and Codex CHALLENGE recorded via --review"
attempts: 3
review_round: 2
quota_budget: 60
created: "2026-09-22T08:00:00+00:00"
updated: "2026-09-22T09:49:57+00:00"
---
Reviewer: codex. Two review rounds max. No outreach, no sending, no spend.

## Handoff to Codex (round 1)
Research deliverable: research/markets/dec-001-validation.md. CHALLENGE it via
`--review TASK-002 --result changes|pass --note` — attack the scoring, the UK narrowing,
and the vertical choice with evidence, not preference.
The 200-email CSV (success metric) is execution, not research: it needs network access
and ~$25 of tooling. Sequence: owner resolves SPEND-PROSPECTS → Codex runs the pipeline
in §"Prospect pipeline" and commits research/markets/prospects-sample.csv → then PASS is
possible. If Codex passes the research before the CSV exists, keep status `doing` and
record the CSV commit as the closing evidence.

## Round 2 handoff (Claude → Codex)
Revision 2 of research/markets/dec-001-validation.md answers REV-005 §1–§5; see its §7.
Material change: fallback is now US cleaning, not dental (criterion (e) self-serve buying norm).
This is the final review round (DEC-005). PASS on the research is expected only together
with the CSV; if the CSV is still blocked on SPEND-PROSPECTS, record the research verdict
in the note and keep status doing until the CSV commit.

## Final review disposition (Codex)
REV-006 records round 2 CHANGES REQUESTED against 6955490. See research/markets/dec-001-challenge-round2.md for resolved points, source checks and remaining F1/F2. DEC-005 requires owner escalation after two rounds: status blocked pending FINAL-REVIEW-TASK-002, not a third review or autonomous Claude retry. Research remains a pilot hypothesis; the contradictory pipeline handoff and scoring claims need bounded disposition. SPEND-PROSPECTS remains pending, and the 200-business verified CSV is still required for completion. Codex recorded no --attempt in this round; attempts remains 3.
