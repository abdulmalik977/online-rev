# TASK-008 — Codex review, round 1

Reviewed 2026-09-23 against commit `76866f2`, `sales/outreach.md`, accepted offer revision 2, DEC-002/003/007 and the task's definition of done. Result: **CHANGES**. No messages sent, production classifier implemented, or attempt recorded on Claude's task. The table below marks the decisions Codex would otherwise have to invent. Examples are specification counterexamples, not measurements of a running sender.

## Rules requiring interpretation or correction

| ID | Location | Evidence / missing decision | Required bounded revision |
|---|---|---|---|
| R01 | §5 precedence | `Can I have a refund?` matches question before refund; `Yes, refund please` matches interested first. `Stop, my lawyer will contact you` matches unsubscribe before legal escalation. | Make refund/legal detection override ordinary reply generation while still suppressing any opt-out. Specify combined actions, not only one winning class. Legal must not send an acknowledgement contrary to its no-reply rule. |
| R02 | §3/5 text detection | Every original footer contains `unsubscribe`. A positive reply quoting that footer can suppress the prospect. Keywords have no body/header/quotation boundary; `yesterday` contains `yes`; `report` can mean analytics. | Define newest authored body extraction, word/phrase boundaries, negation and multi-intent precedence; distinguish authenticated delivery/auto-response metadata from words in ordinary mail. Route uncertain intent to review without guessing. |
| R03 | §5 required classes | TASK-008 explicitly requires `not-now`; it is absent. `Not now` falls into other and `Not interested right now` into permanent negative. §1 says no follow-up after a reply while auto-reply explicitly continues. | Add not-now detection, canned action, retention/restart policy and exact human-reply versus automatic-response eligibility. Preserve the ever-three cap and handle the two-automatic-reply ceiling. |
| R04 | §1 timing / §4 pauses | Under Mon–Fri business-day arithmetic, day 0 Wed 2026-09-23 gives day 3 Mon 09-28 (outside allowed windows) and day 10 Wed 10-07. This fixture expires 10-06 00:00Z, before email 3. Three sends are therefore not guaranteed. | Define America/Chicago, holiday calendar, whether offsets count Mon–Fri or only send days, roll-forward rule, expiry cutoff and stale-preview handling after pauses. A send must recheck expiry. Do not reset the original preview date. Define the business-hour reply clock separately from Tue–Thu send windows. |
| R05 | §3 suppression / opt-out | One unsubscribe at `person@gmail.com` suppresses the entire `gmail.com` domain as written. A link scanner's GET counts as a page hit. `never send again` conflicts with the acknowledgement. | Explicitly choose shared-mail-domain and subdomain scope, address/domain normalization, opt-out request semantics/token mapping and idempotency. Define any non-promotional acknowledgement exception. Keep opt-out simple and functional for the full required period. |
| R06 | §3/4 bounces, complaints, caps | Three soft bounces lack a window/reset rule. Bounce and complaint rates lack denominator, attribution day, minimum sample, and missing-feedback handling. The same-domain five-send cap lacks global/mailbox scope. | Define all counters, DST/day reset, pause/resume and delayed-event attribution; specify DSN recipient/status handling, absent complaint feed, retry/dedup behavior, and which automated/internal sends consume each cap. Recheck caps and suppression atomically at send time. |
| R07 | §2/4 identity / warm-up | Fixed `hello@SENDING_DOMAIN` does not specify routing across 3–5 sending mailboxes. Weeks can start at account creation or first send. Internal reply exchanges have no evidence here of better deliverability. | Define mailbox configuration, stable thread sender and From/Reply-To alignment, warm-up start/age, pass criteria for DNS/authentication and allocation of all sends. Treat artificial warm-up benefits as unvalidated, not a readiness guarantee. |
| R08 | §1/5/6 sales promises | Email 1 promises the existing domain live within two days without the accepted payment/confirmation start clock or DNS exception. Email 2 says change anything. FAQ says about 30 minutes rather than the offer's cap. | Reuse offer rev2's precise clock, subdomain/DNS qualification and bounded request scope/30-minute cap in initial email, interested reply and FAQ. Provide exact interested/question/call canned templates and deterministic FAQ matching; unknown questions must not invent answers. |
| R09 | §5 escalation | Refund row auto-acknowledges but the final paragraph says nothing sent until owner resolution. Unknown FAQ promises one day without specifying whether an acknowledgement is allowed. No policy for an unresolved queue at the deadline or repeated inbound events. | State allowed acknowledgements per escalation class, owner-queue ID/dedup, reply-limit behavior, and overdue action. Legal remains no reply. Do not promise an owner response whose operating clock is undefined. |
| R10 | §7 metrics | Two human replies from one prospect could yield 200% reply rate. Question classified ahead of refund can make a refund positive. Internal warm-up and repeated webhooks are not excluded. Company reporting uses Asia/Riyadh, sends use Central. | Separate message counts from unique-person rates; define stable prospect/order IDs, event deduplication, daily versus pilot cohorts/time zones, excluded test/internal events and refunds. Define a view event/bot/IP filter with an available data source; current previews have no analytics. DEC-007 starts on the first real pilot outreach, not warm-up. |
| R11 | §8 launch / placeholders | Reply-to-order fallback is unwritten and departs from DEC-002's self-serve checkout. A disabled preview button cannot satisfy email 1/3 order-button copy. SIGNATURE is a defined footer expansion, but per-prospect values, mailbox identities and order links have no configuration schema. | Keep launch gated on usable self-serve checkout and matching copy; any alternate sales model needs an explicit decision, not implementer invention. Define runtime versus company config fields and reject unresolved placeholders. Include classifier and scheduler cases below in acceptance, not just happy paths. |
| R12 | §2 legal mapping | Accurate identity, ad disclosure, address and opt-out are mapped. A live page alone does not show that an opt-out works; outsourced sending and subsequent handling of suppressed addresses are not mapped. UK note is outside this pilot. | Map functional opt-out processing and downstream processors/data handling to an explicit operational control. Gate Houston-only targeting; a future UK launch needs its separate requirements, not just a privacy-page sentence. Do not expand this review into UK implementation. |

The capacity sentence is an estimate needing assumptions: 5 × 40 / 3 = **66.7 new prospects per send day** in a steady-state, three-message, no-reply cohort before internal mail/replies. A 70–100 estimate needs an observed early-stop mix; it is not a guaranteed capacity. The inherited A/B/C subjects for emails 2/3 are acceptable thread variants; no invented requirement for unrelated follow-up subjects.

## Twenty acceptance counterexamples

These fixtures require explicit expected actions in the revised specification. Current outcomes below follow the written row order; substring-dependent outcomes are labelled ambiguous. They are not claims that a production classifier has been tested.

| # | Input / event | Current consequence or ambiguity | Required acceptance property |
|---|---|---|---|
| 1 | `Yes, interested` | interested | Exact approved order reply; no invented clock. |
| 2 | Same reply + quoted original unsubscribe footer | unsubscribe under whole-message matching | Quoted footer cannot opt out a positive author. |
| 3 | `Can I have a refund?` | question | Refund escalation, not FAQ/positive metric. |
| 4 | `Yes, refund please` | interested | Refund escalation, no sales order reply. |
| 5 | `Stop. My lawyer will contact you.` | unsubscribe | Suppress AND legal escalation, no auto-reply. |
| 6 | `Please unsubscribe` | unsubscribe | Immediate suppression; acknowledgement policy explicit. |
| 7 | `Not now` | other | Defined not-now action, no automatic sales continuation. |
| 8 | `Not interested right now` | negative | Explicit temporary/permanent intent policy. |
| 9 | `I saw it yesterday` | interested if substring `yes` | Word-boundary/uncertainty policy prevents accidental interest. |
| 10 | `Can you show my monthly analytics report?` | negative/legal from `report` | Ordinary question must not automatically become a legal threat. |
| 11 | Human: `I am back from out of office; how much?` | auto_reply | Author text alone cannot reliably establish automatic origin. |
| 12 | Genuine auto-reply with quoted footer | unsubscribe if full body | Auto-response detection, quote extraction and continuation precedence defined. |
| 13 | Genuine 5.1.1 DSN for one queued recipient | bounce | Suppress actual failed recipient, not mailer-daemon; no reply. |
| 14 | Third soft DSN, first two in a prior month | bounce_soft_x3 unspecified | Exact window/reset and distinct-event count. |
| 15 | Duplicate delivery of the same inbound Message-ID | repeated action allowed as written | One count, one escalation/acknowledgement at most. |
| 16 | `owner@gmail.com` opts out | email + entire gmail.com | Shared-domain scope intentionally specified and tested. |
| 17 | Security scanner opens UNSUB_URL | opt-out page hit | Explicit request semantics and no burdensome opt-out steps. |
| 18 | Email 1 on 09-23; email 3 due 10-07; expiry 10-06Z | Dead preview link | Skip or explicit revised cadence; never extend fixture age silently. |
| 19 | Paid webhook delivered twice while email 2 queued | paid double-count / race unspecified | One paid order; send-time outreach suppression. |
| 20 | Third inbound after two automated replies, includes legal + opt-out | reply ceiling versus precedence unclear | Suppress/escalate regardless of reply ceiling; no third auto-reply. |

## External evidence and review boundary

The FTC business guide covers B2B commercial mail too. Opt-outs must remain functional at least 30 days after sending and be honored within ten business days, without fees or unnecessary steps. It also addresses transfer of opted-out addresses and responsibility for contractors. These support R05/R12; final operating controls still need implementation. [FTC CAN-SPAM guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business), checked 2026-09-23.

Google recommends keeping reported spam below 0.1% and avoiding 0.3% or higher. A configured pause threshold is not proof that provider feedback is available or that delivery is healthy. Bulk-sender requirements are not a new legal threshold for this small pilot. [Google sender guidelines FAQ](https://support.google.com/mail/answer/14229414?hl=en), checked 2026-09-23.

Return scope: revise this document's marked rules, supply deterministic expected actions for the fixtures, and resubmit TASK-008 for round 2. No sender implementation, outreach, new infrastructure or TASK-005 collection requested. Claude remains task owner; Codex records only `--review TASK-008 --result changes`.
