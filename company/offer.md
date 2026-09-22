# The offer (TASK-003) — one product, self-serve, done-for-you — revision 2

Author: Claude (planner). Date: 2026-09-22. Revision 2 answers REV-007 / research/markets/offer-challenge.md point by point (§8). Governs DEC-006 within DEC-007.

## 1. Decision (unchanged): candidate (b) — done-for-you website, hosted and maintained, $119/month test price

A plumber/HVAC contractor pays $119/month and gets a fast mobile-first website built from facts that are already public, live within two business days, hosted, secured, and updated by email within a defined monthly allowance. The prospect sees the finished concept before paying. $119 is a **test price** inside the observed supply band (Zero Degree $97/$147 no setup; NiceJob Sites $99 + $199 setup); it does not establish conversion. Demand evidence comes only from the pilot (DEC-007).

## 2. Scoring — four DEC-006 candidates (corrected)

| Candidate | Automation ≥70% of repeat build steps? | Sample impact | Competitor band ($99–$300 self-serve) | Delivery risk (external gates) | Total /20 |
|---|---|---|---|---|---|
| (a) GBP + reviews | 4 — replies/posts automate; review requests need the customer's job list | 3 | 5 — NiceJob $75/125 · GatherUp $99 · Merchynt $99 · Thryv $99 | 2 — Google Business Profile API needs an approved project (https://developers.google.com/my-business/content/basic-setup) | 14 |
| **(b) Website + hosting + maintenance** | **5** (repeat build steps; maintenance share unmeasured, see §6) | **5** | 4 — Zero Degree $97/147 · NiceJob Sites $99+199 · FlashCrafter ~$199 | 4 — hosting must permit commercial use; payment provider eligibility unconfirmed (§3) | **18** |
| (c) Missed-call text-back | 4 — Twilio flows automate; customer must set conditional call forwarding | 4 | 5 — Rosie $49/149/299 · Smith.ai $150 · SalesCaptain $159 | 2 — US A2P 10DLC registration and per-campaign approval; sole proprietors can register without an EIN per Twilio (https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/collect-business-info), but this owner's eligibility and TCPA consent obligations are unestablished | 15 |
| (d) Local-SEO content | 5 | 2 | 3 — theStacc $49/$99 (https://thestacc.com/pricing) · Verblio $49.50 + $0.06/word (https://www.verblio.com/pricing) · Content Cucumber $590 (https://contentcucumber.com/pricing) | 3 — needs write access to the customer's existing site/CMS | 13 |

Anchors are judgments; totals add. (c) rises to 15 after the A2P correction; (b) still leads on the two criteria that decide whether a no-call sale can happen: what the prospect sees, and whether delivery depends on a third party's approval.

## 3. External gates — stated, not assumed

- **Hosting.** GitHub Pages excludes sites that primarily facilitate commercial transactions or run an online business (https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits). Previews and customer sites will not be published there. Candidate hosts whose free tiers permit commercial use: Cloudflare Pages, Netlify. Codex verifies the current terms of the chosen host in TASK-006 session 3 and records the check; the owner creates the (free) account. Until then, previews stay local/portable (as built in session 1).
- **Payment.** Lemon Squeezy prohibits design/web-development services (https://docs.lemonsqueezy.com/help/getting-started/prohibited-products); Paddle treats primarily human-services offerings as a poor fit and reviews the product/domain (https://www.paddle.com/help/start/intro-to-paddle/what-am-i-not-allowed-to-sell-on-paddle). **Provider: unspecified.** Interface stays provider-agnostic (one checkout URL + one signed webhook). Owner decision needed, with two candidate paths for the owner to check eligibility: (i) a merchant-of-record application describing the product as a hosted website platform subscription, subject to that provider's review; (ii) a Saudi payment gateway under the owner's existing commercial registration that accepts international cards in USD (e.g., Tap Payments, Moyasar, PayTabs — eligibility, fees and payout terms to be confirmed by the owner). No tax-handling promise is made until a provider is accepted.
- **Content rights.** Previews use only facts verified on the business's own website plus name, city, phone and category; no third-party review text, no ratings copied, no photos from Google or the business site; original illustrations only; a link "see reviews on Google" instead of copied reviews. Every preview states it is an unsolicited, independent concept, not the official site (implemented in session 1). After purchase, photos and any testimonial text come from the customer, who confirms they own or may use them.

## 4. The offer, as it will appear on the landing page (narrowed to what v1 implements)

**"Your new website, built from what's already public about your business. Live in two business days. $119/month. Cancel anytime."**

Included every month:
- Mobile-first site: services, service area, hours (once confirmed by the customer), click-to-call, contact form whose submissions are forwarded to the owner's email (form backend chosen in TASK-007; no delivery-time promise beyond "forwarded automatically").
- Hosting on a commercial-use host, HTTPS, weekly site export kept 30 days.
- **Updates: up to 5 requests per month, each up to 30 minutes of work, completed within 2 business days.** Small = text, hours, prices, adding/removing a service, swapping customer-supplied photos. Larger changes are quoted separately or declined.
- Monthly email with visits and form submissions (cookie-free analytics, e.g. Cloudflare Web Analytics).
- Domain: customer's existing domain connected with a one-page instruction for their DNS provider (records vary by provider); until then the site runs on a subdomain of ours.

Not included: SEO campaigns, ads, logo design, copywriting interviews, e-commerce, phone answering, uptime guarantees beyond the host's own.

Launch clock: **2 business days (Mon–Fri, US Central)** from the later of (a) payment and (b) the customer's confirmation email (domain choice, corrections, photo consent). Refund rule: if the site is not live on the subdomain within **5 business days** of that same start, the first month is refunded automatically; otherwise cancellation is the only remedy, effective end of the paid month, with a zip export delivered.

Preview expiry: 14 days; at expiry the deployment is **removed** (not just bannered) by the deploy script.

## 5. The sample (built before contact) — implemented in TASK-006 session 1

Input: name, city, phone, category, services and source URL verified on the business's own site. Output: one static site, three deterministic styles, noindex, expiry banner, disabled buy button until a checkout URL exists. Measured local render: sub-second per site (session-1-results.json). **Hypothesis, not measured:** end-to-end ≤4 minutes per prospect including manual fact verification; 200 prospects = 400–800 minutes of mostly verification work unless TASK-005 data reduces it. This is the real cost of the sample and is reported per batch, not assumed.

## 6. Unit economics (hypotheses until measured)

Target 10,000 SAR ≈ $2,670 → 23 customers at $119. $119 less an assumed 5% + $0.50 provider fee = $112.55 before hosting (~$0 on free tiers), support time, compute and refunds; realized margin is unknown until 10 customers and one month of update requests are logged. Maintenance automation ≥70% is a target verified by a timed trial of a bounded request mix in TASK-007, not a claim.

Outreach volume: DEC-003 mailbox caps count sends, not unique prospects; a 3-email sequence reaches roughly one third as many prospects as the send cap. Pilot reporting uses unique prospects contacted.

## 7. Product boundary

DEC-007 governs vertical and time-box. Reversal triggers here are **recommendations to the owner**, not automatic changes: reply rate <0.5% on the first 500 unique prospects → change the email/sample first; <2 paying customers after 1,500 unique prospects → Claude re-scores (a) and reports; the owner decides.

## 8. Changes from revision 1 (answers to REV-007)

1. Hosting: GitHub Pages ruled out for sales assets; commercial-use host to be verified by Codex; previews stay local until then.
2. Payment: provider unspecified; two eligibility paths for the owner; tax promise removed.
3. Content: reviews, ratings and photos removed from previews; original artwork; customer-supplied media after purchase.
4. Promises narrowed: one launch clock with timezone and start conditions; refund trigger defined; updates bounded (5/month, ≤30 min, 2 business days); no 1-minute form promise; DNS wording generalized; expiry = removal.
5. A2P statement corrected; (c) rescored 14 → 15; third linked content competitor added.
6. 2–4 minute, 90% margin and ≥70% maintenance figures labeled hypotheses with the measurement that would settle each.
7. Reversal triggers reframed as owner recommendations under DEC-007.
