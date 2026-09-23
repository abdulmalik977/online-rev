# TASK-008 final review, round 2

Review target: `7576955`, `sales/outreach.md` revision 2, 2026-09-23. **CHANGES; escalate under DEC-005, no third review.**

## Verification design (before audit code)

Use a read-only local probe to extract the written keyword lists and FAQ from the reviewed Markdown, apply whole-word matching to the actual text fixtures, and calculate the two calendar variants. Preserve its source hash and JSON output. It is a specification audit, not a sender, mail integration, or production classifier test. Check all twenty acceptance rows manually against the complete state/decision rules as well: the text probe cannot resolve contradictory state transitions or prove transactional sending. No external messages, task attempts, or infrastructure work.

## All twenty section-9 cases

Consistent means the expected result follows from the specification, not a production test pass. Common assumptions: one known prospect/email, fresh Message-ID unless case 15, thread-correlated DSNs, valid configuration, no exhausted cap unless stated. Case 2 uses the exact quoted signature in section 5.2. Case 18 uses a NEW September 23 preview and 08:30 CDT first send, not the existing September 22 generator previews.

| # | Result | Evidence / qualification |
|---|---|---|
| 1 | Consistent | INTERESTED from interested; row 8 chooses ORDER, sets replied and cancels outreach. |
| 2 | Consistent | Exact quoted footer is removed by section 5.2; remaining body is case 1. Other quoting formats are not demonstrated. |
| 3 | Consistent | REFUND + QUESTION; row 3 precedes questions: ACK_REFUND and escalation, not positive. |
| 4 | **Mismatch: flags** | Actual flag is REFUND only. The yes rule requires the ENTIRE body to equal a short affirmative. Refund action is correct, but this does not test combined INTERESTED+REFUND as claimed. |
| 5 | Consistent | LEGAL only; suppress/escalate, no reply. Bare-body stop intentionally does not match this sentence. |
| 6 | **Contradiction: state** | Row 1 sets suppressed and queues ACK_UNSUB without stopping; section 5.4's final sentence sets every human reply to replied. Expected final suppressed state needs an explicit exception. |
| 7 | **Contradiction: state** | Row 5 sets not_now, then the final human-reply rule says replied. No separate not-now deadline field exists. Retained state/60-day eligibility needs explicit precedence. |
| 8 | **Mismatch: flags/action** | Actual NEGATIVE + INTERESTED, NOT NOT_NOW: none of the NOT_NOW phrases matches not interested right now. Row 4 selects uncertain/no reply, not ACK_NOT_NOW. Adding the missing temporary phrase alone would still leave INTERESTED triggering row 4. |
| 9 | Consistent | No flags; yesterday does not equal yes. Row 10 queues other, no reply. |
| 10 | **Mismatch: action** | QUESTION matches FAQ contract via its explicit monthly keyword. Result is a contract/cancellation answer, not ACK_QUESTION and owner queue. |
| 11 | Consistent | No auto headers; QUESTION matches price through how much. Body out of office does not trigger the header rule. |
| 12 | Consistent | Auto-Submitted auto-replied is an automatic-origin signal; ignored before text processing, not a human-reply metric. |
| 13 | Consistent with correlation | Known/thread-correlated DSN, Status 5.1.1: suppress failed recipient, not daemon; no reply. DSNs without outer thread correlation are a separate gap below. |
| 14 | Consistent with correlation | Two DSNs 40 days old are outside the 30-day window; current third distinct soft DSN counts as one, no suppression. |
| 15 | Consistent | Previously recorded Message-ID ignored before actions/counting. Missing IDs and crash recovery not covered. |
| 16 | Consistent for one known email | Opt-out has no domain row, including gmail.com. Other known emails for the same business are also suppressed by section 3.1; include them if fixture has multiple addresses. |
| 17 | Consistent | GET renders only; POST suppresses. Does not prove hosted POST or DKIM header behavior. |
| 18 | Consistent for newly dated fixture | With 08:30 CDT initial send, day 8 is 2026-10-01 13:30Z, before 10-06 00:00Z cutoff. Synthetic holiday moves slot to 10-06 13:30Z, skipped. Original September 22 previews still expire October 6, not October 7. |
| 19 | Consistent for queued send | Duplicate order_id gives one paid record; queued email 2 reloading state after payment is refused. Not proof of in-flight SMTP crash/race behavior. |
| 20 | **Partial: persistence** | OPT_OUT+LEGAL suppresses/escalates without reply regardless of ceiling. But CSV has one reason and existing keys are not duplicated: the email key written as unsubscribe cannot retain a second legal row. Define whether both reasons means durable evidence of both or union of suppressed addresses. Final state also has case-6 conflict. |

Totals: **14 consistent under explicit fixture assumptions, 5 mismatched/contradictory, 1 partial**. Not 14 live tests passed. The read-only [probe](qa/task008-rev2-check.py) and [JSON observations](qa/task008-rev2-results.json) reproduce text/FAQ/calendar findings; this table covers all twenty action paths. Run `python sales/qa/task008-rev2-check.py` from the repository root.

## Blocking findings for owner disposition

### F1 - Acceptance examples disagree with matching rules

Cases 4/8/10 conflict with sections 5.3/5.4/7 (reviewed file lines 144-163, 188, 212/216/218). The probe extracts keyword lists directly from the Markdown. Case 8 needs a negation/temporary-interest policy, not just another phrase: plain `Not interested` also sets INTERESTED+NEGATIVE and becomes uncertain instead of permanent-negative. Case 10 needs keyword scoping or an honest expected FAQ action. Correct fixture-4 flags or choose a fixture that actually tests combined refund/interest.

### F2 - Opt-out, reply arbitration and state transitions conflict

Section 5.4 row 1 queues ACK_UNSUB without stopping ordinary sales branches. `Unsubscribe. I was interested.` sets OPT_OUT+INTERESTED and reaches ORDER; `Unsubscribe. Refund please.` queues ACK_UNSUB before ACK_REFUND. At most one reply is allowed but no arbitration is supplied. The unconditional final replied state also overwrites suppressed/not_now/paid states. Define terminal suppression, retained state/deadline and at most one permitted non-promotional acknowledgement.

Section 4.4 rechecks section 1's active-only/Tue-Thu/expiry gate for each scheduled send, while section 5 requires replies for replied/suppressed customers Mon-Fri, including refunds unrelated to preview expiry. Distinguish outreach eligibility from permitted service acknowledgements while retaining caps. Define what happens when a cap prevents the 15-minute reply; do not silently exceed DEC-003.

FTC guidance requires honoring opt-outs and warns against filtering them away. This finding is an inconsistent implementation specification, not a claim that messages were sent unlawfully. [FTC business guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business), checked 2026-09-23.

### F3 - Revised expiry rule extends existing previews

Sections 0/1 reset a delayed preview to email-1 date (lines 9/14). Existing generator manifest/hosting handoff preserve **2026-09-22 to 2026-10-06T00:00:00Z**. A September 23 email would reset this to October 7. Case 18 changed creation date instead of testing the original fixture. Keep generation/publication age as expiry authority; store first-send time separately and skip when no slot remains. An explicitly authorized new preview/batch is different from silently re-dating an existing deployment.

Day 8 itself is a technically sensible documented cadence adjustment; its arithmetic works for Tue-Thu starts without holidays. It differs from the day-10 task DoD, so include that narrow adjustment in owner disposition rather than pretend the DoD changed. No objection to selecting day 8 itself.

### F4 - Complaint pause unreachable; SMTP unknown outcomes unhandled

Sections 4.2/4.3 cap a mailbox at 40 sends per Central day but require at least 100 in that same daily denominator for complaint-rate pausing. The branch cannot trigger even with a complaint feed. Reply-based complaints suppress recipients/domains but do not specify an equivalent mailbox pause. Choose a reachable window/denominator or direct complaint-event rule.

Section 4.4 logs only AFTER SMTP 250. If the process exits after acceptance but before durable logging, a retry sees no row and sends again. An ambiguous transport timeout also lacks a policy. A local lock does not make SMTP and disk one transaction. Specify durable pre-send intent/stable identity and a reconciliation/hold policy for unknown outcomes. The existing sequence cannot claim retry deduplication or an ever-three cap under failure. No new service is needed to specify this within the current storage design.

### F5 - Response-suppression header mistaken for automatic origin

Section 5.1 ignores any message carrying X-Auto-Response-Suppress and continues outreach. Microsoft defines this header as controlling automatic replies TO that message; presence alone does not prove automatic authorship. A known prospect's human opt-out carrying it would be discarded before text processing. Distinguish automatic-origin classification from a request not to auto-reply; suppression/escalation must still work. [Microsoft protocol definition](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxcmail/e489ffaf-19ed-4285-96d9-c31c42cab17f), [RFC 3834](https://www.rfc-editor.org/rfc/rfc3834.html), checked 2026-09-23.

## Remaining bounded clarifications

- Section 5.0 routes unknown senders before DSN parsing, although daemon mail can lack matching OUTER thread headers; correlate embedded original headers/recipient before unknown-sender dispatch. Define missing Message-ID behavior.
- Section 0 defines a string slug but section 1 applies modulo 3 directly; section 4 leaves hash algorithm and mailbox order unspecified. Define stable numeric mapping and queued-to-active transition. Config needs the prospect state/region field, complaint-feed option and analytics IP exclusions it later uses; domain names are not IP ranges.
- Section 7's maximum two FAQ answers needs a tie-break for three matches. Owner-response and payment/confirmation clocks should explicitly use the accepted offer's start conditions. These are specification clarifications, not new sales features.
- Claimed RFC 8058 support requires valid DKIM covering BOTH List-Unsubscribe headers; generic dkim=pass does not establish this. Add header-coverage and direct HTTPS POST acceptance checks without redirect/session dependency. [RFC 8058 sections 3-4](https://www.rfc-editor.org/rfc/rfc8058), checked 2026-09-23. This is the chosen protocol's requirement, not a claim that CAN-SPAM mandates RFC 8058.
- Section 10 improves unique-prospect metrics and n/a without analytics. Define reporting-window cutoff and prospect attribution of multiple order IDs for paid conversion; do not divide raw orders by prospects. Existing report replies/numeric schema still needs an explicit implementation mapping.

## Resolved points and final disposition

Revision 2 improves refund/legal priority, mailbox routing, warm-up age, shared-domain suppression, GET/POST opt-out, checkout gating, canned templates, unique-prospect metrics and hosting/expiry launch gates. It removes the unsupported capacity estimate and marks internal warm-up benefits unvalidated. Retain these improvements; no return to revision 1 requested.

The success metric requires implementation without interpretation. F1-F5 prevent PASS. Record `--review TASK-008 --result changes` once (round 2), then block the task and add FINAL-REVIEW-TASK-008 for owner disposition under DEC-005. No third review, autonomous Claude retry, sender implementation or outreach. Codex records NO --attempt; Claude's patch supplies attempt 2 and that count stays 2.
