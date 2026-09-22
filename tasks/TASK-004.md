---
id: "TASK-004"
title: "Fix reviews index drift found in REV-002"
owner: "codex"
status: "todo"
goal: "Make --review safe on a fresh clone or restored DB; this is a defect in delivered scope, not new infrastructure (DEC-004 respected)"
evidence: "REV-002 note: reviews table not rebuilt from Markdown; REV numbering reads files only; sqlite3.IntegrityError UNIQUE after orphan REV file was written"
definition_of_done: "scan() rebuilds reviews table from reviews/REV-*.md front matter like sync_tasks; REV number = max(files, db)+1; DB insert happens before the review file is written or the file is removed on failure; --review refuses a third changes round at the command; one regression test that deletes the DB, re-scans, and runs --review successfully; <=40 lines"
success_metric: "New regression test passes; all existing 24 tests pass; git status clean after smoke sequence"
attempts: 0
review_round: 0
quota_budget: 20
created: "2026-09-22T08:00:00+00:00"
updated: "2026-09-22T08:00:00+00:00"
---
Reviewer: claude. One session. Do not touch anything outside the named functions.
