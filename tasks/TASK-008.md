---
id: "TASK-008"
title: "Outreach sequence, compliance kit and reply handling rules"
owner: "claude"
status: "done"
goal: "Write everything the sending system needs so that Codex can wire it without interpretation: the 3-email sequence with the preview link, CAN-SPAM footer, unsubscribe handling, suppression list rules, sending schedule within DEC-003, and reply-classification rules with canned responses"
evidence: "DEC-008 owner closure; sales/outreach.md rev2 plus binding section 12 A1-A6; prior REV-009/010 retained; executable findings transferred to TASK-009, no further prose review"
definition_of_done: "sales/outreach.md with: email 1 (preview), email 2 (day 3 nudge), email 3 (day 10 expiry notice), subject lines (3 variants each for A/B), footer block with physical address placeholder and unsubscribe line, suppression rules (unsubscribe, bounce, reply-negative, role addresses), warm-up schedule for new mailboxes (weeks 1-3), daily caps, reply classes (interested / question / not-now / negative / auto-reply / bounce) each with a canned reply or action, escalation rules to the owner (legal threats, refund requests), and the metrics definitions for the daily report pipeline line"
success_metric: "Codex PASS via --review confirming every rule is machine-implementable (no ambiguous instruction), and a checklist mapping each CAN-SPAM requirement to the email element that satisfies it"
attempts: 2
review_round: 2
quota_budget: 30
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-23T09:12:08+00:00"
---
No sending. Owner still owes SETUP-EMAIL (sending domain + mailboxes); this task removes
every other blocker so sending can start the day those exist. Reviewer: codex.

## Handoff (Claude -> Codex, round 1)
Deliverable: sales/outreach.md (sequence, compliance map, suppression, warm-up, reply classes, FAQ, metrics, go-live checklist). Review for machine-implementability: flag any rule that needs interpretation. Record via --review TASK-008. No --attempt on this task.

## Codex round-1 result
CHANGES recorded through --review in REV-009. Correct the marked R01-R12 rules and define the twenty acceptance outcomes in sales/outreach-review.md; resubmit for round 2. No sender implementation or additional scope requested. attempts remains 1; Codex did not record --attempt on this Claude-owned task.

## Round 2 handoff (Claude -> Codex, final round)
sales/outreach.md revision 2: section 11 maps R01-R12; section 9 gives expected actions for all 20 fixtures. One deliberate deviation from the DoD text: email 3 offset is day 8, not day 10 (calendar proof in section 1). Record via --review TASK-008.

## Final round 2 result
REV-010 records CHANGES against 7576955. All twenty section-9 cases checked: fourteen consistent under stated fixture conditions, five mismatched/contradictory (4,6,7,8,10), one partial (20). Keyword/FAQ/calendar probes are reproducible in sales/qa; this is a specification audit, not production sender testing.

F1-F5 and bounded corrections are in sales/outreach-review-round2.md. Per DEC-005, status is blocked for FINAL-REVIEW-TASK-008 owner disposition: no third review or autonomous Claude retry. Codex did not call --attempt; attempts remains 2 from Claude revision-2 patch. No sending or other task execution.

## Owner closure
Closed by DEC-008 after two review rounds (REV-009, REV-010). Specification = rev 2 + section 12 amendments A1-A6. Remaining findings become automated tests in TASK-009.
