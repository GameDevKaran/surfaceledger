# SurfaceLedger

Find gaps and weak detail in tiled artwork captures.

## Status

This repository contains the initial product documentation. Application development has not started. There is no runnable application, measured benchmark or deployed service yet.

## Intended use

A small archive photographing a large flat poster needs to know whether it captured every region sharply enough before dismantling the setup. A visually pleasing stitched image can hide omissions or weak source detail. SurfaceLedger builds a quality-weighted coverage map and tells the operator which physical region to recapture. Its final deliverable is an auditable capture set and coverage report, not invented restoration.

## Planned workflow

Upload overlapping photographs of one owned planar artwork with four corner markers → OpenCV 5 detects correspondences, rejects outliers and estimates homographies → calculate coverage plus focus/glare masks → select the largest deficient region → capture another photograph → update the map and export a report linking regions to source files. Invalid geometry returns “unable to register,” never green coverage.

## Development

Start with the behavior and boundaries in [Architecture](docs/architecture.md), then establish the fixtures and acceptance checks in [Verification plan](docs/verification-plan.md). Runtime versions, dependency installation, commands and deployment instructions will be added alongside working code. No installation command is available at this stage.

Keep credentials in local ignored files or the deployment secret store. Do not commit user data, provider tokens or private evaluation records.

## License

Original application code and these documents use the [MIT license](LICENSE). Future dependencies, models, datasets and media retain their own licenses and must be reviewed before inclusion.
