# SurfaceLedger

Find gaps and weak detail in tiled artwork captures.

## Status

The local OpenCV 5 worker is implemented and tested on owned synthetic fixtures. It exports a coverage report, recapture region and source-backed image evidence. AWS execution, a public application and real camera validation remain pending. Source stays private until the owner explicitly authorizes publication of this project.

## Intended use

A small archive photographing a large flat poster needs to know whether it captured every region sharply enough before dismantling the setup. A visually pleasing stitched image can hide omissions or weak source detail. SurfaceLedger builds a quality-weighted coverage map and tells the operator which physical region to recapture. Its final deliverable is an auditable capture set and coverage report, not invented restoration.

## Current workflow

Supply a rectified overview and overlapping detail photographs → OpenCV 5 detects correspondences, rejects outliers and estimates homographies → calculate source coverage and conservative focus/glare masks → select the largest deficient region → add a photograph and rerun → export a report linking regions to original files. Invalid geometry returns “unable to register” and contributes zero coverage.

## Development

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

## License

Original application code, documentation and generated fixture patterns use the [MIT license](LICENSE). [Dependency notices](THIRD_PARTY_NOTICES.md) preserve their separate licensing.
