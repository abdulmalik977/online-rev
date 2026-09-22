# TASK-003 — Codex review, round 1

Reviewed 2026-09-22 against `cbbad8a`. Verdict: **CHANGES REQUESTED**.
Product (b), a generated website with maintenance, is technically feasible and a
reasonable bounded pilot at $119. This is not approval of the public promises,
provider eligibility, or the unmeasured automation/maintenance assumptions.
Proceed with the owner's requested TASK-006 local generator; publication and
checkout remain dependent on the specific corrections below. TASK-005 stays deferred.

## Blocking corrections, scoped to the current offer

1. **Hosting and payment are real external gates.** GitHub Pages explicitly excludes
   sites primarily facilitating commercial transactions or running an online business.
   The proposed ten buy-button previews are sales assets, not a neutral code demo.
   Do not deploy this sales path to Pages on the assumption that static means allowed.
   Produce portable static files now and select suitable hosting before publication.
   [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
   Lemon Squeezy explicitly prohibits services including design/web development.
   Paddle says a primary human-services/design offering is not a good fit and requires
   product/domain review. Automation does not establish eligibility for this offer.
   Keep payment provider unspecified until the actual product is accepted; retain the
   provider-agnostic interface, without promising either provider or its tax handling.
   [Lemon Squeezy policy](https://docs.lemonsqueezy.com/help/getting-started/prohibited-products),
   [Paddle policy explanation](https://www.paddle.com/help/start/intro-to-paddle/what-am-i-not-allowed-to-sell-on-paddle).

2. **Public content is not a reuse license.** The preview spec copies review text and
   photos into persistent static sites/exports. Attribution alone does not authorize
   that. Google Maps terms restrict copying except where permitted; Places API rules
   also restrict storage and require source/author attribution. API rules apply to API
   content, not automatically to every independently collected fact. Use basic facts
   independently verified on business websites, link to Maps, and omit third-party
   reviews/photos until reuse rights and the acquisition path are documented. A photo
   appearing on a business website is not itself proof of a reusable license. Preview
   branding must state it is an unsolicited concept, not the business's official site.
   [Maps terms](https://www.google.com/help/terms_maps/),
   [Places policies](https://developers.google.com/maps/documentation/places/web-service/policies).

3. **Promises exceed the v1 implementation and conflict.** A static host cannot by
   itself email a form lead within one minute. No chosen form service, delivery queue,
   uptime measurement, backup restore, update capacity or analytics exists yet.
   "48 hours" and "48 h business time" differ; define one launch clock, timezone,
   missing-input/DNS exceptions and the five-business-day refund trigger. DNS records
   vary by provider: do not promise exactly two. Define "small update" and an operating
   capacity bound before promising unlimited next-day work. A banner/noindex does not
   remove an expired page; require removal/replacement in deployment. Local previews
   must not expose a form that pretends to send. Narrow unimplemented promises now;
   this review does not request building new monitoring/payment infrastructure.

4. **Success metric and economic evidence are incomplete.** Each candidate needs
   three linked priced competitors; the content row has only two named providers,
   one without a numeric quote. Several others have names/prices but no direct source.
   All table totals (14/18/14/13) add correctly; scoring anchors are still judgments.
   Label the 2–4 minute end-to-end figure and 90% margin as hypotheses until measured.
   $119 less the assumed 5%+$0.50 fee leaves $112.55 (94.58%) **before** hosting,
   support, compute and refunds; it does not establish realized gross margin. 200
   previews at 2–4 minutes is 400–800 minutes unless a demonstrated batch process
   changes that denominator. Three-email sequences consume three sends per prospect;
   mailbox capacity is not unique-prospect volume. Keep the DEC-007 60-day vertical
   decision and product boundary authoritative; do not silently replace it with a
   different product reversal after 1,500 emails.

## Price and candidate findings

Keep **$119 as a test price**. Zero Degree publishes $97/$147 with no setup, while
NiceJob Sites publishes $99/month plus $199 setup. Their first-year totals are
$1,164/$1,764 and $1,387 respectively; ours is $1,428 with zero setup. Thus $119 sits
within observed supply prices. These offers do not prove conversion or select $99
versus $149. Zero Degree also describes a call and 7–14-day launch, so it does not
substantiate our faster no-call SLA. [Zero Degree](https://www.zerodegreemedia.com/pricing),
[NiceJob](https://get.nicejob.com/pricing). Sources checked 2026-09-22.

GBP API approval is a real gate: [Google setup](https://developers.google.com/my-business/content/basic-setup).
The blanket A2P claim that every registrant requires a US entity/EIN is inaccurate:
Twilio documents sole-proprietor registration for eligible US/Canadian businesses
without an EIN. That does not establish this owner's eligibility or remove campaign
approval/consent requirements. Correct the statement without changing the chosen
website product. [Twilio registration](https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/collect-business-info).

## Written estimate and automation boundary (at most five sessions)

| Session | Deliverable / exit check |
|---|---|
| TASK-006 1 of 3 | Schema, sourced ten-business fixture, deterministic templates/three styles, local build, claim/escaping tests, timings |
| TASK-006 2 of 3 | Visual/mobile QA, source corrections, expiry packaging and host handoff |
| TASK-006 3 of 3 | Approved-host deployment and ten live checks, or explicit external blocker; no fourth session |
| TASK-007 1 of 2 | Landing/config, provider-neutral signed fake event, idempotent order record/promotion tests |
| TASK-007 2 of 2 | End-to-end QA, welcome/opt-out artifacts, deployment after host resolution |

The estimate covers a constrained v1, not every unbounded SLA in the current offer.
No new infrastructure task is needed. Automated CSV validation, normalization,
template population, build, expiry selection and package generation can cover more
than 70% of **repeat build steps**. This is a feasibility judgment, not a measured
labor percentage for build plus maintenance. Record acquisition/rights review, QA,
DNS and exception time separately. Maintenance >=70% needs a bounded request mix
and timed trials; it cannot honestly be confirmed for unlimited arbitrary requests.
TASK-006 will measure local render time separately from manual research/deploy time.

No --attempt on Claude's TASK-003, no outreach, and no provider signup or purchase.
