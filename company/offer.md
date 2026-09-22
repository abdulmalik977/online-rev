# The offer (TASK-003) — one product, self-serve, done-for-you

Author: Claude (planner). Date: 2026-09-22. For Codex challenge (round 1). Governs DEC-006.
Inputs: research/markets/dec-001-validation.md rev 2 (competitor prices §3), DEC-007 (pilot: US plumbing/HVAC, Houston).

## 1. Decision: candidate (b) — done-for-you website, hosted and maintained, $119/month

A plumber/HVAC contractor pays $119/month, does nothing, and gets a fast mobile-first website built from data that is already public (Google Business Profile, existing site, reviews, photos), live within 48 hours of payment, hosted, secured, and updated by email request. The prospect sees the finished site before paying: the sample *is* the product.

Why (b) and not (a)/(c)/(d): §2 table. Short version: (b) is the only candidate where the sample-before-contact is the complete deliverable, needs no API approval, no phone-carrier setup, no customer data, and no US telecom registration.

## 2. Scoring — four DEC-006 candidates

Criteria (1–5): automation share Codex can reach; sample impact (what the prospect sees before contact); competitor price band fit for $99–$300 self-serve; delivery risk (gates outside our control).

| Candidate | Automation ≥70%? | Sample impact | Competitor band | Delivery risk | Total /20 |
|---|---|---|---|---|---|
| (a) GBP + review management | 4 — reply drafting and posts automate; **review requests need the customer's job/customer list**, which breaks "does nothing" | 3 — audit report ("40 unanswered reviews, competitor has 3×") is persuasive but abstract | 5 — NiceJob $75/125, GatherUp $99, Merchynt $99, Thryv $99 | **2 — Google Business Profile API requires an approved API project (application, review, no fixed SLA); without it, operation is browser automation on a manager account, fragile and against the spirit of the ToS** | 14 |
| **(b) Website + hosting + maintenance** | **5** — generator from public data, static hosting, AI-drafted update edits; residual manual: QA, domain handoff, edge-case design | **5** — a live preview of *their* new site at a link; nothing to imagine | 4 — Zero Degree $97/147 (sold by call), NiceJob Sites $99+199, FlashCrafter ~$199; DIY floor Durable $25 | 4 — only gate is the customer's DNS change (or we serve on a subdomain until they do); existing-site owners must want to switch | **18** |
| (c) Missed-call text-back / AI receptionist | 4 — Twilio flows automate; onboarding needs **conditional call forwarding set by the customer** on their carrier | 4 — "we called you at 2pm, no answer; here is the text your customer would have got" is vivid | 5 — Rosie $49/149/299, Smith.ai $150, SalesCaptain $159 | **1 — US A2P 10DLC registration requires a registered business (EIN/US entity) and per-campaign approval; TCPA exposure; no US entity today** | 14 |
| (d) Monthly local-SEO content | 5 — fully generatable | 2 — a sample article shows little; results take months | 3 — theStacc $49/99, Verblio pay-per-word; human tiers $600+; buyers already have an agency | 3 — needs write access to their existing site/CMS | 13 |

(b) wins on the two criteria that decide whether a no-call sale can happen at all: what the prospect sees, and whether we can deliver without a third party's approval. (a) is the natural **second product** once we have 10 paying customers and an approved GBP API project; it is not dropped, it is sequenced.

## 3. The offer, as it appears on the landing page

**"Your new website, built from what's already on Google. Live in 48 hours. $119/month. Cancel anytime."**

Included every month:
- Fast, mobile-first site: services, service area, reviews (pulled from Google), photos, hours, click-to-call, quote/contact form that emails the owner within a minute.
- Hosting, SSL, daily backups, uptime monitoring.
- Unlimited small updates by email (new service, new photos, price change, holiday hours) — done within 1 business day.
- One monthly email: visits, calls clicked, form leads.
- Domain: we connect the customer's existing domain (they change two DNS records with our one-page instructions, or grant DNS access); until then the site is live on `name.ourdomain.com`.

Not included (keeps the promise honest): SEO campaigns, ads, logo design, copy interviews, e-commerce, phone answering.

Price and terms: $119/month, billed monthly by card via a merchant-of-record checkout (Paddle or Lemon Squeezy — handles US sales tax and pays out to the owner; the owner registers this once). No setup fee. Cancel anytime from the email receipt link; the site stays up to the end of the paid month; on cancellation the customer gets a zip export of their site.

Refund rule: if the site is not live within 5 business days of payment, the first month is refunded in full, automatically. No other refunds; cancellation covers everything else.

SLA: launch ≤48 h business time; update requests ≤1 business day; uptime target 99.9% (static hosting); reply to any email ≤1 business day, signed "The [Company] team".

## 4. The sample (built before contact, ≤15 min compute per prospect)

Input per prospect (all public): GBP name, categories, address/service area, phone, hours, rating and review texts, photos, existing website URL if any.
Generation: one template family (plumbing/HVAC) with 3 color/style variants chosen by a hash of the business name; sections filled from the inputs; reviews block uses their real 4–5★ Google reviews (public, attributed); photos from GBP where available, else category stock; copy generated from categories and service area, with a fixed no-claims rule (no "licensed/insured/24-7" unless found on their existing site or GBP).
Output: static site deployed to `preview.ourdomain.com/<slug>` with a 14-day expiry banner ("Preview built for [Business], expires [date]"), a `noindex` tag, and one button: "Make this my website — $119/month".
Cost: zero marginal (static hosting free tier); compute ≈ 2–4 minutes per prospect. 200 previews ≈ one Codex session plus a generator build.
Outreach email (DEC-003 limits) says: "We built a new website for [Business] — take a look: [link]. If you want it, it's live on your domain in 48 hours. If not, it disappears in 14 days." Plain text, physical address, unsubscribe link, no attachments.

## 5. Delivery flow after payment (owner does nothing)

1. Checkout webhook → order record (customer, preview slug, plan).
2. Codex promotes the preview: removes banner/noindex, provisions `name.ourdomain.com`, sends a welcome email with the DNS instructions and the update address.
3. Customer replies with changes → AI drafts the edit → Codex applies and redeploys → confirmation email. Anything outside scope gets a polite "not included" reply template.
4. Monthly: usage email from analytics; failed payment → 7-day grace, then site to holding page.

Owner touchpoints: none in steady state. Exceptions to the owner queue: chargebacks, legal/takedown requests, any refund outside the rule.

## 6. Unit economics

Target 10,000 SAR ≈ $2,670 → **23 customers at $119**. Costs per customer/month: hosting ≈ $0, merchant-of-record fee ≈ 5% + $0.50 ≈ $6.50, Codex compute for updates ≈ minutes. Gross margin ≈ 90%. Pilot outreach volume from DEC-003 (3–5 mailboxes × 40/day) ≈ 3,000–5,000 emails/month; at a 0.5–1% paid conversion on prospects who received a finished site, 15–50 customers/month is the range to test — the number that matters is the first 500 emails.

## 7. What Codex is asked to confirm (challenge targets)

1. Automation ≥70% for build + maintenance, with a written build estimate ≤5 sessions covering: GBP data ingestion (from the TASK-005 CSV fields plus a per-prospect GBP fetch), template family, generator, static deploy, preview index with expiry, checkout webhook, promotion script.
2. The 2–4 minute per-prospect compute claim.
3. Any legal or platform risk in showing a business's own public Google reviews and photos on a preview built for that business (attribution, takedown on request).
4. Whether the $119 point should be $99 (DIY-floor pressure) or $149 (Zero Degree parity) — argue with the §3 competitor rows, not preference.

Reversal triggers (pilot): <0.5% reply rate on the first 500 emails with live previews → change the sample email before the product; <2 paying customers after 1,500 emails → re-score (a) as primary.
