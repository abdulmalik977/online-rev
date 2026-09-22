# Session 1 fixture provenance — 2026-09-22

Ten real businesses serving Houston, TX, manually researched using their official
public websites. Only basic facts/service labels are transcribed; marketing copy,
review text, ratings, logos and photography are not copied. No messages or calls.
City is service coverage, not a claim about headquarters. Public business phone
numbers appear only where independently visible on the cited page; blank means
not transcribed/verified in this pass. These are not paid customers or vetted leads.

| Business | Official source and facts checked |
|---|---|
| Nick's Plumbing & Air Conditioning | https://www.nicksplumbing.com/ — Houston, plumbing, water heaters/drains; footer phone 713-868-9907 |
| Abacus Plumbing, Air Conditioning & Electrical | https://www.abacusplumbing.net/ — Houston, plumbing/drain cleaning/leak detection; 713-766-3605 |
| Lucky's Plumbing | https://luckysplumbing.com/ — Houston, plumbing/leaks/water heaters; 713-464-1921 |
| Texas Quality Plumbing | https://texasqualityplumbing.com/ — Greater Houston, water heaters/drains/repiping/gas lines; 346-636-2418 |
| Wedgeworth Plumbing | https://wedgeworthplumbing.com/ — Houston plumbing/water heater service; phone omitted |
| Mission Air Conditioning & Plumbing | https://www.missionac.com/ — Houston HVAC/plumbing/water heaters; phone omitted |
| Village Plumbing, Air & Electric | https://villageplumbing.com/ — Houston plumbing/HVAC; 281-957-6221 |
| John Moore Services | https://www.johnmooreservices.com/plumbing/ — Houston plumbing/repiping/sewer; 713-853-9881 |
| GEI Plumbing Services | https://www.geiplumbingservices.com/ — Houston plumbing repairs; 832-402-7860 |
| Aqueduct Plumbing Company | https://aqueductplumbingcompany.com/services/ — Houston plumbing/repiping/gas lines; phone omitted |

## Remaining Maps check

This set does **not** yet satisfy the task's literal hand-collection-from-Google-Maps
requirement. All ten `maps_status` values remain `pending`. Official pages for Nick's
and Abacus link to Maps, but an outgoing link is not evidence that the matching Maps
record was inspected. Do not turn `pending` into `checked` or invent place IDs to
satisfy a count. The connected browser's latest initialization in this conversation failed with
`CryptUnprotectData failed`; public web results enabled the website research.
A separate isolated headless browser was used only for local layout tests.
Direct matching of ten Maps records remains a follow-up before TASK-006 review.

The generator's original `house.svg` is generic artwork, not a depiction of any
business, staff, premises or completed work. It requires no third-party stock license.
The source audit fields stay in local `records.json`; `deploy.py` excludes that audit
file from the public package. Each preview retains a visible official-source link.
