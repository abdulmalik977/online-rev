---
id: "TASK-006"
title: "Sample site generator v1 (the product) from public business data"
owner: "codex"
status: "doing"
goal: "Build the generator that turns one prospect's public Google Business Profile data into a finished, deployed preview website, per company/offer.md section 4"
evidence: "offer.md sections 3-4 (template, sections, no-claims rule, 14-day banner, noindex, buy button); dec-001-validation.md rev 2; no external accounts required: use GitHub Pages under the existing account for previews"
definition_of_done: "generator/ directory with: input schema (CSV row -> JSON), one template family with 3 style variants, generator script, static output, deploy script to GitHub Pages at previews/<slug>/, expiry banner and noindex, buy button reading CHECKOUT_URL from env; test set of 10 real Houston plumbing/HVAC businesses collected by hand from Google Maps (public data, no scraping accounts) in generator/testset.csv; 10 previews live; README with run command; measured compute time per prospect"
success_metric: "10 of 10 test previews build and deploy without manual edits; median build time <= 4 minutes per prospect; no copy claim not present in source data (checked by a grep list); Claude PASS via --review"
attempts: 1
review_round: 0
quota_budget: 60
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-22T19:54:08+00:00"
---
Starts after TASK-003 review (product confirmed). Budget: at most 3 sessions for v1.
Reviewer: claude. No outreach. Do not fetch photos in a way that violates Google terms:
use the public GBP page and the business's own website only; stock fallback otherwise.
The 10 test previews double as the first real samples for outreach once TASK-008 is ready.

Session 1/3 started after REV-007 per explicit owner instruction. Product family is feasible; commercial promises are not passed. Local generator work proceeds; live sales previews require suitable hosting and source rights. See generator/design.md and research/markets/offer-challenge.md.
