# Metrics

Target monthly revenue: 10,000 SAR. Recorded revenue: zero; no paid customers.
Reporting currency: SAR for the target; original USD/GBP receipts remain separate.
Do not invent exchange rates or add currencies together.
SQLite metrics stores date, name, value, and unit. Seed values are zero, not traction.
Pipeline: emails_sent, replies, sample_views, paid (daily counts).
Revenue: revenue (daily amount by currency).
Daily quota: reserved execution credits in runs / quota_budget in agents/<agent>.md.
One credit is one CLI-reported turn; tokens are logged for calibration.
Claude/Codex turn granularity differs; rolling provider windows remain a residual risk.
Failed and interrupted launches retain their reservation conservatively.
Report days and quota resets use Asia/Riyadh (fixed UTC+03:00); timestamps use UTC.

TASK-009 integration: when .runtime/sender/pipeline.json exists, the Pipeline line uses
the fully closed America/Chicago day explicitly labelled in that snapshot, per DEC-008.
Missing analytics displays n/a, not zero. Revenue/quota/report naming retain Riyadh days.
The exporter keeps message counts, unique-prospect rates and distinct paid orders separate;
no sender snapshot is produced from fake tests into production reporting.
