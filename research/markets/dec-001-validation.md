# DEC-001 validation — market hypothesis (TASK-002), revision 2

Author: Claude (planner). Date: 2026-09-22. Revision 2 answers REV-005 (Codex challenge) point by point; §7 lists what changed.
Question: is "US/UK local service businesses, reached by cold email, buying done-for-you monthly services self-serve" a market we can sell into with no calls?

## 1. Verdict (hypothesis, with the evidence class stated)

- **US plumbing/HVAC contractors: primary pilot.** Supported by supply-side evidence (vendors publish prices, sell by trial/signup, and name the vertical) and by a lawful opt-out email channel. Demand evidence — that these owners buy *our* offer by email without a call — does not exist yet and is produced only by the pilot (§6).
- **Fallback: US cleaning companies**, not dental (changed from revision 1). Dental's buying norm is demo-led, which conflicts with DEC-002; see §2 criterion (e).
- **UK: conservative operational filter** — corporate subscribers only, implemented as Ltd/LLP matched via Companies House. This is a policy proposal for the owner (DEC-001-AMEND, pending); it is narrower than the ICO's legal definition, which also covers Scottish partnerships and other corporate bodies. Whether most UK dental practices or trade firms are incorporated is **unmeasured**; the filter does not depend on that claim.
- Words "confirmed" and "proven demand" from revision 1 are withdrawn.

## 2. Scoring — aggregation rule and recomputed table

Rule: US-only comparison; every US row uses the same US legal score. UK is reported in one separate line. Five criteria, 1–5 each, max 25. Yield criterion is a hypothesis for every vertical (see bins) until the pilot measures it.

Criteria:
- (a) Verified-email yield per 100 Maps listings. Bins: 5 ≥50% · 4 40–49% · 3 30–39% · 2 20–29% · 1 <20%. **No vertical has a matched measurement.** The one datapoint is vendor-reported (Scrap.io: 9,166 of 26,376 Texas dentist listings had an email, 34.75%, indexed data, unverified). All five verticals are therefore scored 3 (H) and yield does not discriminate until measured.
- (b) Existing spend on done-for-you services with priced competitors in the vertical (§3). 5 = DFY product in the $99–$300 band with no large setup fee plus agency tier above; 3 = DFY exists but thin or price-sensitive; 2 = DFY absent or only outside the band.
- (c) Cold-email legal status, US (§4). 5 for all US rows.
- (d) Prospect-specific sample feasible before contact, ≤15 min compute (GBP review-gap audit, missed-call test, demo page).
- (e) **Self-serve buying norm** — do vendors in this vertical sell by signup/trial (5) or by demo/quote (1)? Direct evidence for DEC-002 compatibility. From §3.

| Vertical (US) | (a) yield | (b) spend | (c) legal | (d) sample | (e) self-serve norm | Total /25 |
|---|---|---|---|---|---|---|
| Plumbing / HVAC | 3 (H) | 5 | 5 | 5 | 5 (Rosie, Housecall Pro, NiceJob: trial/signup) | **23** |
| Cleaning | 3 (H) | 3 | 5 | 5 | 5 (ZenMaid, Launch27, BookingKoala: signup) | **21** |
| Auto detailing | 3 (H) | 3 | 5 | 5 | 5 (Urable, Siimple: signup) | **21** |
| Landscaping / lawn | 3 (H) | 3 | 5 | 4 | 4 (Jobber signup; LMN, Service Autopilot demo-led) | **19** |
| Dental clinics | 3 (H) | 4 | 5 | 4 | 2 (Weave, Podium, NexHealth, Doctible, ProSites: demo/quote; only DocSites/PatientGain publish, with $2k+ setup or $799+ bundles) | **18** |

UK line: same criteria, legal (c) = 3 for all trades after the Ltd/LLP filter (list shrinks by an unmeasured but large share; 57% of all UK businesses are sole proprietorships, an aggregate not a trade-level figure) and 4 for dental (unmeasured incorporation share; treated as a hypothesis). UK is not the pilot.

Tie-break note: cleaning and detailing tie at 21; cleaning is the fallback because its pipeline, sample and product are identical to plumbing/HVAC (home services, GBP-driven), so a switch costs nothing. Detailing's DFY band is thinner ($49 Cannone + $199 setup; $297 Detailer Systems).

## 3. Priced competitors per vertical (3+ each, primary sources checked 2026-09-22)

n/p = not published. DIY = customer operates software; DFY = vendor does the work.

**Plumbing / HVAC**
| Vendor | $/mo | Setup | DIY/DFY | Self-serve | Source |
|---|---|---|---|---|---|
| Rosie AI receptionist | 49 / 149 / 299 | none, 7-day trial | DIY | Yes | https://heyrosie.com/industries/plumbing · /pricing |
| Zero Degree Media (website+maintenance) | 97 / 147 | $0, no contract | DFY | No (call; 7–14 day launch) | https://zerodegreemedia.com/pricing |
| Housecall Pro | 79 / 189 / 329 | trial | DIY | Yes (top tier demo) | https://www.housecallpro.com/plumbing/ |
| NiceJob (reviews; "Sites") | 75 / 125; Sites 99 + 199 setup | see left | DIY / DFY | Yes | https://get.nicejob.com/pricing |
| Hook Agency | 1,000–4,000+ per service | n/p | DFY | No | https://hookagency.com/pricing/ |
Read: a DFY product at $97–$147 exists and is sold by call; the same category has an agency tier at $1,000+. Our gap: DFY at the low band, sold without the call.

**Dental**
| Vendor | $/mo | Setup | DIY/DFY | Self-serve | Source |
|---|---|---|---|---|---|
| Weave | from 199 (tiers n/p) | n/p | DIY | No (demo) | https://www.getweave.com/industry/dentistry/ |
| DocSites | 89 | 1,999–3,999 | DFY | No (assessment call) | https://www.docsites.com/web-designs/ |
| PatientGain | 149–499 à la carte; bundles 799+ | 0 on bundles | DFY | Partial | https://www.patientgain.com/pricing-medical-digital-marketing |
| Podium, Birdeye, NexHealth, Swell, Doctible, RevenueWell, ProSites, Great Dental Websites, Wonderist | n/p | — | — | No (demo/quote) | vendor pricing pages |
Read: only three publish; no DFY product at $99–$300 without a large setup fee. Buying norm is demo-led → (e) = 2.

**Cleaning**
| Vendor | $/mo | Setup | DIY/DFY | Self-serve | Source |
|---|---|---|---|---|---|
| ZenMaid | 19 / 39 / 49 | none | DIY | Yes | https://get.zenmaid.com/pricing |
| Launch27 | 75 / 150 / 299 | n/p | DIY | Yes | https://launch27.com/pricing/ |
| BookingKoala | 27 / 57 / 197+ | none | DIY | Yes | https://www.bookingkoala.com/pricing/ |
| Jobber (cleaning page) | 39–599 | none | DIY | Yes | https://www.jobber.com/industries/cleaning (prices via third-party 2026 write-up; jobber.com blocked fetch) |
| Zero Degree Media | 97 / 147 | 0 | DFY | No | https://zerodegreemedia.com/pricing (cleaning listed) |
Read: crowded DIY low end; DFY at band exists but thin → (b) = 3.

**Landscaping / lawn care**
| Vendor | $/mo | Setup | DIY/DFY | Self-serve | Source |
|---|---|---|---|---|---|
| Jobber (landscaping page) | 39–599 | none | DIY | Yes | https://www.getjobber.com/industries/landscaping-software/ |
| LMN (Granum) | 297 / 648 | onboarding fee n/p | DIY | No (demo) | https://granum.com/lmn/pricing |
| Service Autopilot | 49 / 199 / 499 | setup fee n/p | DIY | Demo-led | https://www.serviceautopilot.com/pricing/ |
| Zero Degree Media (landscaping page) | 97 / 147 | 0 | DFY | No | https://www.zerodegreemedia.com/landscaping-websites |
| Urable | 70 / 110 / 183 | none | DIY | Yes | https://www.urable.com/pricing |

**Auto detailing**
| Vendor | $/mo | Setup | DIY/DFY | Self-serve | Source |
|---|---|---|---|---|---|
| Urable | 70 / 110 / 183 | none | DIY | Yes | https://www.urable.com/pricing |
| Cannone Marketing (site + GBP mgmt) | 49 | 199 | DFY | No | https://cannonemarketing.com/web-design-for-auto-detailers |
| Detailer Systems | 297 (+997 ads tier) | 0 | DFY | No (call) | https://detailersystems.com/pricing |
| Siimple | 10 | none | DIY | Yes | https://getsiimple.com/for-auto-detailers/ |

Spend benchmark, stated with its limits: Hook Agency and PipelineOn describe contractor marketing budgets stratified by revenue ($2,000–$10,000/month for $500k–$1M+ firms). This is a category-level range from two agency sources, not a measured distribution of our prospects, and it says nothing about willingness to buy our specific offer.

## 4. Legal (binding for DEC-003)

US — CAN-SPAM is opt-out and the FTC states it makes no exception for B2B. Requirements: accurate headers and sender identity; no deceptive subject; identify as advertising; physical postal address; working opt-out for 30 days; honor opt-outs within 10 business days; liability extends to contractors. Penalty up to $53,088 per email. CAN-SPAM preempts state law except fraud/deception statutes; California B&P §17529.5 (misleading headers/subjects) carries a private right of action. This is a *conditional* compliant channel, not unrestricted permission.

UK — PECR: corporate subscribers (companies, LLPs, Scottish partnerships, other corporate bodies) need no consent for email; sole traders and ordinary partnerships are individual subscribers and need consent or soft opt-in; unknown types are treated conservatively. Named addresses are personal data under UK GDPR → documented legitimate-interests assessment, privacy notice, immediate honoring of objections. Maximum PECR fine now £17.5m / 4% turnover (DUA Act 2025). ICO guidance is flagged as under review after the DUA Act. Our operational filter (Ltd/LLP via Companies House) is narrower than the law; identity must be matched to the actual contact.

Excluded, consent-required: Canada (CASL), Australia (Spam Act 2003), Germany (UWG §7).

HIPAA (dental, corrected from revision 1): third-party processing of PHI is permitted under a business-associate agreement and safeguards; it is an implementation and liability burden, not a ban. It counts against dental in (d) and in product choice, not as an exclusion.

## 5. Prospect pipeline and the 200-email gate (Codex executes after approval)

Google Places returns no email field (websiteUri, phone only); Companies House returns no email. Email discovery is a separate crawl step.

Denominators to report separately: listings retrieved → unique businesses (place ID, then domain/email identity) → emails located with source page → verifier-valid emails (exclude catch-all/unknown/invalid/disposable) → distinct eligible businesses.

Scenario math (scenarios, not observations): at 30% located-email yield, 80% verifier retention and 85% uniqueness, 700 listings → ~143 usable. To reach 200 the envelope is **~1,000 listings** (→ ~204). Cost at published rates: Outscraper 1,000 listings ($3/1k after 500 free) + enrichment ($3/1k after 500 free) ≈ $1.50–$6.00; Reoon 10k credits $11.90; total ≈ $13–$18, within the $25 cap in SPEND-PROSPECTS. Codex's execution plan (prospect-pipeline-plan.md) governs; amend its envelope from 700 to 1,000 listings.

If the first 300 listings yield <20% located emails, report the measured denominators and stop; a switch to the cleaning fallback needs a revised approval because SPEND-PROSPECTS covers plumbing/HVAC only.

## 6. What the pilot must measure (demand evidence, absent today)

Emails sent → replies → sample views → paid, per DEC-003 limits. Decision thresholds: reply rate <0.5% on the first 500 emails with a prospect-specific sample → change the sample first, vertical second. Nothing in this document substitutes for these numbers.

## 7. Changes from revision 1 (answers to REV-005)

1. Aggregation rule defined; US-only totals recomputed; UK reported as a separate line. Revision-1 totals were inconsistent (mixed UK/US legal scores) — acknowledged.
2. Yield bins defined; all five verticals scored 3 (H) because no matched measurement exists; the Texas dental figure is labeled vendor-reported and unverified.
3. Competitors mapped per vertical (3–5 each) with setup, DIY/DFY, and sales motion; "confirmed"/"proven" withdrawn.
4. New criterion (e) self-serve buying norm, sourced from the same tables; it moves dental to last and cleaning to fallback.
5. UK claims narrowed: filter is operational, not the legal definition; incorporation shares unmeasured; DEC-001-AMEND left pending.
6. HIPAA statement corrected to implementation risk.
7. Listing envelope raised to ~1,000 with denominators and scenario math stated; CSV remains the completion gate.

## Sources

FTC CAN-SPAM guide https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business · preemption https://www.law.cornell.edu/wex/inbox/can-spam_act_preemption · Cal. B&P §17529.5 private action https://kleinmoynihan.com/private-right-of-action-for-california-email-statute-violations/ · ICO B2B https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/ · UK BPE 2025 https://www.gov.uk/government/statistics/business-population-estimates-2025/business-population-estimates-for-the-uk-and-regions-2025-statistical-release · PECR penalties https://www.oconnors.law/news-views/penalties-for-breaching-direct-marketing-regulations-set-to-increase/ · ICO fines Jan 2026 https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/01/fines-of-225-000-for-nuisance-marketing-messages/ · CASL https://crtc.gc.ca/eng/com500/faq500.htm · Australia https://privacymatters.dlapiper.com/2024/08/australias-e-marketing-expectations-when-customers-dont-give-a-spam/ · Germany https://www.ihk.de/nordwestfalen/recht/rechtsthemen/wettbewerbsrecht/werbung-per-telefon-telefax-oder-e-mail-3614212 · HHS business associates https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html · Places schema https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places · Scrap.io dentists https://scrap.io/extract-emails-google-maps · Outscraper https://outscraper.com/pricing/ · Reoon https://www.reoon.com/email-verifier/ · Companies House API https://developer.company-information.service.gov.uk/developer-guidelines · spend benchmarks https://hookagency.com/blog/digital-marketing-costs-for-home-service-business/ · https://pipelineon.com/blog/marketing-spend/ · vendor pricing pages as linked in §3.
