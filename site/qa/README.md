# TASK-007 session 1 - local visual and performance evidence

2026-09-23. Isolated headless Chrome, explicit device metrics. Sales, privacy and
email-preferences pages checked at 320, 390, 430 and 1440 CSS pixels: 12/12 pass,
no horizontal overflow, expected headings, no cookies, disabled checkout.
The [mobile](mobile.png) and [desktop](desktop.png) full-page captures were inspected.
The final template describes the preview without claiming it is access-controlled.

Lighthouse 13.5.0 default simulated mobile profile against loopback:
performance 100, accessibility 100, best practices 100; LCP about 751 ms, CLS 0.
The scores are lab observations, not accessibility certification or hosted speed.
Full results and public artifact hashes are in `../session-1-results.json`;
full Lighthouse JSON remains at `.runtime/task007-qa/lighthouse.json`.

The plain local server has no compression or cache-lifetime tuning. Lighthouse
reports those opportunities even though the category scores are 100. Verify the
actual host's headers and repeat the performance run after deployment.

Reproduce by building the page, serving it on loopback port 8777, starting an
isolated Chrome on debugging port 9227 and running `node site/qa.cjs`. Screenshots
and layout measurements are written to `.runtime/task007-qa/` (create it first).
No real customer content, credentials, account access, payment or email appears
in this evidence.
