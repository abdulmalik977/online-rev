# TASK-006 v1 — design before code

1. Session budget: three total; this is session 1. Record one --attempt on TASK-006 only.
2. Build a portable static preview generator using Python standard library; no service or database added.
3. Read strict CSV rows into validated JSON, retaining per-field source URLs and collection dates.
4. Hand-research ten real Houston businesses; distinguish Maps discovery from independent website facts.
5. No email verification or 200-prospect collection: TASK-005 is deferred by the owner.
6. Render one responsive template family with three deterministic business-name-hash color variants.
7. Use only supplied factual services/location/phone; no invented credentials, ratings, reviews or 24/7 claims.
8. Use original geometric artwork; omit third-party photos/reviews until rights are established.
9. Every page says independent concept preview, includes noindex and a fixed fourteen-day expiry date.
10. Disable checkout unless CHECKOUT_URL is configured; reject non-HTTPS checkout links and escape all input.
11. No lead form, analytics, calls or email sending in the preview; link clearly to the existing official site.
12. Rebuilding after expiry produces a minimal expired page; deployment must replace stale files atomically.
13. Package only a fresh allowlisted output tree; never deploy repository/task/approval files or secrets.
14. Do not publish commercial previews on GitHub Pages; REV-007 identifies the hosting eligibility gate.
15. Validate ten builds, malicious data, expiry, deterministic output and timings; publication remains a separate verified gate.

## Session 2 plan (before edits)
Preserve original preview dates. Prepare both active and post-expiry archives from the same input; the expiry tree omits all preview directories rather than replacing them with branded placeholders. Ship a dated removal manifest separately from public files. Remote replacement/cache verification belongs to session 3, not a local deletion claim. Recheck missing phone sources and mobile layouts at 320/390/430 px, including all styles.
