# TASK-002 — Codex CHALLENGE, final round 2

Reviewed 2026-09-22 against commit `6955490` (Claude revision 2).
Decision: **CHANGES REQUESTED; escalate to owner under DEC-005.**
Research verdict: improved, usable as a pilot hypothesis, but not an evidence-backed
validation of the proposed ranking or a consistent execution handoff. Task completion
also remains gated on the real 200-business verified CSV. No third review is opened.

## Resolved from REV-005

- US-only totals now recompute correctly: plumbing/HVAC 23, cleaning 21, detailing
  21, landscaping 19, dental 18. All use the same US legal score.
- Common yield bins and equal hypothesis scores remove the prior unsupported
  email-yield advantage; the Texas dental vendor statistic is explicitly unverified.
- The revision distinguishes published offers from demand, acknowledges the absence
  of no-call purchases, and adds per-vertical competitor tables with delivery type.
- UK Ltd/LLP is now a proposed operational filter, incorporation shares are explicitly
  unmeasured, and HIPAA is described as an implementation burden rather than a ban.
  These address the interpretation problems documented in the first challenge;
  this review does not grant legal clearance or resolve DEC-001-AMEND.
- The scenario arithmetic is correct: 700 * .30 * .80 * .85 = 142.8;
  1,000 * .30 * .80 * .85 = 204. Neither is an observed yield.

## F1 — Execution plan contradicts revision 2 (must resolve before collection)

At the reviewed commit, validation section 5 specifies about 1,000 listings and
cleaning as fallback, but prospect-pipeline-plan.md step 6 still caps listings at
approximately 700 and step 5 still names dental. Its purchasing paragraph changes
the quantity to 1,000 but retains the old 700-record cost estimates.

For the stated envelope of 1,000 listing records **and** 1,000 enriched domains,
Outscraper lists separate 500-unit free tiers and $3/1,000 paid units for each service.
Thus both free tiers available: 2 * (1,000 - 500) * .003 = **$3.00**; both exhausted:
2 * 1,000 * .003 = **$6.00**. Validation's $1.50 lower bound counts only one service.
The plan's $1.20/$4.20 figures are stale. These are usage estimates, not checkout
quotes; actual domains processed and account allowances can change the charge.
[Outscraper pricing](https://outscraper.com/pricing/), checked 2026-09-22.

With the listed $11.90 one-time Reoon package, that envelope is **$14.90–$17.90**
before tax, minimum top-ups and fallback lookups. The $25 all-in cap can still be
plausible, but requires account quotes. [Reoon pricing](https://www.reoon.com/email-verifier/),
checked 2026-09-22.

Bounded resolution: reconcile both files to the same listing envelope, cleaning
fallback and corrected arithmetic; preserve the initial 300-listing raw-yield
stop rule and require revised scope approval before switching verticals.

## F2 — The new ranking criterion remains a proxy, not a buying norm

Section 2 calls criterion (e) direct evidence for DEC-002 and uses it to demote dental.
But the cleaning score of 5 is based on DIY software signup, while its documented
DFY vendor sells through a call. ZenMaid confirms $19/$39/$49 software plans and a
trial; that is evidence of software availability, not purchases of our DFY offer.
[ZenMaid pricing](https://get.zenmaid.com/pricing), checked 2026-09-22.

Zero Degree confirms $97/$147 managed websites, no setup fee, and a launch process
starting with a call; it explicitly serves plumbing, HVAC, cleaning and landscaping.
That supports offer availability across those verticals, not a distinct no-call
advantage for plumbing or cleaning. [Zero Degree pricing](https://www.zerodegreemedia.com/pricing),
checked 2026-09-22.

Detailer Systems confirms a $297 managed service with free setup and a launch call.
Its $997 advertising service is additional. This is in-band DFY supply for detailing;
it does not establish no-call demand either. [Detailer Systems pricing](https://detailersystems.com/pricing),
checked 2026-09-22.

NiceJob confirms $75/$125 software and a separate $99 Sites service with $199 setup.
The software trial CTA should not automatically classify the separate Sites buying
process. [NiceJob pricing](https://get.nicejob.com/pricing), checked 2026-09-22.

The rubric only anchors (e)=1 and 5, without a reproducible rule for dental=2 or
landscaping=4. It also leaves (b)=4 and the cross-vertical DFY supply comparison
unexplained. Counterfactual check: replacing all five (e) scores with the same
unknown value of 3 produces 21/19/19/18/19 in the table's row order. Dental then ties
cleaning and detailing. This is sensitivity analysis, not a replacement ranking.

Bounded resolution: label vendor sales motion as a supply-side proxy, explain the
intermediate score rule, and treat fallback choice/switching cost as hypotheses.
Do not require outreach to revise those claims, and do not infer that dental must
replace cleaning. Competitor tables meet the count of priced rows, but mostly DIY
rows cannot establish three DFY spend examples per vertical as the task describes.

## Additional source qualifications (not separate blockers)

- Service Autopilot confirms $49/$199/$499 as annual-subscription monthly rates
  plus signup fees; the page also offers self-signup. A demo button alone does not
  establish an exclusively demo-led motion. [Official pricing](https://www.serviceautopilot.com/pricing/).
- PatientGain's linked dental pricing also lists a $299 FastStart option. Its
  linked detail page could not be fetched, so delivery/setup terms remain unknown.
  This does not prove a qualifying DFY counterexample, but the categorical claim
  that no in-band DFY dental product exists exceeds the verified evidence.
  [PatientGain pricing](https://www.patientgain.com/pricing-medical-digital-marketing).
- Launch27 and Urable fetches failed in this review. Failure is not evidence that
  their prices are wrong. Jobber's third-party price basis is disclosed in the
  revision and should not be called a primary-source verification.

## Completion and owner disposition

At review time, prospects-sample.csv does not exist, SPEND-PROSPECTS remains in
approvals/pending.md, and no matching completion is in approvals/done.md. The
success metric is therefore unmet; no placeholder CSV or conditional task PASS.

The second review is recorded using --review TASK-002 --result changes. The command
sets doing; this final unsuccessful review is then explicitly blocked and escalated
under company/DECISIONS.md DEC-005. This overrides the handoff's suggestion to keep
doing while CSV is pending because substantive final-review findings also remain.
The owner can accept the bounded pilot limitations and authorize the corrections
and funded collection, or change/stop the task. No automatic attempt or third round
is authorized. SPEND-PROSPECTS and DEC-001-AMEND stay separate pending decisions.

No --attempt was recorded by Codex in this round; attempts stays 3. No spending,
collection, outreach, new infrastructure, or changes to Claude's research were made.
