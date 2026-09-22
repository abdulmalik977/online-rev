# TASK-002 — Codex CHALLENGE, round 1

Reviewed 2026-09-22 against research commit `0b30d8f`.
Decision: **CHANGES REQUESTED**. US plumbing/HVAC remains a reasonable pilot
hypothesis, but the submitted evidence does not confirm the market or establish
its superiority to dental. Do not mark TASK-002 done before the verified CSV exists.
No outreach, provider purchase, or new infrastructure was performed for this review.

## 1. The ranking is not reproducible

Recomputed directly from lines 20–24 of dec-001-validation.md, using the explicitly
listed US legal score (5) consistently for every US candidate:

| Vertical | Stated total | Sum of supplied US scores |
|---|---:|---:|
| Plumbing/HVAC | 18 | 3+5+5+5 = 18 |
| Dental | 17 | 5+4+5+4 = 18 |
| Cleaning | 15 | 3+3+5+5 = 16 |
| Landscaping | 13 | 2+3+5+4 = 14 |
| Auto detailing | 12 | 3+2+5+5 = 15 |

Dental's 17 can be obtained with its UK score, while detailing's 12 uses its UK
score despite its US label. Cleaning and landscaping match neither displayed
country score. A country-specific comparison is necessary. Correct arithmetic
alone ties US dental with plumbing/HVAC; it does not prove dental is better.
Required revision: define the aggregation rule, separate countries, recompute all
totals, and explain the primary/fallback choice after the correction.

## 2. Email-yield scores are hypotheses, not five comparable observations

The source study reports 9,166 email-bearing records among 26,376 Texas dentist
establishments: 34.75%, as vendor-reported indexed data. It also mentions 11,734
contacts from an export without reconciling that denominator. Neither figure is
a matched sample of our metro's plumbing/HVAC businesses. The cited source is
real, but its population and verification method cannot be silently transferred
to another vertical. [Scrap.io's own account](https://scrap.io/extract-emails-google-maps).

In the submitted table, approximately 35% earns dental 5/5 while approximately
30–40% earns plumbing 3/5. No common scoring bins, listing sample, extraction date,
or raw counts for the other three verticals are supplied. Website prevalence is
also different from a verified, usable email yield. The official Places schema
includes websiteUri and phone fields, with no email field; site/contact discovery
is therefore a separate step. [Google Places schema](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places).

Required revision: label vendor estimates explicitly, use common bins, and report
listing count, unique-business count, located-email count and verified-email count
separately. Do not invent measurements to fill the five-vertical comparison.

## 3. Published prices validate supply, not the claimed purchasing behavior

Primary-source spot checks substantiate NiceJob $75/$125 per month, GatherUp $99
for one location plus a $40 listings add-on, and B12 $24/$78. These are useful
price references; they are not errors to manufacture for the sake of CHALLENGE.
[NiceJob](https://get.nicejob.com/pricing), [GatherUp](https://gatherup.com/pricing/),
[B12](https://www.b12.io/pricing/).

However B12 distinguishes DIY from expert service, and GatherUp includes customer
upload integrations. These are not proof that customers do nothing. Rosie's page
does list $49/$149 tiers, a self-serve trial, plumbing/HVAC industry links, and its
own 2,000+ SMB claim. It does not break those SMBs down by vertical, paid tier,
acquisition channel, or conversion without calls. [Rosie](https://heyrosie.com/pricing).

The marketing-spend article stratifies contractors by revenue and discusses
overall advertising/channel budgets. It cannot establish a representative
$2,000–$10,000 monthly spend for every prospect, or willingness to buy our offer.
[PipelineOn's original article](https://pipelineon.com/blog/marketing-spend/).

The task asks for three priced competitors **per vertical**; the deliverable
organizes them **per product category** instead. Required revision: map three
primary-source examples to each of the five verticals, disclose setup, customer
work, billing terms and optional sales assistance, and distinguish vendor claims
from observed purchases. Replace "confirmed"/"proven self-serve demand" with a
testable hypothesis unless actual supporting acquisition evidence is supplied.
No new sales experiment is authorized by this review.

## 4. UK narrowing is supported as a policy choice, with narrower claims

ICO confirms the distinction between corporate subscribers and sole traders/
certain partnerships; unknown subscriber types should be treated conservatively.
Its corporate category also includes Scottish partnerships and other corporate
bodies. Therefore Ltd/LLP-only is our proposed operational filter, not the full
legal definition. Business identity must be matched to the actual contact, and
personal-data obligations still apply. The regulator flags its guidance as under
review following the Data (Use and Access) Act. [ICO B2B guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/).

The official statistics confirm 57% sole proprietorships across the UK private
sector and 885,000 construction SMEs. Those aggregates do not establish the legal
form of most dental practices, the corporate share of a particular trade list,
or whether a particular recipient gave consent. VAT/PAYE registration and
incorporation are different measures. [UK 2025 business population release](https://www.gov.uk/government/statistics/business-population-estimates-2025/business-population-estimates-for-the-uk-and-regions-2025-statistical-release).

Required revision: retain the proposed conservative filter, identify the stronger
claims as unmeasured, and leave DEC-001-AMEND pending until the owner decides.
US opt-out mechanics broadly match FTC guidance, which expressly covers B2B too;
this supports a conditional compliant channel, not unrestricted sending permission.
[FTC guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business).

Also replace the categorical "HIPAA rules out call-handling products" with an
implementation-risk judgment. HHS permits relevant third-party PHI processing
subject to business-associate agreements and applicable safeguards. That adds
requirements; it is not a blanket ban. This does not approve building such a
product. [HHS business-associate guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html).

## 5. The 200-email completion gate and collection assumptions remain open

At review time research/markets/prospects-sample.csv does not exist. SPEND-PROSPECTS
is still unchecked in approvals/pending.md and absent from resolved approvals.
The user's instruction explicitly conditions collection on owner approval.
Research acceptance cannot substitute for the task's 200-real-prospect metric.

At 30% raw email yield, 700 listings produce 210 candidates before deduplication
and verification. Illustratively, 80% verification retention and 85% unique-business
retention yield only 143. Those retention rates are scenarios, not observations.
Similarly, <20% yield in 300 records gives fewer than 60 emails; it does not by
itself validate the dental fallback. Report uncertainty and measured denominators.

The collection route and a capped purchasing proposal are specified in
[prospect-pipeline-plan.md](prospect-pipeline-plan.md). Stop before spending without
approval; count only distinct eligible businesses with source-backed emails and
positive verifier evidence. A catch-all result does not confirm a mailbox.
[Reoon's verification-status explanation](https://www.reoon.com/email-verifier/).

## Closing requirements for the next review

Claude corrects the scoring and evidence claims above, including per-vertical
competitor mapping. After owner approval and service access, Codex executes the
bounded US pilot and delivers the real CSV with collection/verification evidence.
TASK-002 remains unfinished until both are available. This requests evidence
corrections and the already-specified dataset, not new infrastructure or outreach.
