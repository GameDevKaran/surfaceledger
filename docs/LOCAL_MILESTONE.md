# Local OpenCV 5 milestone — 20 October 2026

Implemented: capture-set input → ORB feature correspondence → RANSAC homography → registration rejection → source coverage and focus/glare quality coverage → largest deficient connected region → JSON/provenance and PNG exports. The recapture target is inside a deficient cell, including nonrectangular regions.

Actual local runtime: `opencv-python-headless==5.0.0.93`, `cv2.__version__ == 5.0.0`, `numpy==2.4.3`, Python 3.14. Dependencies are pinned. The runtime refuses an OpenCV major version other than 5.

OpenCV 5 availability was checked against the [official release page](https://opencv.org/release/opencv-5-0-0/) and the [OpenCV-maintained PyPI package](https://pypi.org/project/opencv-python-headless/5.0.0.93/). The installed binary supplies a build-information hash in every report.

The deterministic generator owns its original pixel patterns. Its two target boards have independently specified translations, a missing strip, a deliberately blurred capture, an authored glare rectangle, a blank rejected input and a projective pose with specified corner geometry. These are **synthetic development fixtures**, not real camera photographs, human evaluation, held-out validation or AWS execution.

## Verification

**Result: 17 tests passed in 10.49 seconds.** `pip check` found no broken requirements. CLI fixture/gap/recapture commands ran successfully; `git diff --check` passed.

Run `python -m pytest -q` after installing the development requirements. On this Windows host, its pre-existing default pytest temporary directory was inaccessible; verification used an ignored directory inside this repository through `PYTEST_DEBUG_TEMPROOT`. No system directory permissions were changed.

Tests cover registration against authored geometric truth, gap recovery, blur/glare handling, source-only preview and source-index agreement, zero coverage from rejected input, faulty geometry, version refusal, path containment, invalid manifests, evidence preservation and recapture targeting.

The controlled board-1 run registered both supplied crops, reported coverage `0.8249`, and selected the authored missing strip `[320, 0, 448, 512]`. Adding the bridge crop raised coverage to `0.9935`; all 96 cells met the fixed thresholds. The remaining excluded boundary pixels remain visible in the pixel masks, so “thresholds met” is not “every pixel captured.”

Generated input/output evidence lives under ignored `.local/`. Recreate it using the README commands; no private images or credentials are committed.

## Remaining release gates

- Implement the upload/review interface and AWS worker delivery using the existing pipeline.
- Obtain specific AWS spending authorization before creating resources or paid execution. The approved $25 GCP allowance covers the three Amazon apps only.
- Execute this real OpenCV 5 computation on authorized AWS infrastructure, recording request/runtime/source evidence.
- Collect owned real camera captures using `calibration.md`, including separate development and held-out sessions. The original 20+20 targets and claimed success rates remain unmeasured.
- Verify public deployment, upload limits, session isolation, job failures, cleanup and demo.
- Keep the repository private. Obtain the owner's explicit SurfaceLedger publication authorization before satisfying any public-source competition requirement.

No AWS API was called and no cloud resource was created in this milestone. No deployment or competition-completion claim is made.
