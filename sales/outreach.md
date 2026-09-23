# Outreach sequence, compliance kit and reply handling (TASK-008) — revision 2

Author: Claude (planner). Date: 2026-09-23. Revision 2 answers REV-009 R01–R12 (§10 maps each) and defines the 20 fixture outcomes (§9). Governing: DEC-002/003/007, company/offer.md rev 2. No sending until §8 is fully true.

## 0. Configuration and identifiers

Two config sources, both validated at startup; any unresolved `{PLACEHOLDER}` in an outgoing message aborts the send.
- `company/config.json` (company-level): `company`, `postal_address`, `sending_domain`, `mailboxes` (list of 3–5 local parts, e.g. `hello, team, hi, contact, web`), `preview_base_url`, `unsub_base_url`, `checkout_base_url`, `target_regions` (pilot: `["Houston, TX"]`), `internal_domains` (company + sending domain), `shared_mail_domains` (list in §3), `us_federal_holidays` (dates), `owner_queue_path`.
- Prospect runtime record (`prospect_id` = stable slug from TASK-005 CSV row hash): `business`, `first_name` (nullable → "there"), `city`, `email`, `mailbox` (assigned at first send), `preview_slug`, `preview_date` (= date of email 1, Central), `expiry_utc` (= preview_date + 14 days at 00:00 UTC), `thread_message_id`, `subject_variant`, `sends[]`, `state` ∈ {queued, active, replied, not_now, suppressed, paid, expired}.
- `order_id` from the checkout provider is the dedup key for `paid`. Inbound `Message-ID` is the dedup key for every inbound event (§5.0).

## 1. Sequence (plain text, no attachments, images or tracking pixels)

Calendar: **America/Chicago**. Send days: Tue, Wed, Thu, excluding `us_federal_holidays`. Send windows: 08:30–11:30 and 13:30–16:00 local. Offsets are calendar days from email 1's send timestamp; the send happens at the **first send-window slot at or after** the offset. Every send re-checks, atomically at send time: prospect state = active, not suppressed (§3), no paid order, `now < expiry_utc − 24h` (else state → expired, no send). A preview's `preview_date` is set once from email 1 and never changed; if email 1 is delayed past the generator's build date, the preview is rebuilt with `preview_date` = actual email-1 date before sending.

- **Email 1**: day 0.
- **Email 2**: first slot ≥ day 3, only if state = active.
- **Email 3**: first slot ≥ **day 8** and ≤ expiry − 24h; otherwise skipped (no substitute send). Day 8 (not the task text's day 10) is chosen because with Tue–Thu send days and a 14-day expiry, day 10 has a valid slot only for Thursday email-1s, while day 8 has one for all three (Tue → Wed d8; Wed → Thu d8; Thu → Tue d12). Holidays can still remove the slot; then email 3 is skipped and logged.
- Cap: 3 outreach sends per prospect, ever. Automated replies (§5) are not outreach sends and do not count.

Subject variants for email 1 (rotate evenly by `prospect_id` mod 3; record variant):
- A: `A new website for {BUSINESS} (preview inside)`
- B: `{BUSINESS} — we built you a website concept`
- C: `Quick one: your {CITY} plumbing site, redesigned`
Emails 2 and 3 use `Re: ` + email 1's subject and `In-Reply-To`/`References` = email 1's Message-ID.

**Email 1**
```
Hi {FIRST_NAME},

We build websites for plumbing and HVAC companies in {CITY}, and we made one for {BUSINESS} using the services listed on your current site:

{PREVIEW_URL}

It's an independent concept, not your official site. If you'd like it, the order button is on the preview page: $119/month, no setup fee, cancel anytime. It goes live on a subdomain within two business days of your order and confirmation email, and on your own domain as soon as you point it there (we send the instructions).

If it's not for you, no reply needed. The preview is removed on {EXPIRY_DATE}.

{SIGNATURE}
```
**Email 2**
```
Hi {FIRST_NAME},

Following up on the concept site we built for {BUSINESS}: {PREVIEW_URL}

Two things people ask: yes, it works on your existing domain, and yes, you can send us up to 5 change requests a month (each up to 30 minutes of work), done within two business days.

The preview is up until {EXPIRY_DATE}.

{SIGNATURE}
```
**Email 3**
```
Hi {FIRST_NAME},

Last note from us: the concept site for {BUSINESS} comes down on {EXPIRY_DATE}.

{PREVIEW_URL}

If you want it, the order button on that page is all it takes. If not, thanks for your time, and we won't email you again about this.

{SIGNATURE}
```
**`{SIGNATURE}` (identical in every outreach email; it is also the quote-detection anchor in §5.1):**
```
The {COMPANY} team
{COMPANY} · {POSTAL_ADDRESS}

This is a commercial email about website services. To stop receiving emails from us: {UNSUB_URL} (or reply with the word "unsubscribe"). We honor every request within 10 business days, usually the same day.
```
Headers on every outreach email: `List-Unsubscribe: <{UNSUB_URL}>, <mailto:{MAILBOX}?subject=unsubscribe>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058).

Copy rules: no claims about the prospect's current site; no urgency beyond the factual expiry date; no invented person names.

## 2. Compliance mapping (operational controls)

| Requirement | Control | Verified by |
|---|---|---|
| Accurate From/Reply-To/routing | From = `{COMPANY} <{mailbox}@{sending_domain}>`; Reply-To identical; mailbox fixed per prospect (§4.1) | Startup validation; §8.5 |
| No deceptive subject | Fixed subjects §1; `Re:` only inside the real thread | Code review |
| Identified as advertisement | Footer sentence | Template test |
| Physical postal address | `postal_address` in footer; send aborts if empty | Startup validation |
| Working opt-out ≥30 days | `{UNSUB_URL}` page (§3.2) and one-click header; page kept live until `last_send + 45 days`; reply keyword | §8.6 functional test from an external mailbox |
| Honor opt-out ≤10 business days | Suppression written before any acknowledgement; effective at the next send-time check | Fixture 6 |
| Opted-out addresses not transferred/sold | Suppression list stays in the repo's private data; only shared with processors below, only to enforce suppression | Privacy page text (TASK-007) |
| Responsibility for processors | Processors listed in the privacy page: mailbox provider, preview host, analytics provider; each bound by its own terms; the company remains responsible | TASK-007 privacy page |
| Targeting | Sends only to prospects whose `city, state` ∈ `target_regions`; UK and any other region rejected at send time | Fixture: non-Houston row refused |
| UK/PECR | Out of scope for the pilot; a UK launch requires its own task and review | — |

## 3. Suppression

### 3.1 List and scope
`sales/suppression.csv`: `key,kind,reason,added_at,source_message_id`. `kind` ∈ {email, domain}. Normalization: lowercase, trim, strip surrounding `<>`; domain = text after the last `@`. A `domain` key matches the exact domain and all subdomains. Domain-level rows are **never** written for a domain in `shared_mail_domains` (gmail.com, googlemail.com, yahoo.com, ymail.com, outlook.com, hotmail.com, live.com, msn.com, icloud.com, me.com, mac.com, aol.com, comcast.net, att.net, sbcglobal.net, verizon.net, protonmail.com, proton.me, mail.com); for those, only the email row is written.

| Reason | Trigger | Rows written |
|---|---|---|
| `unsubscribe` | §3.2 opt-out event, or OPT_OUT flag (§5.3) | email + every other email of the same `prospect_id` (business); no domain row |
| `bounce_hard` | DSN with `Status: 5.x.x` for a recipient we sent to | email |
| `bounce_soft_x3` | three DSNs `4.x.x` for the same email within a 30-day sliding window, counted by distinct DSN Message-ID | email |
| `negative` | NEGATIVE without NOT_NOW (§5.3) | email + domain (subject to shared-domain rule) |
| `legal` | LEGAL flag | email + domain (subject to shared-domain rule) |
| `complaint` | complaint feedback (§4.3) or a reply containing "spam" as a whole word plus any of "report", "reported", "complaint" | email + domain (shared-domain rule) |
| `role_address` | local part ∈ {abuse, postmaster, noreply, no-reply, donotreply, legal, privacy, security, mailer-daemon, hostmaster, webmaster} | filtered before scheduling; never sent |
| `customer` | paid order | email; state → paid |
| `owner_manual` | line added by owner | as written |

Checks happen inside the send transaction (§4.4). Suppression is idempotent: an existing key is not duplicated; the earliest `added_at` is kept.

### 3.2 Opt-out page semantics
`{UNSUB_URL}` = `unsub_base_url/<token>` where token = HMAC(prospect_id). **GET** renders a page with one button "Unsubscribe" and a one-line statement; GET never suppresses (link scanners). **POST** to the same URL (button, or RFC 8058 one-click POST) writes the suppression row and shows "Done. You won't hear from us again." No login, no email entry, no fee. A POST for an already-suppressed token returns the same confirmation. Email acknowledgement: **none** for page/one-click opt-outs; for reply-keyword opt-outs, exactly one transactional acknowledgement (§5.4, template ACK_UNSUB), sent even if the reply ceiling is reached, and never with promotional content.

## 4. Sending

### 4.1 Mailboxes and routing
Active mailboxes = those in `mailboxes` whose authentication check passed (§4.2). A prospect is assigned at first send to `active_mailboxes[hash(prospect_id) mod N]` and keeps that mailbox for the whole thread and all automated replies. If that mailbox is paused, the prospect's sends wait; they are not re-routed.

### 4.2 Authentication and warm-up
Pass criteria before a mailbox is active: a test message from it to an external mailbox we control (different provider) shows `spf=pass`, `dkim=pass`, `dmarc=pass` in `Authentication-Results`; DMARC record `p=quarantine` or stricter on the sending domain. Warm-up age = calendar days since the mailbox's **first send of any kind**. Daily outreach cap per mailbox: days 1–7 → 10; 8–14 → 20; 15–21 → 30; ≥22 → 40 (DEC-003 ceiling). Internal mailbox-to-mailbox exchanges during warm-up are **optional and unvalidated** as a deliverability technique; they count against the mailbox's daily cap if used. Caps count outreach sends and automated replies to prospects; internal mail counts only when used for warm-up.

### 4.3 Pauses and counters
All counters are per mailbox, per Central calendar day, DST-aware. Denominator = accepted sends that day (SMTP 250). A DSN is attributed to the day of the original send (matched by Message-ID from `In-Reply-To`/`References`/original headers in the DSN; if unmatched, to the day received).
- Hard-bounce rate: hard bounces attributed to a day ÷ that day's accepted sends, evaluated 72 h after the day ends, minimum 20 sends; >5% → mailbox paused 24 h + owner report line.
- Complaint rate: only if a complaint feedback source exists (config flag `complaint_feed=true`); >0.1% with ≥100 sends → pause 48 h. If no feed, the rule is inactive and §3.1 `complaint` (reply-based) is the only complaint control.
- Same-domain cap: at most 5 outreach sends per prospect-domain per Central day across all mailboxes (shared mail domains exempt).
- Resume: automatically at the end of the pause; a second pause within 7 days → mailbox disabled until owner re-enables.

### 4.4 Send transaction
For each scheduled send: lock → reload prospect state and suppression → re-check §1 conditions and caps → send → on 250 write the send log row (`prospect_id, mailbox, email_no, variant, message_id, sent_at_utc`) → unlock. A duplicate scheduled job for the same `(prospect_id, email_no)` is a no-op if a log row exists.

## 5. Inbound handling

### 5.0 Dedup and scope
Every inbound to a sending mailbox is keyed by its `Message-ID`; a repeated Message-ID is ignored entirely (no count, no action). Inbound from `internal_domains` is ignored. Inbound not matching a known prospect (by From address after normalization, or by thread headers) → owner queue as `unknown_sender`, no automated reply.

### 5.1 Automatic-mail detection (headers only; body words are never used for this)
- **DSN**: `Content-Type: multipart/report; report-type=delivery-status`, or From local part ∈ {mailer-daemon, postmaster}. Parse `Final-Recipient`/`Original-Recipient` and `Status` per recipient; hard = `5.x.x`, soft = `4.x.x`. Suppress the failed recipient(s), never the DSN sender. No reply.
- **Auto-response**: any of `Auto-Submitted:` ≠ `no`, `X-Autoreply`, `X-Autorespond`, `X-Auto-Response-Suppress`, `Precedence: auto_reply|bulk|junk`. Action: ignore; sequence continues; the message is not a reply for metrics. A later message from the same prospect without these headers is a human reply.

### 5.2 Authored-text extraction
Take the `text/plain` part (or HTML→text). Remove, in order: everything from the first line matching `^On .+ wrote:$`, `^From: .+$`, `^-----Original Message-----$`, or `^_{5,}$`; every line starting with `>`; everything from a line equal to `-- ` (signature separator); any verbatim occurrence of our `{SIGNATURE}` block. What remains, lowercased and whitespace-normalized, is `body`. Matching below is on `body` only, using whole-word/phrase regex (`\b…\b`).

### 5.3 Flags (all evaluated; actions combine)
- **OPT_OUT**: `unsubscribe`, `opt out`, `opt-out`, `take me off`, `remove me`, `stop emailing`, `stop sending`, `no more emails`, `do not contact`, `don't contact`, `don't email`, or `body` equals `stop`.
- **LEGAL**: `lawyer`, `attorney`, `legal action`, `cease and desist`, `sue`, `lawsuit`, `ftc`, `report you`, `spam complaint`, `harassment`.
- **REFUND**: `refund`, `money back`, `chargeback`, `charge back`, `dispute the charge`.
- **NOT_NOW**: `not now`, `not right now`, `not at the moment`, `not for now`, `maybe later`, `later this year`, `next month`, `next year`, `next quarter`, `check back`, `circle back`, `busy right now`, `in a few months`.
- **NEGATIVE**: `not interested`, `no thanks`, `no thank you`, `we're good`, `we are good`, `already have`, `don't need`, `do not need`, `pass`.
- **INTERESTED**: `interested`, `let's do it`, `lets do it`, `sign me up`, `sign up`, `how do i order`, `how do i sign up`, `i'll take it`, `i want it`, `go ahead`, `sounds good`, `let's go`, or `body` ∈ {`yes`, `yes please`, `ok`, `okay`, `sure`}.
- **CALL**: `call me`, `give me a call`, `phone call`, `schedule a call`, `hop on a call`, `talk on the phone`.
- **QUESTION**: `body` contains `?`.
(`yesterday` does not match `yes`; `report` alone matches nothing; `stop` alone matches only as the whole body.)

### 5.4 Decision (evaluate top to bottom; every matching row's suppression/escalation applies; at most one automated reply per inbound)
1. OPT_OUT → suppress per §3.1 `unsubscribe`; state → suppressed. If the message came as a reply keyword (not the page), queue ACK_UNSUB — unless LEGAL is also set (then no reply at all).
2. LEGAL → suppress per §3.1 `legal`; owner escalation `legal` (§6); **no automated reply**; stop here.
3. REFUND → owner escalation `refund`; reply ACK_REFUND (allowed regardless of ceiling); stop here. (If the sender is not a paying customer, the queue item says so; still no sales reply.)
4. If both INTERESTED and (NEGATIVE or NOT_NOW) → owner queue `uncertain`; no automated reply; stop.
5. NOT_NOW (takes precedence over NEGATIVE when both match) → state → not_now; no further outreach for 60 days; after 60 days the prospect may be included in a new batch only with a fresh preview and owner approval of that batch; reply ACK_NOT_NOW; stop.
6. NEGATIVE → suppress per §3.1 `negative`; reply ACK_NEGATIVE; stop.
7. CALL → reply NO_CALL (counts as an automated reply); if INTERESTED also set, use NO_CALL_ORDER instead; state → replied; stop.
8. INTERESTED → reply ORDER; state → replied; stop.
9. QUESTION → match FAQ (§7): if ≥1 match, reply with the matched answers (max 2) using template FAQ_REPLY; else owner queue `question` + reply ACK_QUESTION; state → replied; stop.
10. Otherwise → owner queue `other` with a drafted reply; no automated reply; state → replied.

Reply ceiling: at most 2 automated replies per prospect (ACK_UNSUB and ACK_REFUND are exempt). When the ceiling is reached, rows 5–9 still apply their state/suppression changes but the reply is replaced by an owner-queue item. A human reply of any kind sets state → replied and cancels remaining outreach sends.

Reply timing: automated replies are sent within 15 minutes when received Mon–Fri 08:00–18:00 Central; otherwise at 08:00 the next business day.

### 5.5 Templates (verbatim; `{SIGNATURE}` appended to all)
- **ORDER**: `Great — the order button is on your preview page: {PREVIEW_URL}. After you order and reply to the confirmation email, the site is live on a subdomain within two business days, and on your own domain as soon as you point it there (we send the DNS instructions). Anything you want changed, just email us.`
- **NO_CALL**: `We work by email rather than calls — that's how we keep it at $119/month with no setup fee. Ask anything here and we'll answer within one business day.`
- **NO_CALL_ORDER**: NO_CALL + ` When you're ready, the order button is on the preview page: {PREVIEW_URL}.`
- **FAQ_REPLY**: `Thanks for asking.` + newline + matched answers, each as its own paragraph.
- **ACK_QUESTION**: `Thanks — good question. We'll come back to you by the next business day.`
- **ACK_NOT_NOW**: `No problem — we'll leave it there. Thanks for the reply.`
- **ACK_NEGATIVE**: `Understood, thanks for letting us know. You're removed from our list.`
- **ACK_UNSUB**: `Done — you're unsubscribed and won't hear from us again.` (no signature footer beyond company name and address)
- **ACK_REFUND**: `Received — a person will come back to you within one business day.`

## 6. Owner escalation queue
Item = one line in `approvals/pending.md`: `- [ ] Q-{prospect_id}-{n} | {utc} | {class}: {one-line summary}; thread {message_id}; draft in sales/queue/Q-{prospect_id}-{n}.md`. Dedup by inbound Message-ID. Classes: `legal` (no reply ever without owner), `refund`, `uncertain`, `question`, `other`, `unknown_sender`. Owner clock: items older than 1 business day appear in the daily report "Critical"; nothing further is sent automatically. Answers written by the owner in the queue file are sent by Codex from the prospect's mailbox and count as owner replies (not automated).

## 7. FAQ matching (deterministic)
Each entry has a keyword set; an entry matches if any keyword is a whole-word/phrase match in `body`.
- **domain** {`domain`, `url`, `my site`, `existing site`, `dns`} → `Yes, it runs on your existing domain. After you order we send a one-page instruction for your DNS provider; until then the site is live on a subdomain of ours.`
- **changes** {`change`, `changes`, `edit`, `update`, `updates`, `add a`, `remove`} → `Email us the change. Up to 5 requests a month are included (each up to 30 minutes of work), done within two business days.`
- **contract** {`contract`, `cancel`, `commitment`, `lock in`, `month to month`, `monthly`} → `Month to month. Cancel anytime from your receipt email; the site stays up to the end of the paid month and you get a zip export.`
- **photos** {`photo`, `photos`, `pictures`, `images`, `logo`} → `Send us your own photos or logo and we'll swap them in. We only use images you own or have permission to use.`
- **hosting** {`hosting`, `host`, `ssl`, `https`, `secure`} → `Hosting and HTTPS are included.`
- **timing** {`how long`, `how fast`, `when`, `turnaround`, `days`} → `Live on a subdomain within two business days of your order and confirmation email. If it isn't live within 5 business days, the first month is refunded automatically.`
- **price** {`price`, `cost`, `how much`, `fee`, `setup`} → `$119/month, no setup fee, cancel anytime. The order button is on your preview page.`
- **who** {`who are you`, `who is this`, `your company`, `legit`, `scam`} → `We're {COMPANY}, a small team that builds and maintains websites for trade businesses. We work by email; our postal address is in every message we send.`
No match → §5.4 row 9 fallback. Answers never contain anything not in this list.

## 8. Go-live gate (all true, checked by a script that prints each line)
1. SETUP-EMAIL resolved; ≥3 mailboxes pass §4.2.
2. `company/config.json` complete; `postal_address` non-empty; `target_regions` = Houston only.
3. Preview host verified for commercial use (SETUP-HOSTING); 10 previews live; expiry replacement rehearsed remotely (generator/hosting-handoff.md step 4) and scheduled (SETUP-CRON).
4. **Self-serve checkout live** on the preview page (`checkout_base_url` returns 200 and the order button is enabled). No reply-to-order fallback exists; if checkout is not live, nothing is sent.
5. Suppression list initialized; role filter tested; classifier passes the 20 fixtures in §9 plus the 8 FAQ entries.
6. Opt-out functional test: a test send to an external mailbox → click the link → POST → suppression row present → a second send attempt to that address is refused.
7. Escalation test: a fake inbound `Stop. My lawyer will contact you.` produces suppression rows, one queue item, and zero outgoing mail.
8. DEC-007 clock starts at the first accepted outreach send to a real prospect (warm-up and tests excluded).

## 9. Fixture outcomes (acceptance)
| # | Input / event | Flags | Expected actions |
|---|---|---|---|
| 1 | `Yes, interested` | INTERESTED | ORDER reply; state replied; outreach cancelled |
| 2 | Same + quoted original footer | INTERESTED (footer stripped) | ORDER reply; no suppression |
| 3 | `Can I have a refund?` | REFUND, QUESTION | Escalation `refund`; ACK_REFUND; not counted positive |
| 4 | `Yes, refund please` | INTERESTED, REFUND | Row 3 wins: escalation `refund`; ACK_REFUND; no ORDER |
| 5 | `Stop. My lawyer will contact you.` | LEGAL only (`stop` is not the whole body, so OPT_OUT is not set) | Suppress `legal` (email + domain unless shared); escalation `legal`; no reply |
| 6 | `Please unsubscribe` | OPT_OUT | Suppress `unsubscribe`; ACK_UNSUB once; state suppressed |
| 7 | `Not now` | NOT_NOW | state not_now; ACK_NOT_NOW; no outreach 60 days |
| 8 | `Not interested right now` | NEGATIVE, NOT_NOW | NOT_NOW wins: as #7, no permanent suppression |
| 9 | `I saw it yesterday` | none | Row 10: owner queue `other`; no reply |
| 10 | `Can you show my monthly analytics report?` | QUESTION | FAQ: no match (`report`, `analytics` absent) → ACK_QUESTION + queue `question` |
| 11 | Human: `I am back from out of office; how much?` (no auto headers) | QUESTION | FAQ `price` → FAQ_REPLY |
| 12 | Genuine auto-reply with quoted footer (`Auto-Submitted: auto-replied`) | header rule | Ignored; sequence continues; not a reply |
| 13 | DSN `5.1.1` for one recipient | DSN | Suppress that recipient `bounce_hard`; no reply; DSN sender untouched |
| 14 | Third soft DSN, first two 40 days ago | DSN soft | Not suppressed (window 30 days); counter = 1 |
| 15 | Duplicate inbound Message-ID | dedup | No action, no count |
| 16 | `owner@gmail.com` opts out | OPT_OUT | Email row only (shared domain); no gmail.com row |
| 17 | Scanner GET on UNSUB_URL | GET | No suppression; page renders button |
| 18 | Email 1 Wed 09-23 → expiry 10-07 00:00Z; day 8 = Thu 10-01 08:30 CT = 13:30Z, before expiry−24h (10-06 00:00Z) | timing | Email 3 sent Thu 10-01; preview date untouched. Variant: email 1 Wed 09-23 with Thu 10-01 a holiday → next slot Tue 10-06 13:30Z is after expiry−24h → email 3 skipped and logged; no extension |
| 19 | Paid webhook delivered twice while email 2 queued | order_id dedup | One paid record; state paid; email 2 refused at send time |
| 20 | Third inbound after two automated replies, contains legal + opt-out | OPT_OUT, LEGAL | Suppress both reasons; escalation `legal`; no reply (ceiling irrelevant) |

Fixture 18 note: the day-8 offset (§1) guarantees an email-3 slot for every send day absent holidays; a holiday collision skips it rather than extending the preview.

## 10. Metrics (daily report "Pipeline")
- Events carry Central dates; the report (Riyadh 08:00) aggregates by Central date. Cohort = prospects by email-1 date.
- `emails_sent`: accepted outreach sends (250), excluding internal/warm-up and automated replies.
- `unique_prospects_contacted`: distinct `prospect_id` with ≥1 accepted email 1.
- `replied_prospects`: distinct prospects with ≥1 human inbound (not DSN/auto-response); `reply_messages` reported separately.
- `positive_prospects`: distinct prospects whose first human reply resolved to ORDER, FAQ_REPLY, ACK_QUESTION or NO_CALL*; refund/legal/negative/not_now/uncertain are not positive.
- `sample_views`: distinct prospect slugs with ≥1 page view from the host's cookie-free analytics, excluding `internal_domains` IP ranges and known bots as classified by that provider; if no analytics source is configured, report `n/a`, never 0.
- `paid`: distinct `order_id` with a confirmed webhook; refunds reported as `refunded` separately.
- Rates = distinct prospects ÷ `unique_prospects_contacted`; never message counts.
- DEC-007 day-30 checkpoint uses these definitions on the pilot cohort only.

## 11. Changes from revision 1 (REV-009 mapping)
R01 → §5.4 ordered rows with combined actions; refund/legal first. R02 → §5.1 header-only automatic detection, §5.2 extraction, whole-word matching, keyword lists revised. R03 → NOT_NOW class, 60-day rule, human-vs-automatic eligibility. R04 → §1 Chicago calendar, holidays, slot roll-forward, expiry recheck, preview date fixed; reply clock separate. R05 → §3.1 shared-domain rule, normalization, §3.2 GET/POST semantics, acknowledgement policy. R06 → §4.3 windows, denominators, attribution, inactive rule without a feed, cap scope, §4.4 atomic send. R07 → §4.1 routing, §4.2 pass criteria, warm-up age, internal exchanges marked unvalidated. R08 → copy aligned with offer rev 2; exact templates; deterministic FAQ. R09 → §6 acknowledgements per class, queue IDs, dedup, overdue reporting. R10 → §10 distinct-prospect rates, dedup, time zones, `n/a` views. R11 → §8.4 self-serve gate, no fallback; §0 config validation. R12 → §2 functional opt-out test, processors, targeting gate, UK out of scope. Capacity sentence removed; capacity is whatever §4.2 caps allow.

## 12. Revision 2.1 amendments (binding; resolve REV-010 F1–F5 and clarifications). Where §§0–11 conflict with this section, this section wins.

**A1 — Matching order and negation (F1).** Evaluate in this order on `body`: (1) OPT_OUT, LEGAL, REFUND; (2) NEGATIVE and NOT_NOW; remove every matched NEGATIVE/NOT_NOW span from `body` before step 3; (3) temporal rule: if NEGATIVE matched and the original `body` contains any of {`right now`, `at the moment`, `for now`, `at this time`, `currently`, `this year`, `later`, `maybe`} → clear NEGATIVE and set NOT_NOW; (4) INTERESTED, CALL, QUESTION on the reduced body. Consequences: `not interested` → NEGATIVE only; `not interested right now` → NOT_NOW only. FAQ `contract` keywords become {`contract`, `cancel`, `cancellation`, `commitment`, `lock in`, `lock-in`, `month to month`, `month-to-month`}; `monthly` is removed. Fixture 4 text becomes `Interested, but I want a refund first` (INTERESTED + REFUND → row 3). Fixture 8 → NOT_NOW → ACK_NOT_NOW. Fixture 10 → no FAQ match → ACK_QUESTION + queue.

**A2 — Terminal states and reply arbitration (F2).** States `suppressed`, `paid`, `expired` are terminal: no later rule changes them. `not_now` stores `not_now_until = now + 60 days`; outreach is refused while `now < not_now_until`. "A human reply sets state → replied" applies only when the current state is `active`. §5.4 row 1 is terminal: after writing suppression, exactly one of: LEGAL → escalation `legal`, no reply; else REFUND → escalation `refund` + ACK_REFUND; else ACK_UNSUB (reply-keyword opt-outs only). No sales branch runs after OPT_OUT. `Unsubscribe. I was interested.` → suppressed, ACK_UNSUB, no ORDER. `Unsubscribe. Refund please.` → suppressed, escalation refund, ACK_REFUND only. Service replies (all §5.5 templates and owner-written replies) are exempt from §1's outreach gates (send days, windows, expiry, state = active) but count toward the mailbox daily cap (§4.2); when the cap is reached the reply is deferred to 08:00 CT next day, and no template promises a faster time than "next business day" except none. Outreach sends never exceed DEC-003 caps to make room for replies; replies take priority within the cap.

**A3 — Expiry authority (F3).** `expiry_utc` is fixed at preview generation (generation date + 14 days, 00:00 UTC) and is never rewritten. `first_send_at` is stored separately. If email 1 has not been sent within 24 h of generation, the batch is **regenerated as a new batch** (new slugs, new generation date, old previews removed) with a log line; existing deployed previews are never re-dated. Day-8 cadence for email 3 stands (owner decision DEC-008); if no slot exists before `expiry_utc − 24h`, email 3 is skipped and logged. The 2026-09-22 test previews keep 2026-10-06T00:00Z and are not used for outreach.

**A4 — Complaints and unknown SMTP outcomes (F4).** Complaint rule (replaces §4.3's rate): per mailbox, rolling 7 Central days: ≥1 complaint event with ≥50 accepted sends in the window → pause 48 h; ≥2 complaint events in the window regardless of volume → disable until the owner re-enables. A reply-based complaint (§3.1 `complaint`) is a complaint event and additionally pauses that mailbox 24 h. Send transaction (replaces §4.4): pre-generate `message_id`; write an intent row `status=sending` durably **before** SMTP; on 250 → `status=sent`; on definite failure → `status=failed`; on timeout/ambiguous → `status=unknown` and the prospect is held (no further sends). Reconciliation every 30 min: for `unknown`, search the mailbox's Sent folder (IMAP) by `message_id`; found → `sent`; not found after 24 h → `failed`. A send is scheduled only if no row exists for `(prospect_id, email_no)` in {sending, sent, unknown}; one retry is allowed after `failed`. Caps count rows in {sending, sent, unknown}.

**A5 — Automatic-origin signals (F5).** Origin signals are only: `Auto-Submitted` present and ≠ `no`; `X-Autoreply`; `X-Autorespond`; `Precedence: auto_reply`; DSN structure per §5.1. `X-Auto-Response-Suppress` and `Precedence: bulk|junk` are **not** origin signals; a message carrying them is processed normally for flags and state, but no automated reply is sent to it (owner queue instead when a reply would have been due). Suppression and escalation always apply.

**A6 — Clarifications.** DSN correlation (embedded original `Message-ID`/`Original-Recipient`) runs before the unknown-sender rule; a missing inbound `Message-ID` is replaced by `sha256(From, Date, first 512 bytes of body)` and processed once. Mailbox index = `int(sha256(prospect_id).hexdigest()[:8], 16) mod N` over active mailboxes in config order; a prospect moves queued → active at its first `sending` row. Config adds `prospect_state`, `region` per prospect, `complaint_feed` (bool) and `analytics_exclude_ips` (CIDR list). With more than two FAQ matches, keep the two whose first keyword occurrence appears earliest in `body`. RFC 8058 gate: the DKIM `h=` tag must include `list-unsubscribe` and `list-unsubscribe-post`, and the POST endpoint must accept a direct POST with no redirect, cookie or session (tested in §8.6). Metrics: `paid_prospects` = distinct prospects with ≥1 confirmed order (a prospect with two orders counts once); reporting window = Central days fully closed at report time; owner-response and launch clocks start per offer rev 2 §4 (payment and confirmation email, whichever later).

Tests, not prose, are the arbiter from here: TASK-009 implements §§0–12 with automated tests for §9's twenty fixtures (as amended), Codex's additional cases (`Unsubscribe. I was interested.`, `Unsubscribe. Refund please.`, plain `Not interested`, `X-Auto-Response-Suppress` opt-out, DSN without outer thread headers, missing Message-ID, SMTP timeout then IMAP-found), and the calendar variants.

**A7 — Adopted from TASK-009 failing tests (session 1), binding.**
- A4 amendment: an SMTP-accepted send whose Sent copy is absent after 24 h stays `unknown` and the prospect stays held; it becomes `failed` (retry-eligible) only on definite non-acceptance (SMTP 4xx/5xx or connection refused before DATA) or explicit owner reconciliation via a queue item `Q-{prospect_id}-unknown-send`. SMTP acceptance never proves an IMAP copy exists.
- A6 amendment: the owner-response clock for every queue item starts at inbound receipt time; the later(payment, confirmation) clock applies only to launch and automatic-refund eligibility (offer rev 2 §4).
- A6 amendment: when `Message-ID` is absent, the dedup key is `sha256(mailbox_id, provider_uid if available, canonical full message bytes)`; never a body prefix.
Tests in `sender/tests/test_spec_conflicts.py` are the reference for these three rules and must be green once implemented per this section.
