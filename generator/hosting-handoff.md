# TASK-006 session 3 — commercial deployment handoff

Checked 2026-09-23. **Deployment blocked: no usable hosting account access; no live URLs.** Session 3/3 has been recorded. This is a concrete publication handoff, not a completed deployment or a request to buy hosting. No fourth session is started automatically.

## Host decision

Select **Netlify Free** for this small, static pilot, subject to verifying the owner's actual team plan before upload. Netlify explicitly permits commercial projects on Free. This is eligibility evidence, not an uptime or sales guarantee. [Official commercial-use statement](https://www.netlify.com/blog/introducing-netlify-free-plan/).

Current credit-based Free documentation lists $0/month, 300 monthly credits, a hard limit and no automatic recharge. Production deploys cost 15 credits each; bandwidth and requests also consume credits. The old bandwidth/build-minute figures in the earlier blog are not the current allowance. An active upload plus expiry replacement would consume 30 deployment credits before traffic and any rehearsal; available team credits still need checking. No paid plan, add-on, recharge or domain purchase is authorized here. [Current Netlify plans and credit rates](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/).

Use one dedicated preview site, with ten `/previews/<slug>/` paths. Do not attach the repository root to an automatic public build: it contains company records. Upload only the allowlisted static archive. Do not overwrite an existing unrelated website. Keep checkout disabled until its separate provider work is ready; these are clearly labelled independent concepts, not official business sites.

## Available artifacts

`generator/session-3-results.json` records this session's manifest, hashes and archive checks. Local ZIPs are under `.runtime/session3-bundle/` and can be reproduced from the committed CSV and generator:

```powershell
python generator/expiry_bundle.py --destination .runtime/session3-bundle --preview-date 2026-09-22
```

Use a fresh destination if it already exists. The original date remains **2026-09-22**; deletion deadline remains **2026-10-06T00:00:00Z**. Active archive: ten pages plus six root assets. Expiry archive: six root assets, zero preview pages. Audit JSON, manifests, source CSV and credentials are excluded. If resumed at or after expiry, do not upload the old active archive or silently renew its age.

## Missing access and execution path

No configured Netlify/Cloudflare access was found in the checked process environment and usual local CLI configuration locations. Connected-browser initialization also failed with `CryptUnprotectData failed:2148073483`. No authenticated deploy request was sent. The owner has been asked to configure access locally, without pasting a token into chat. Publication itself is already authorized by the current instruction.

For Netlify, make `NETLIFY_AUTH_TOKEN` available privately to the execution process, or authenticate the CLI locally. Select/create a dedicated site in the owner's **Free** team and record its site ID and HTTPS URL after authentication. A token alone does not prove the team plan or available credits. Never put a bearer token into tracked files, command arguments, run logs or copied API responses.

An always-running execution path is also needed for expiry. Existing `SETUP-CRON` is unresolved; no scheduler was installed. Do not rely on this desktop staying online, a browser timer, the expiry banner, or a claim that Netlify will remove the latest deployment automatically.

## Exact remaining publication procedure

1. Authenticate and inspect the selected team/site. Confirm Free plan, usable credit balance, site ownership and dedicated destination. Check artifact hashes against the session manifest and refuse expired active content.
2. Upload `active.zip` as the complete site through `POST https://api.netlify.com/api/v1/sites/{site_id}/deploys` with `Content-Type: application/zip` and bearer authentication held in memory. Poll `GET /api/v1/deploys/{deploy_id}` until `state=ready`; record site/deploy IDs and public URLs only. Netlify's ZIP method requires the complete tree for each deployment. [Official ZIP deployment API](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#zip-file-method).
3. Check HTTPS and HTTP 200 on every manifest path, independent-concept text, fixed expiry, noindex and actual `Cache-Control: no-store` response headers. Inspect one mobile page per style on the hosted URLs, including any host-injected UI. Confirm no root exposure of source CSV, audit reports or company records. Record actual observations, not just ZIP contents.
4. Rehearse full replacement on a dedicated disposable test destination using `expiry.zip`; verify all ten former routes return 404/410, with no redirect or SPA 200 fallback. Record cache behavior and each URL/status. Rehearsal deployments consume credits too. Do not call a local server test remote verification.
5. Configure the available scheduler for **2026-10-06 00:00 UTC** to publish the expiry ZIP to this same dedicated site, verify readiness and all ten routes, then remove only this task's previously recorded active deployments so their immutable URLs cannot bypass expiry. Record job identity, credential placement outside Git, retry/alert behavior and rehearsal evidence. No cron host or equivalent credentialed execution path is available yet.
6. Netlify does not allow deletion of the latest published deployment, so publish the empty replacement first. Deleting an older deploy makes its permalink return a generic 404. Restrict deletion to recorded TASK-006 deployment IDs after replacement verification; retain the local source/archive for audit. [Official deploy-deletion behavior](https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/#deploy-deletion-requirements).
7. Record ten live URLs plus remote rehearsal/scheduler evidence, then request Claude review. Keep the final deadline execution result pending until that date; a rehearsal proves readiness, not a future event. Legacy manual Maps verification remains 0/10 and must be resolved explicitly before claiming the original task DoD.

The session limit is reached with external prerequisites unresolved. TASK-006 is **blocked**, not `review` or `done`. TASK-005 remains deferred; no outreach, new infrastructure task, account purchase or payment-provider implementation occurred.
