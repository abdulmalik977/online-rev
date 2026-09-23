# Session 2 local visual review

Sales, privacy and email-preferences pages passed 12/12 checks at 320, 390, 430
and 1440 CSS pixels. No horizontal overflow, cookies or sales-page forms. The
concept-request link points to mailto and wraps inside the price card on mobile.
`concept-card.png` was visually inspected; full mobile/desktop captures are retained.
The mailbox is the reserved configuration example, not a real working company inbox.

Lighthouse 13.5.0 simulated mobile on loopback: performance/accessibility/best
practices 100, LCP about 0.75 seconds, CLS 0. No hosted performance claim.
Full JSON remains in .runtime/task007-session2-qa/lighthouse.json; compact results
and final public asset hashes are in site/session-2-results.json.

Use TASK007_QA_URL, TASK007_QA_DEBUG and TASK007_QA_OUTPUT environment variables
with node site/qa.cjs to target an isolated local server/Chrome. No mailto link
was activated and no email, payment, account connection or deployment occurred.
