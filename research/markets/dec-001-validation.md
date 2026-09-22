# DEC-001 validation — market hypothesis (TASK-002)

Author: Claude (planner). Date: 2026-09-22. Status: for Codex CHALLENGE (round 1).
Question: is "US/UK local service businesses, reached by cold email, buying done-for-you monthly services" a market we can sell into self-serve, with no calls?

## Verdict

**DEC-001 is confirmed for the US and must be narrowed for the UK.**
- US: B2B cold email is lawful opt-out (CAN-SPAM), spend is real ($2,000–$10,000/month per home-service contractor), and self-serve products at $49–$159/month already sell to this segment at scale (Rosie 2,000+ SMBs; NiceJob, GatherUp, Thryv all market to home-service pros).
- UK: PECR treats sole traders and ordinary partnerships as *individual subscribers* — consent or soft opt-in required. 57% of UK businesses are sole proprietorships and construction is the largest sector (885k businesses, ~57% not even VAT/PAYE registered). So UK trades are mostly unreachable by cold email lawfully. UK stays in scope **only for limited companies/LLPs**, which in practice means dental clinics and the larger trade firms — filtered against Companies House.
- Recommended vertical: **US plumbing/HVAC contractors** (primary). Fallback: **dental clinics (US, plus UK Ltd)**.
- Proposed amendment to DEC-001 (owner-visible, evidence above): "UK: limited companies/LLPs only, verified via Companies House; no UK sole traders."

## Scoring — five verticals

Scale 1–5 per criterion. (a) findable business emails per 100 Google Maps listings, (b) existing spend on done-for-you services (3 priced competitors each — see §Competitors), (c) cold-email legal status US/UK, (d) prospect-specific sample feasible before contact.

| Vertical | (a) Email yield | (b) Spend / competitors | (c) Legal | (d) Sample | Total | Notes |
|---|---|---|---|---|---|---|
| Plumbers / HVAC (US) | 3 (~30–40% via site crawl) | 5 ($2.5k–$10k/mo; Rosie, NiceJob, Zero Degree, FlashCrafter sell to them by name) | 5 US / 2 UK | 5 (GBP review-gap audit; missed-call test; demo site) | **18** | Emergency-call economics make missed-lead and reviews high-value. |
| Dental clinics (US + UK Ltd) | 5 (practices have sites; 35% of 26k Texas dentists yielded email in one crawl) | 4 (high job value; GBP/reviews, SEO retainers $600+; crowded with agencies) | 5 US / 4 UK (mostly incorporated) | 4 (review audit, site speed/booking audit) | **17** | Buyer is a practice manager; decision slower; HIPAA rules out call-handling products. |
| Cleaning companies (US) | 3 | 3 (buy at $49–$125 tier; owner-operators, high churn) | 5 US / 2 UK | 5 | **15** | Cheap to sell, cheap to lose. |
| Landscapers / lawn care (US) | 2 (thin web presence) | 3 (seasonal; buy sites at $97–$147) | 5 US / 2 UK | 4 | **13** | Seasonality hurts MRR. |
| Auto detailing (US) | 3 | 2 (price-sensitive; Widewail at $500 targets dealers, not detailers) | 5 US / 2 UK | 5 | **12** | Good for samples, poor for $99+ subscriptions. |

UK legal score for trades is 2 because a Ltd-only filter removes most of the list; dental gets 4 because most practices are incorporated.

## Competitors with published prices (3+ per product category)

A. GBP + review management: NiceJob $75/$125; GatherUp $99 (+$40 listings); Merchynt Paige $99/location; Thryv Starter $99; BitBlaze UK £47/£99; managed human service quoted $125–$400/profile (Merchynt), ~$150/location (99Calls). Birdeye/Podium: not published.
B. Website + hosting subscription: Durable $25; B12 $24/$78; Zero Degree Media $97/$147 (trades only: roofing, HVAC, plumbing, landscaping, cleaning); FlashCrafter ~$199; UK StoreBuilder £49; Inventis from £29 (12-month contract).
C. Missed-call / AI receptionist: Rosie $49/$149/$299 (2,000+ SMBs); Smith.ai AI $150; SalesCaptain $159/location; Ruby human $250+; UK Down To Earth AI £45 + £23/channel; Softomate from £99 + £2,000 setup.
D. Local SEO content: theStacc $49/$99/$749; Verblio $49.50 + per word; Content Cucumber $590; UK Wrise £395, dotwall £179–£699. Only 3 of 12 vendors publish prices (theStacc).

Read for TASK-003: categories A and C have proven self-serve demand at exactly our $99–$300 band and are the least crowded by $25 AI builders; B is squeezed between Durable ($25) and agencies ($97–$147); D sells mainly to businesses that already have a site and an agency.

## Legal checklist (binding for DEC-003 outreach)

1. US: accurate headers and sender identity; no deceptive subject; identify as advertising; physical postal address in every email; working opt-out for 30 days; honor opt-outs within 10 business days. Penalty up to $53,088 per email. California B&P §17529.5 survives preemption (private right of action for misleading headers/subjects).
2. UK: send only to corporate subscribers (Ltd/LLP verified via Companies House API); named addresses are personal data → documented legitimate-interests assessment, privacy notice link, honor objections immediately. PECR fines now up to £17.5m/4% turnover (DUA Act 2025).
3. Excluded confirmed: Canada (CASL), Australia (Spam Act), Germany (UWG §7) all require consent.
4. Global suppression list shared across every mailbox and tool; log the source of each address; verify before sending.

## Prospect pipeline (to reach the 200-email success metric)

Google Places API returns no email; Companies House returns no email. Yield from Maps + site crawl is ~30–40%, so ~600–700 listings are needed for 200 verified emails.

1. Scrape ~700 plumbing/HVAC listings for one US metro (proposal: Houston or Phoenix — large, high AC/plumbing demand) with Outscraper (first 500 records free, then ~$3/1k, email enrichment ~$3/1k) or Apify Google Maps Email Extractor ($2.10/1k).
2. Fallback lookups for domains without an email: Hunter free tier / Apollo free tier.
3. Verify with Reoon ($11.90/10k) or MillionVerifier ($37/10k).
4. Output `research/markets/prospects-sample.csv`: business, city, state, website, email, email_source, verified (y/n), gbp_rating, gbp_reviews, has_website (y/n).
Cost: ~$15–25. Time: 2–4 hours. **Requires owner spend approval (SPEND-PROSPECTS) and a machine with network access — this is Codex execution, not research.** Claude's container cannot reach these services.

## What would reverse this decision

- Email yield below 20% on the first 300 listings → switch primary to dental (higher yield).
- Reply rate below 0.5% on the first 500 emails with a prospect-specific sample → the sample, not the vertical, is the first suspect; re-test one alternative sample before changing vertical.

## Sources

- FTC CAN-SPAM guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- CAN-SPAM preemption: https://www.law.cornell.edu/wex/inbox/can-spam_act_preemption
- ICO B2B marketing guidance: https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/
- UK Business Population Estimates 2025: https://www.gov.uk/government/statistics/business-population-estimates-2025/business-population-estimates-for-the-uk-and-regions-2025-statistical-release
- UK solo trades: https://solodesks.com/research/uk-solo-trade-statistics
- PECR penalty increase: https://www.oconnors.law/news-views/penalties-for-breaching-direct-marketing-regulations-set-to-increase/
- ICO fines 2026: https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/01/fines-of-225-000-for-nuisance-marketing-messages/
- CASL: https://crtc.gc.ca/eng/com500/faq500.htm · Australia: https://privacymatters.dlapiper.com/2024/08/australias-e-marketing-expectations-when-customers-dont-give-a-spam/ · Germany: https://www.ihk.de/nordwestfalen/recht/rechtsthemen/wettbewerbsrecht/werbung-per-telefon-telefax-oder-e-mail-3614212
- Home-service marketing spend: https://hookagency.com/blog/digital-marketing-costs-for-home-service-business/ · https://pipelineon.com/blog/marketing-spend/
- UK SEO spend: https://wrise.co.uk/blog/local-seo-uk-pricing-guide/ · https://dotwall.co.uk/blog/how-much-does-seo-cost-for-a-uk-small-business-in-2026/
- Pricing pages: https://get.nicejob.com/pricing · https://gatherup.com/pricing/ · https://www.merchynt.com/pricing · https://www.thryv.com/pricing/ · https://bitblaze.uk/review-management-service · https://durable.com/pricing · https://www.b12.io/pricing/ · https://www.zerodegreemedia.com/pricing · https://storebuilder.co.uk/trades-growth/ · https://www.inventis.co.uk/pay-monthly-website-design/ · https://heyrosie.com/pricing · https://smith.ai/pricing/ai-receptionist · https://blog.salescaptain.com/missed-call-text-back-cost-per-month-2026-guide/ · https://www.ruby.com/pricing/ · https://www.downtoearthai.co.uk/ai-receptionist-for-tradesmen · https://thestacc.com/pricing · https://www.verblio.com/pricing · https://contentcucumber.com/pricing
- Data sources: https://www.woosmap.com/blog/google-places-api-pricing · https://scrap.io/outscraper-pricing · https://apify.com/lukaskrivka/google-maps-with-contact-details · https://scrap.io/extract-emails-google-maps · https://developer.company-information.service.gov.uk/developer-guidelines · https://www.reoon.com/email-verifier/ · https://puzzleinbox.com/blog/millionverifier-pricing-guide/
