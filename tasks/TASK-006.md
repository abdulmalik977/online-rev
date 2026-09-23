---
id: "TASK-006"
title: "Sample site generator v1 (the product) from public business data"
owner: "codex"
status: "blocked"
goal: "Build the generator that turns one prospect's public Google Business Profile data into a finished, deployed preview website, per company/offer.md section 4"
evidence: "REV-008 TASK-003 PASS; generator/session-3-results.json; generator/hosting-handoff.md; generator/session-2-results.json; active/expiry ZIP checks pass; live previews 0/10; hosting access and scheduler unavailable; session budget 3/3 reached"
definition_of_done: "generator/ directory with: input schema (CSV row -> JSON), one template family with 3 style variants, generator script, static output, deploy script to GitHub Pages at previews/<slug>/, expiry banner and noindex, buy button reading CHECKOUT_URL from env; test set of 10 real Houston plumbing/HVAC businesses collected by hand from Google Maps (public data, no scraping accounts) in generator/testset.csv; 10 previews live; README with run command; measured compute time per prospect"
success_metric: "10 of 10 test previews build and deploy without manual edits; median build time <= 4 minutes per prospect; no copy claim not present in source data (checked by a grep list); Claude PASS via --review"
attempts: 3
review_round: 0
quota_budget: 60
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-23T05:55:18+00:00"
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

## Session 3 result (3/3; BLOCKED)
TASK-008 review was recorded first (REV-009 CHANGES). Netlify Free selected using current first-party commercial eligibility and credit-plan evidence; actual owner team plan remains unverified. Prepared and checked .runtime/session3-bundle (16 active files, 6 expiry files, allowlists/CRC/SHA-256 pass), preserving 2026-09-22 and expiry 2026-10-06T00:00:00Z. See generator/hosting-handoff.md and generator/session-3-results.json.

No hosting token in checked process/user/machine environment or normal CLI configuration locations; connected browser failed CryptUnprotectData. No authenticated deploy request was possible, no site was created, and live previews remain 0/10. Existing SETUP-CRON remains unresolved, so neither a remote expiry rehearsal nor scheduling is claimed. Missing account access is recorded as SETUP-HOSTING; publication is already authorized, not awaiting a new spend approval. Legacy Maps verification is still 0/10.

All three sessions are consumed. No fourth session or automatic task restart; owner resolution of the external blocker and session budget is needed before further execution. Not ready for Claude PASS. No TASK-005 work, purchases, outreach, new infrastructure task or payment implementation.
