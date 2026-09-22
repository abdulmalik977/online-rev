---
id: "TASK-008"
title: "Outreach sequence, compliance kit and reply handling rules"
owner: "claude"
status: "todo"
goal: "Write everything the sending system needs so that Codex can wire it without interpretation: the 3-email sequence with the preview link, CAN-SPAM footer, unsubscribe handling, suppression list rules, sending schedule within DEC-003, and reply-classification rules with canned responses"
evidence: "DEC-003 limits (3-5 mailboxes, <=40/mailbox/day, plain text, unsubscribe, team signature); dec-001-validation.md section 4 legal checklist; offer.md section 4 email copy"
definition_of_done: "sales/outreach.md with: email 1 (preview), email 2 (day 3 nudge), email 3 (day 10 expiry notice), subject lines (3 variants each for A/B), footer block with physical address placeholder and unsubscribe line, suppression rules (unsubscribe, bounce, reply-negative, role addresses), warm-up schedule for new mailboxes (weeks 1-3), daily caps, reply classes (interested / question / not-now / negative / auto-reply / bounce) each with a canned reply or action, escalation rules to the owner (legal threats, refund requests), and the metrics definitions for the daily report pipeline line"
success_metric: "Codex PASS via --review confirming every rule is machine-implementable (no ambiguous instruction), and a checklist mapping each CAN-SPAM requirement to the email element that satisfies it"
attempts: 0
review_round: 0
quota_budget: 30
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-22T19:50:00+00:00"
---
No sending. Owner still owes SETUP-EMAIL (sending domain + mailboxes); this task removes
every other blocker so sending can start the day those exist. Reviewer: codex.
