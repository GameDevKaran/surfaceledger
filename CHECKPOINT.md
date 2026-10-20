# SurfaceLedger continuation checkpoint

Updated 21 October 2026. Scope: working local browser application; no cloud execution.

**Current milestone:** stateless upload/API and browser interface added. Seven new backend tests passed, including actual HTTP/OpenCV processing and a targeted emulator-label regression check; nine browser workflow checks passed, including real file-picker uploads, known gap, recapture, rejection, save/reload, export, deletion and isolated/mobile browsers. All inputs in automated checks were synthetic; no camera or AWS verification claim.

**Release preparation:** pinned AWS Python 3.14/Linux image, private ECR and isolated Lambda CloudFormation templates prepared. Application template accepted by the read-only CloudFormation validation API. The Linux image/emulator checks passed, including actual processing under 1 GB/0.6 CPU and cleanup. Image source `8161eae7b8de9cb54c33e285329ebe5cca272602`, local manifest digest `sha256:2ace0b2465ae4bf8023cc93de4771de439f4cddb4907b474ebfb93589478d498`. Preserve `.local/browser/` and `.local/container/` evidence; do not repeat passed suites without a relevant change. The AWS read-only preflight found no collision for the two intended stack names, ECR repository or Lambda function. The existing account has total concurrency 10; a one-instance reserved limit is not available under the documented 100-unreserved rule. No quota changes or paid resources were made.

**Next:** SurfaceLedger-only USD10 spending approval through December 16 is requested from the concrete `docs/AWS_RELEASE.md` proposal and is pending. Do not infer consent from elapsed time or a generic continue. After approval, deploy, run the existing browser verifier against the actual public HTTPS URL, and retain AWS request IDs/runtime/source evidence. Never relabel local tests as cloud tests. Real owned camera evaluation remains separate.

## Preserved local vision milestone

**Completed:** actual OpenCV 5.0.0 pipeline, owned synthetic target generator, authored geometry/missing-region truth, projective registration, focus/glare coverage, largest recapture region, JSON/provenance and source-only PNG exports. Existing repository history and MIT license preserved.

**Verified:** 17 tests passed in 10.49 seconds on Python 3.14 / NumPy 2.4.3 / OpenCV 5.0.0. `pip check` found no broken requirements. CLI `version`, fixture generation, missing-strip analysis and successful recapture ran. Both board seeds and the projective pose passed. `git diff --check` passed. These are synthetic/local results.

**Recovery:** `.venv` contains pinned dependencies; `.local/verified-fixtures`, `.local/verified-gap`, and `.local/verified-recaptured` retain local evidence. Use the README commands with fresh output directories to reproduce. The pytest temporary-directory workaround is documented in `docs/LOCAL_MILESTONE.md`.

**Completed next slice:** upload/review interface connected; see `docs/WEB_MILESTONE.md`. AWS deployment must run the real OpenCV pipeline after specific spending authorization. The approved Amazon GCP allowance does not apply.

**Not yet verified:** real camera captures, held-out accuracy targets, actual AWS computation, public deployment, upload/session/job-failure behavior, final demo or submission.

**Source privacy:** keep this repository private. Public source requires explicit owner authorization for SurfaceLedger. No Devpost navigation or submission is authorized; the owner handles it manually.
