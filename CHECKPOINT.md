# SurfaceLedger continuation checkpoint

Updated 20 October 2026. Scope: complete local vision milestone; no cloud execution.

**Completed:** actual OpenCV 5.0.0 pipeline, owned synthetic target generator, authored geometry/missing-region truth, projective registration, focus/glare coverage, largest recapture region, JSON/provenance and source-only PNG exports. Existing repository history and MIT license preserved.

**Verified:** 17 tests passed in 10.49 seconds on Python 3.14 / NumPy 2.4.3 / OpenCV 5.0.0. `pip check` found no broken requirements. CLI `version`, fixture generation, missing-strip analysis and successful recapture ran. Both board seeds and the projective pose passed. `git diff --check` passed. These are synthetic/local results.

**Recovery:** `.venv` contains pinned dependencies; `.local/verified-fixtures`, `.local/verified-gap`, and `.local/verified-recaptured` retain local evidence. Use the README commands with fresh output directories to reproduce. The pytest temporary-directory workaround is documented in `docs/LOCAL_MILESTONE.md`.

**Next bounded milestone:** connect an upload/review interface to this worker, preserving explicit synthetic/camera labels and per-source evidence. AWS deployment must run the real OpenCV pipeline after a specific spending authorization. The approved Amazon GCP allowance does not apply.

**Not yet verified:** real camera captures, held-out accuracy targets, actual AWS computation, public deployment, upload/session/job-failure behavior, final demo or submission.

**Source privacy:** keep this repository private. Public source requires explicit owner authorization for SurfaceLedger. No Devpost navigation or submission is authorized; the owner handles it manually.
