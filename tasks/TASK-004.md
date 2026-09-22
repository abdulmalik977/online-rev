---
id: "TASK-004"
title: "Fix reviews index drift found in REV-002"
owner: "codex"
status: "done"
goal: "Make --review safe on a fresh clone or restored DB; this is a defect in delivered scope, not new infrastructure (DEC-004 respected)"
evidence: "REV-002; scripts/watchdog.py scan/record_counter; scripts/test_operations.py test_reviews_rebuild_after_database_loss_and_avoid_restored_ids; 7 rule + 18 operations tests pass"
definition_of_done: "scan() rebuilds reviews table from reviews/REV-*.md front matter like sync_tasks; REV number = max(files, db)+1; DB insert happens before the review file is written or the file is removed on failure; --review refuses a third changes round at the command; one regression test that deletes the DB, re-scans, and runs --review successfully; <=40 lines"
success_metric: "New regression test passes; all existing 24 tests pass; git status clean after smoke sequence"
attempts: 1
review_round: 1
quota_budget: 20
created: "2026-09-22T08:00:00+00:00"
updated: "2026-09-22T08:26:47+00:00"
---
Reviewer: claude. One session. Do not touch anything outside the named functions.

## Implementation evidence - attempt 1

- Applied Claude's supplied patch with git am and pushed it first (fa74578).
- Attempt registered through --attempt before implementation; counters remain script-owned.
- scan now rebuilds reviews from REV-*.md front matter and removes stale index rows.
- record_counter selects max(review IDs in files, review IDs in SQLite) + 1.
- The SQLite review insert precedes writing its Markdown file.
- A third changes decision is refused before counters, history, or review files change.
- Production edits are restricted to scan and record_counter: 12 added lines, under 40.
- One new regression first failed on missing REV-002, then passed after the fix.
  It also exercises a DB-only higher ID, database deletion in a temporary fixture,
  re-scan, and a successful subsequent review using the rebuilt index.
- All 25 tests pass (7 rules + 18 operations). The existing third-review test now
  asserts the newly requested admission refusal; stale/context fixtures reflect
  TASK-001 being done in Claude's patch. No other production functions changed.
- Submitted for Claude review; no self-approval or extra infrastructure work.
