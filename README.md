# SurfaceLedger

Find gaps and weak detail in tiled artwork captures.

## Status

**Live application:** https://2gflnfptor3334dyrlb6fy4jxy0jdiny.lambda-url.us-east-1.on.aws

Public AWS Lambda execution was verified on 25 October 2026: nine browser workflow checks and seven API/security/artifact checks passed. The deployed image runs OpenCV 5.0.0 and NumPy 2.4.3; four actual analysis request IDs match AWS execution logs. Upload photographs, inspect measured coverage, add a recapture, save locally and export source-backed evidence. Verification used owned synthetic fixtures; real camera accuracy remains unmeasured. See the [release evidence and demonstration](docs/LIVE_RELEASE.md). Source stays private until the owner explicitly authorizes publication of this project.

## Intended use

A small archive photographing a large flat poster needs to know whether it captured every region sharply enough before dismantling the setup. A visually pleasing stitched image can hide omissions or weak source detail. SurfaceLedger builds a quality-weighted coverage map and tells the operator which physical region to recapture. Its final deliverable is an auditable capture set and coverage report, not invented restoration.

## Current workflow

Supply a rectified overview and overlapping detail photographs → OpenCV 5 detects correspondences, rejects outliers and estimates homographies → calculate source coverage and conservative focus/glare masks → select the largest deficient region → add a photograph and rerun → export a report linking regions to original files. Invalid geometry returns “unable to register” and contributes zero coverage.

## Development

Start the browser application after installing the Python requirements:

```powershell
./.venv/Scripts/python.exe -m surfaceledger.web
```

Open `http://127.0.0.1:8784`. “Load sample gap” loads explicitly synthetic inputs; “Inspect coverage” runs actual OpenCV. Add the sample recapture and inspect again. For your own inputs, provide an already rectified overview, overlapping PNG/JPEG details, physical dimensions and planarity confirmation. Limits are shown in the interface. Nothing is retained on the server; optional local saving uses IndexedDB.

Browser checks: `npm ci`, `npx playwright install chromium`, then `npm run test:browser`. Python tests: `python -m pytest -q`. For a deployed release, set `SURFACELEDGER_VERIFY_URL` to its exact authorized Lambda URL before running the browser verifier. This invokes real computation and needs the approved release allowance.

See [browser milestone](docs/WEB_MILESTONE.md) and [AWS release procedure](docs/AWS_RELEASE.md).

Use Python 3.14 and an isolated environment. On Windows:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
./.venv/Scripts/python.exe -m surfaceledger version
./.venv/Scripts/python.exe -m surfaceledger fixtures --output .local/demo-fixtures
./.venv/Scripts/python.exe -m surfaceledger analyze .local/demo-fixtures/board-1/gap.json --output .local/demo-gap
./.venv/Scripts/python.exe -m surfaceledger analyze .local/demo-fixtures/board-1/recaptured.json --output .local/demo-recaptured
./.venv/Scripts/python.exe -m pytest -q
```

On Linux/macOS replace `./.venv/Scripts/python.exe` with `.venv/bin/python`. Use fresh output directories for subsequent runs; existing evidence is never overwritten. If the host's default pytest temporary directory is inaccessible, set `PYTEST_DEBUG_TEMPROOT` to an existing, writable local directory.

Open `report.json` for registration evidence, per-cell coverage, source SHA-256 hashes, frozen thresholds and the largest recapture region in pixels and millimetres. `source-preview.png` uses only nearest-neighbor source samples; unsupported regions remain transparent. `source-index.png` records the 1-based capture index for each preview pixel, with zero meaning unsupported. `coverage.png` and `quality.png` distinguish photographed detail from detail meeting the controlled quality thresholds.

The overview calibrates geometry only and never supplies coverage. Automatic corner-marker detection is not implemented. See [calibration and input format](docs/calibration.md), [verification record](docs/LOCAL_MILESTONE.md) and [architecture](docs/architecture.md).

Keep credentials in local ignored files or the deployment secret store. Do not commit user data, provider tokens or private evaluation records.

## Development approach

Developed through AI-assisted coding and ChatGPT-assisted research. Verification results and their limits are documented in this repository.

## License

Original application code, documentation and generated fixture patterns use the [MIT license](LICENSE). [Dependency notices](THIRD_PARTY_NOTICES.md) preserve their separate licensing.
