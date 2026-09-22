---
id: "TASK-006"
title: "Sample site generator v1 (the product) from public business data"
owner: "codex"
status: "doing"
goal: "Build the generator that turns one prospect's public Google Business Profile data into a finished, deployed preview website, per company/offer.md section 4"
evidence: "REV-008 TASK-003 PASS; generator/session-2-results.json; generator/qa/session-2/; generator/sources.md; generator/expiry_bundle.py; generator/README.md; local active/expiry bundles; remote deployment pending session 3"
definition_of_done: "generator/ directory with: input schema (CSV row -> JSON), one template family with 3 style variants, generator script, static output, deploy script to GitHub Pages at previews/<slug>/, expiry banner and noindex, buy button reading CHECKOUT_URL from env; test set of 10 real Houston plumbing/HVAC businesses collected by hand from Google Maps (public data, no scraping accounts) in generator/testset.csv; 10 previews live; README with run command; measured compute time per prospect"
success_metric: "10 of 10 test previews build and deploy without manual edits; median build time <= 4 minutes per prospect; no copy claim not present in source data (checked by a grep list); Claude PASS via --review"
attempts: 2
review_round: 0
quota_budget: 60
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-22T20:36:35+00:00"
---
Starts after TASK-003 review (product confirmed). Budget: at most 3 sessions for v1.
Reviewer: claude. No outreach. Do not fetch photos in a way that violates Google terms:
use the public GBP page and the business's own website only; stock fallback otherwise.
The 10 test previews double as the first real samples for outreach once TASK-008 is ready.

Session 1/3 started after REV-007 per explicit owner instruction. Product family is feasible; commercial promises are not passed. Local generator work proceeds; live sales previews require suitable hosting and source rights. See generator/design.md and research/markets/offer-challenge.md.

## Session 1 result
Implemented local CSV-to-JSON/static generator, three styles, original artwork, safe URLs/HTML escaping, no-claims allowlist, noindex, 14-day expiry rebuild, disabled-by-default CHECKOUT_URL button, and allowlisted deployment ZIP packaging. Nine tests passed; 10/10 previews built without manual edits; 20 browser layout checks passed at 390/1440 px. Local total build 0.0126 s, median render 0.0000711 s; excludes research, QA and deploy. Ten live previews = 0, Maps-checked records = 0; these remain unmet, not silently waived. Review the code/artifacts before sessions 2-3; no fourth session. TASK-003 still needs correction before commercial publication, and no GitHub Pages sales deployment was performed. No TASK-005 work or outreach.

## Session 2 result (2/3 complete)
TASK-003 final PASS recorded first in REV-008. Reopened all ten official sources; added verified Wedgeworth and Houston Aqueduct phones; Mission number remains blank rather than guessed. Mobile visuals inspected for three styles at 320px; 40 layout checks passed across all ten pages at 320/390/430/1440px. Eleven Python tests pass, including all ten expired routes returning local HTTP 404. Expiry build now contains zero preview directories; active/expiry ZIPs and dated SHA-256 manifest are prepared together by expiry_bundle.py. Original preview date 2026-09-22 retained; deadline 2026-10-06T00:00:00Z. No live deletion/scheduling claimed.

One session remains (3/3): choose/verify commercially eligible host per accepted offer revision 2, deploy with cache/removal behavior, verify ten live URLs and scheduled expiry, then Claude review. GitHub Pages wording in the original task is superseded by offer rev2 section 3; legacy Maps hand-collection remains explicitly 0/10, not silently claimed complete. No TASK-005 collection, spending or outreach.
