# Input schema v1

CSV must have these exact columns, in order (UTF-8, standard CSV quoting):

```text
business,city,state,category,website,phone,services,source_url,checked_on,maps_url,maps_status
```

| Field | Constraint |
|---|---|
| business | Actual public business name, 2–120 characters; escaped, never interpreted as HTML |
| city/state | Houston / TX means **service area**, not necessarily registered office |
| category | plumbing or plumbing_hvac |
| website | Official public HTTPS site |
| phone | Public business number in +1 E.164, or blank if not verified |
| services | Pipe-delimited subset of build.py SERVICES, independently checked on source_url |
| source_url | Official HTTPS page supporting name, service area, category, listed services and phone if present |
| checked_on | ISO date of manual source check, not later than today |
| maps_url | Optional observed Google Maps link; never a manufactured place ID |
| maps_status | pending or checked; checked requires an inspected, matching Maps record and link |

Rows normalize to JSON in `records.json`: services become an array, slug is an ASCII
name plus eight SHA-256 characters, style is SHA-256 modulo three, and `sources`
maps each supplied business fact to the cited official page. One page per row is
intentional in v1; split-source ingestion is not claimed. Source URLs are audit
references, not machine proof of truth. Human review remains necessary.

This is a generator fixture, not TASK-005's verified-email CSV. No email addresses,
ratings, opening hours, reviews, third-party photos or certifications are supported
in v1. Do not fill missing values from guesses. New services require source review
before changing the allowlist. Basic input validation is not a copyright license.
