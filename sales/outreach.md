# Outreach sequence, compliance kit and reply handling (TASK-008)

Author: Claude (planner). Date: 2026-09-23. For Codex review: every rule below must be implementable without interpretation. Governing decisions: DEC-003 (channels and caps), DEC-007 (pilot), company/offer.md rev 2 (promises). No sending until SETUP-EMAIL is resolved.

Placeholders, all read from one config file (`company/config.json`, created in TASK-007): `{COMPANY}`, `{POSTAL_ADDRESS}`, `{SENDING_DOMAIN}`, `{PREVIEW_URL}`, `{EXPIRY_DATE}`, `{UNSUB_URL}`, `{BUSINESS}`, `{FIRST_NAME}` (falls back to "there" if unknown), `{CITY}`.

## 1. Sequence (3 emails, plain text, no attachments, no images, no tracking pixels)

Timing is in US Central business days; sends only Tue–Thu 08:30–11:30 and 13:30–16:00 Central (windows chosen for owner-operators; A/B later).

**Email 1 — day 0 (preview)**
Subject variants (rotate evenly, tag which was used):
- A: `A new website for {BUSINESS} (preview inside)`
- B: `{BUSINESS} — we built you a website concept`
- C: `Quick one: your {CITY} plumbing site, redesigned`

```
Hi {FIRST_NAME},

We build websites for plumbing and HVAC companies in {CITY}, and we made one for {BUSINESS} using the services listed on your current site:

{PREVIEW_URL}

It's an independent concept, not your official site. If you'd like it, it goes live on your domain within two business days for $119/month, no setup fee, cancel anytime. The details and the order button are on the preview page.

If it's not for you, no reply needed. The preview is removed on {EXPIRY_DATE}.

{SIGNATURE}
```

**Email 2 — day 3 (nudge), only if no reply and no purchase**
Subject: `Re: ` + the subject used in email 1.
```
Hi {FIRST_NAME},

Following up on the concept site we built for {BUSINESS}: {PREVIEW_URL}

Two things people ask: yes, it works on your existing domain, and yes, you can change anything on it by emailing us (up to 5 requests a month are included).

The preview is up until {EXPIRY_DATE}.

{SIGNATURE}
```

**Email 3 — day 10 (expiry notice), only if no reply and no purchase**
Subject: `Re: ` + the subject used in email 1.
```
Hi {FIRST_NAME},

Last note from us: the concept site for {BUSINESS} comes down on {EXPIRY_DATE}.

{PREVIEW_URL}

If you want it, the order button on that page is all it takes. If not, thanks for your time, and we won't email you again about this.

{SIGNATURE}
```

**Signature and footer block (every email, unchanged):**
```
The {COMPANY} team
{COMPANY} · {POSTAL_ADDRESS}

This is a commercial email about website services. To stop receiving emails from us: {UNSUB_URL} (or reply "unsubscribe"). We honor every request within 10 business days, usually the same day.
```

Rules: one prospect = one thread (email 2 and 3 are replies to email 1's Message-ID). Max 3 emails per prospect, ever, unless they reply. No "urgency" language beyond the factual expiry date. No claims about the prospect's current site ("slow", "outdated") — the preview speaks for itself.

## 2. Compliance mapping

| Requirement | Satisfied by |
|---|---|
| CAN-SPAM: accurate header/from/reply-to | From: `{COMPANY} <hello@{SENDING_DOMAIN}>`; Reply-To same mailbox; no display-name impersonation |
| CAN-SPAM: no deceptive subject | Subjects above name the product; "Re:" only on actual replies in the same thread |
| CAN-SPAM: identify as an advertisement | Footer sentence "This is a commercial email about website services" |
| CAN-SPAM: physical postal address | `{POSTAL_ADDRESS}` in footer (street or registered PO box; owner input) |
| CAN-SPAM: opt-out mechanism working ≥30 days | `{UNSUB_URL}` (TASK-007 opt-out page) + reply keyword; the page must stay live ≥30 days after the last send |
| CAN-SPAM: honor opt-out ≤10 business days | Suppression applied immediately on unsubscribe (see §3); no fee, no login, no extra info |
| CAN-SPAM: no harvesting from sites that forbid it | Prospect source recorded per row (`email_source`); sites whose terms forbid email collection are skipped (TASK-005 rule) |
| UK PECR (if any UK prospect ever) | Corporate subscribers only (Ltd/LLP via Companies House); legitimate-interests note in privacy page; objection = immediate suppression. Not in the Houston pilot. |
| Sender identity | Signed "The {COMPANY} team"; no invented person names |

## 3. Suppression list (`sales/suppression.csv`, columns: `email,domain,reason,added_at,source`)

Add and never send again when any of these occur:
- `unsubscribe`: opt-out page hit or reply containing "unsubscribe", "remove", "stop", "opt out", "take me off" (case-insensitive) → suppress **email and domain** immediately.
- `bounce_hard`: 5xx bounce → suppress email.
- `bounce_soft_x3`: three soft bounces → suppress email.
- `negative`: reply classified negative (§5) → suppress email and domain.
- `role_address`: local part in {abuse, postmaster, noreply, no-reply, legal, privacy, security} → never contact (filtered before sending).
- `complaint`: any spam complaint feedback → suppress domain; pause the sending mailbox for 48 h.
- `customer`: paid customer → suppress from outreach (they move to the customer list).
- `owner_manual`: owner adds a line by hand.
The sending script checks the suppression list **at send time**, not at scheduling time.

## 4. Sending capacity and warm-up (DEC-003: 3–5 mailboxes, ≤40/mailbox/day)

- Separate sending domain from the company domain; SPF, DKIM, DMARC (`p=quarantine`) set before the first send; a mailbox is not used until its DNS checks pass.
- Warm-up per new mailbox: week 1 ≤10/day, week 2 ≤20/day, week 3 ≤30/day, week 4+ ≤40/day. During weeks 1–2, at least half the volume is to the other company mailboxes (replies exchanged), not prospects.
- Daily unique-prospect capacity at full warm-up with 5 mailboxes: 200 sends/day ≈ 70–100 new prospects/day once follow-ups are counted (each prospect consumes up to 3 sends over 10 days).
- Auto-pause rules: bounce rate >5% in a day → pause that mailbox 24 h and alert; complaint rate >0.1% → pause 48 h; open-ended: no more than 5 emails to the same domain per day.
- All sends are logged: prospect id, mailbox, email number, subject variant, Message-ID, timestamp.

## 5. Reply handling (classification runs on every inbound to the sending mailboxes)

Classes, detection rule, action. When two classes match, the earlier row wins.

| Class | Detection (case-insensitive) | Action |
|---|---|---|
| `unsubscribe` | keywords in §3 | Suppress; reply once: "Done — you won't hear from us again. Sorry for the interruption." |
| `bounce` | mailer-daemon / delivery status notification | Suppress per §3; no reply |
| `auto_reply` | "out of office", "auto-reply", "automatic reply", "away until" | Ignore; sequence continues on schedule |
| `negative` | "not interested", "no thanks", "stop", "don't contact", legal/threat words ("lawyer", "attorney", "report", "spam", "cease") | Suppress email+domain; if legal/threat words → **owner escalation**, no reply until owner decides; otherwise reply once: "Understood, thanks for letting us know. Removed." |
| `interested` | "yes", "interested", "how do", "sign up", "let's do it", "how much", "what's next" | Reply within 1 business hour with the order link and the two-business-day promise; do not offer calls; if they ask for a call: "We work by email so we can keep the price at $119 — happy to answer anything here." |
| `question` | contains "?" and none of the above | Answer from the FAQ set (§6); anything outside the FAQ → owner queue with a drafted answer, 1-business-day promise to the prospect |
| `refund_request` | "refund", "money back", "charge back" | **Owner escalation**; auto-acknowledge: "Received — we'll come back to you within one business day." |
| `other` | none matched | Owner queue with a drafted reply; no auto-send |

Owner escalation = line in `approvals/pending.md` with the thread link and a drafted reply; nothing is sent until the owner resolves it. Maximum automated replies per prospect: 2; after that, owner queue.

## 6. FAQ answers (canned, verbatim)

- **Domain:** "Yes, it runs on your existing domain. After you order we send a one-page instruction for your DNS provider; until then the site is live on a subdomain of ours."
- **Changes:** "Email us the change. Up to 5 requests a month are included (each up to about 30 minutes of work), done within 2 business days."
- **Contract:** "Month to month. Cancel anytime from your receipt email; the site stays up to the end of the paid month and you get a zip export."
- **Photos:** "Send us your own photos and we'll swap them in. We only use images you own or have permission to use."
- **Hosting/SSL:** "Hosting and HTTPS are included."
- **Not live in time:** "If it isn't live on the subdomain within 5 business days of your order and confirmation email, the first month is refunded automatically."
- **Who are you:** "{COMPANY}, a small team that builds and maintains websites for trade businesses. We work by email; our address is in every message."

## 7. Metrics (feed the daily report "Pipeline" line)

- `emails_sent`: sends accepted by the SMTP server (not scheduled).
- `unique_prospects_contacted`: prospects with ≥1 accepted send.
- `replies`: inbound classified as anything except `bounce` and `auto_reply`.
- `positive_replies`: `interested` + `question`.
- `sample_views`: preview page loads excluding our own IPs and known bots (cookie-free analytics on the preview host).
- `paid`: webhook-confirmed orders.
- Rates reported per unique prospect: reply rate, positive rate, paid rate. DEC-007 checkpoint at day 30 uses these definitions.

## 8. Go-live checklist (all must be true before the first send)

1. SETUP-EMAIL resolved: sending domain, 3–5 mailboxes, SPF/DKIM/DMARC passing.
2. `company/config.json` filled: company name, postal address, unsubscribe URL live (TASK-007).
3. Preview host verified for commercial use and 10 previews live with working expiry removal (TASK-006 session 3).
4. Checkout URL live on the preview page, or the buy button stays disabled and email copy switches to "reply to order" (fallback variant to be written only if the provider is still pending at go-live).
5. Suppression list initialized; role-address filter tested; reply classifier tested on 20 sample replies.
6. Owner escalation path tested end to end with one fake legal-threat reply.
