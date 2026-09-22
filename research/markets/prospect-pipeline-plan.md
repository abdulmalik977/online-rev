# TASK-002 — prospect collection ready for approval

Prepared 2026-09-22. **Not executed. SPEND-PROSPECTS remains pending.**
Proposed pilot: plumbing/HVAC businesses in the Houston, Texas metro; one metro
throughout. Use Outscraper listings + site/email enrichment, then Reoon verification.
The owner cap is **US$25 total**, including top-ups, fees and tax, not $25 per tool.
No recurring subscription, outreach, calls, messages, or new infrastructure.

## Purchasing basis

Outscraper's published schedule offers the first 500 listing records free and
$3/1,000 thereafter; site/contact enrichment separately lists 500 free domains and
$3/1,000 thereafter. For 700 of each, estimated usage is $1.20 if both free allowances
are available, or $4.20 if already exhausted. These are usage estimates, not a
confirmed checkout/top-up amount. [Outscraper pricing](https://outscraper.com/pricing/).

Reoon lists a one-time 10,000-credit package at $11.90 (its heading rounds to $12),
plus limited free credits. Listed combined usage/package estimates are therefore
$13.10–$16.10 before taxes, minimum top-ups and fallback lookups. Check actual account
allowances and checkout totals before any payment; stop if the remaining $25 cap
cannot cover it. [Reoon pricing](https://www.reoon.com/email-verifier/).

Required execution inputs: explicit owner approval and authorized access to the
Outscraper/Reoon accounts (signed-in browser or locally configured credentials).
Credentials must not be pasted into research files, logs, chat, or Git.
Hunter/Apollo may be used only within an available free allowance; no upgrades.

## Execution and stopping rules

1. Record consent-to-spend, account quotes and remaining budget before purchasing.
   Extract an initial batch of up to 300 raw listings, using plumbing/HVAC queries
   in the same metro. Keep query, retrieval time, place ID and original source.
2. Remove closed/out-of-area/non-target listings; deduplicate place IDs and then
   business/domain/email identities. Do not count branches sharing one email as
   multiple independently reachable prospects. Retain raw counts for yield analysis.
3. Use business websites/contact pages for email provenance; do not invent address
   patterns. If enrichment lacks a source page, inspect the public company site.
   Free fallback lookups remain subject to the same provenance and eligibility checks.
4. Submit candidates to Reoon. Retain its status and verification timestamp. Set
   verified=y only for confirmed mailbox-valid results without catch-all/invalid/
   unknown/disposable/spam-trap flags; valid shared business inboxes may qualify.
   The verifier says it checks without sending email; no outreach is part of this
   pipeline. Verification is point-in-time evidence, not a guarantee against bounces.
   [Reoon verification details](https://www.reoon.com/email-verifier/).
5. Measure raw and verified yield after the pilot. Below 20% triggers the study's
   fallback decision, but the existing spend approval covers plumbing/HVAC only:
   report the shortfall and obtain a revised scope before spending on dental.
6. Continue within the original approximately 700-listing envelope and $25 cap until
   200 distinct eligible, verified businesses are available. If those bounds do not
   produce 200, preserve the genuine partial results and report the measured gap;
   never pad with duplicates, guessed emails, or fabricated verification.

## Deliverable and checks

Final path: `research/markets/prospects-sample.csv`, UTF-8 with these exact columns:

```text
business,city,state,website,email,email_source,verified,gbp_rating,gbp_reviews,has_website
```

Require at least 200 unique eligible businesses and unique usable emails, populated
source URLs, state=TX, consistent y/n fields, valid rating/review-count values when
available, and vendor-backed verified=y. Missing ratings stay blank, never invented.
Preserve provider receipts, raw statuses and rejection counts for an audit summary.
The CSV is not created as a placeholder now; its existence must represent real data.
Collection approval does not resolve DEC-001-AMEND or authorize any customer contact.
