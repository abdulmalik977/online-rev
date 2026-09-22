# Houston website concept generator — TASK-006, session 1/3

Portable local v1, Python 3.11+, standard library only. No accounts or purchases.
Ten real businesses, three deterministic styles, original artwork, escaped factual
content, noindex, fourteen-day expiry, optional HTTPS checkout URL. No copied
photos/reviews, enquiries, analytics, email sending or external build requests.

From the repository root:

```powershell
python generator/build.py --output .runtime/previews-session1 --preview-date 2026-09-22
python -m http.server 8765 --bind 127.0.0.1 --directory .runtime/previews-session1
# Open http://127.0.0.1:8765/ (local only)
python -m unittest discover -s generator -p "test_*.py" -v
python generator/deploy.py --source .runtime/previews-session1 --archive .runtime/previews-session1.zip
```

Choose a **new** output/archive name for each run. Nothing deletes or merges an
existing deployment. For a newly created preview use its actual creation date;
keep that date on every rebuild. `--as-of` allows reproducible expiry tests.
CHECKOUT_URL is read from the environment, never from the CSV. Unset it for review.
An absent URL produces a visibly disabled purchase button. Do not configure a live
checkout until offer/provider eligibility is resolved. No webhook/order work here.

The example date belongs to this session's fixture; it is not a date to reuse for
future customers. Generated files are ignored under `.runtime/`, and a compact
timing artifact is retained in `generator/session-1-results.json` after validation.

## Evidence and limits

See [schema](schema.md), [sources](sources.md), [design](design.md), and
[TASK-003 review](../research/markets/offer-challenge.md). This testset is not the
TASK-005 list and contains no verified email prospects. Website facts were manually
checked; direct Maps verification remains pending and is not claimed by this build.
Fixture businesses already have websites; the set tests rendering, not buying intent.

`build-report.json` separates local render time from research, visual QA, deployment
and maintenance. A sub-second render is not proof of a four-minute end-to-end SLA
or >=70% maintenance automation. Source URL fields do not prove data truth on their own.
Hours, address, certification claims and review counts remain absent, not invented.

`deploy.py` currently prepares an allowlisted ZIP only. It excludes audit JSON and
rejects unexpected files, symlinks and expired live builds. **Nothing is published**.
GitHub Pages is not the chosen commercial host: its restrictions conflict with the
proposed sales previews; REV-007 records the evidence. Choose an eligible host after
offer correction, then upload the archive as a full replacement and verify all ten
URLs. Do not upload the repository root. No provider integration was invented here.

Expiry JS hides the page at the UTC deadline as a convenience; it is **not** access
control or deletion. A rebuild at/after expiry emits a minimal expired page and removes
names from the index. The eventual host must replace the whole tree at expiry and
purge caches as supported. Until scheduled deployment/removal is working, do not
promise customers that static content automatically disappears. `noindex` is a
crawler request, not privacy protection.

Remaining session budget: at most two sessions, for source/visual refinements and
eligible-host deployment. TASK-006 is not ready for Claude PASS until ten live URLs,
the Maps check, the agreed content spec and expiry deployment are actually verified.
