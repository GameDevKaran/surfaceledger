# SurfaceLedger continuation checkpoint

Updated 21 October 2026. Scope: working local browser application and private ECR image uploaded; AWS application deployment blocked by IAM. No live AWS vision execution is verified.

**Current milestone:** stateless upload/API and browser interface added. Seven new backend tests passed, including actual HTTP/OpenCV processing and a targeted emulator-label regression check; nine browser workflow checks passed, including real file-picker uploads, known gap, recapture, rejection, save/reload, export, deletion and isolated/mobile browsers. All inputs in automated checks were synthetic; no camera or AWS verification claim.

**Release preparation:** pinned AWS Python 3.14/Linux image, private ECR and isolated Lambda CloudFormation templates prepared. The original application template was accepted by the read-only CloudFormation validation API. The Linux image/emulator checks passed, including actual processing under 1 GB/0.6 CPU and cleanup. Image source `8161eae7b8de9cb54c33e285329ebe5cca272602`, immutable image digest `sha256:2ace0b2465ae4bf8023cc93de4771de439f4cddb4907b474ebfb93589478d498`. Preserve `.local/browser/` and `.local/container/` evidence; do not repeat passed suites or rebuild the unchanged image. The private `surfaceledger` ECR repository now contains this tested image. The existing account has total concurrency 10; a one-instance reserved limit is not available under the documented 100-unreserved rule. No quota change was made.

**Approved spending:** owner-approved USD10 total SurfaceLedger AWS usage before credits through 16 December 2026; reference `user-20261021-surfaceledger-aws-usd10`. This does not authorize source publication or unrelated resources.

**Current blocker and next step:** `surfaceledger-application` is `ROLLBACK_COMPLETE` after `iam:CreateRole` was denied to the deployment user. Saved `.local/aws-initial-stack-events.json` shows the attempted role and log group deleted; no application Lambda was created. The owner/admin handoff is in the private planning workspace at `configuration/surfaceledger-iam/`: create dedicated `surfaceledger-runtime` with Lambda trust and own-log-stream permissions, then grant the deployment user only exact-role `GetRole`/Lambda-conditioned `PassRole`. `deployment/application.json` now requires `ExecutionRoleArn` and creates no IAM role. Once the external role is ready, verify ownership/account, recover only the failed application-stack record, reuse the uploaded image and deploy. Then run the existing live browser verifier and retain AWS request IDs/runtime/source evidence. No revised-template cloud validation or new deployment has been performed in the IAM handoff milestone.

## Preserved local vision milestone

**Completed:** actual OpenCV 5.0.0 pipeline, owned synthetic target generator, authored geometry/missing-region truth, projective registration, focus/glare coverage, largest recapture region, JSON/provenance and source-only PNG exports. Existing repository history and MIT license preserved.

**Verified:** 17 tests passed in 10.49 seconds on Python 3.14 / NumPy 2.4.3 / OpenCV 5.0.0. `pip check` found no broken requirements. CLI `version`, fixture generation, missing-strip analysis and successful recapture ran. Both board seeds and the projective pose passed. `git diff --check` passed. These are synthetic/local results.

**Recovery:** `.venv` contains pinned dependencies; `.local/verified-fixtures`, `.local/verified-gap`, and `.local/verified-recaptured` retain local evidence. Use the README commands with fresh output directories to reproduce. The pytest temporary-directory workaround is documented in `docs/LOCAL_MILESTONE.md`.

**Completed next slice:** upload/review interface connected; see `docs/WEB_MILESTONE.md`. The approved SurfaceLedger AWS release must still run the real OpenCV pipeline. The Amazon GCP allowance does not apply.

**Not yet verified:** real camera captures, held-out accuracy targets, actual AWS computation, public deployment, upload/session/job-failure behavior, final demo or submission.

**Source privacy:** keep this repository private. Public source requires explicit owner authorization for SurfaceLedger. No Devpost navigation or submission is authorized; the owner handles it manually.
