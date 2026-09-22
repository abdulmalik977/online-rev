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
