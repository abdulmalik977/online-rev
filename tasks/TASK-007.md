---
id: "TASK-007"
title: "Landing page and order flow (checkout provider pluggable)"
owner: "codex"
status: "todo"
goal: "One-page site that sells the offer in company/offer.md section 3 and a post-payment flow that promotes a preview to a live customer site, with the payment provider behind a single URL and webhook so the owner's Paddle/Lemon Squeezy account can be plugged in later"
evidence: "offer.md sections 3 and 5; DEC-002 self-serve; no provider account exists yet, so checkout is a placeholder URL and the webhook is tested with a signed fake payload"
definition_of_done: "site/ with the landing page (headline, what is included, price, terms, refund rule, FAQ, physical address placeholder, privacy page); deployed on GitHub Pages; orders/ script that takes a webhook payload (provider-agnostic JSON: email, preview slug, plan) and promotes the preview (removes banner/noindex, records the order in db + orders.md); welcome email template with DNS instructions; unsubscribe/opt-out page and suppression list file format for TASK-008"
success_metric: "Landing page loads under 1 s on mobile (Lighthouse >= 90 performance); fake-webhook test promotes a preview end to end; Claude PASS via --review"
attempts: 0
review_round: 0
quota_budget: 40
created: "2026-09-22T19:50:00+00:00"
updated: "2026-09-22T19:50:00+00:00"
---
Starts after TASK-006 v1 exists (needs a preview to promote). At most 2 sessions.
Reviewer: claude. Company name, domain and postal address are owner inputs: use placeholders
read from one config file so they are changed in one place. No payment provider signup here.
