# SurfaceLedger: architecture

Proposed design; no components have been implemented.

Upload overlapping photographs of one owned planar artwork with four corner markers → OpenCV 5 detects correspondences, rejects outliers and estimates homographies → calculate coverage plus focus/glare masks → select the largest deficient region → capture another photograph → update the map and export a report linking regions to source files. Invalid geometry returns “unable to register,” never green coverage.

Python/OpenCV worker on AWS processes signed uploads from a TypeScript web UI; S3 stores originals and reports with short-lived access. The AWS job is the real computation, not a decorative bucket. Calibration and minimum overlap remain explicit. No curved objects, photogrammetric 3D, OCR, generative filling or archival certification. Input is owned artwork/printed patterns; avoid uploading third-party collections without permission.

## Failure handling and data boundaries

Preserve original inputs and make unavailable evidence explicit. Provider failures must return a visible unresolved state. Decisions that change user or provider state need the confirmation specified above. Record source versions and operation identifiers without exposing credentials.

## Implementation record

Add pinned dependencies, actual component boundaries and operational instructions when the first working slice exists. Document departures from this design with their reason; do not describe planned integrations as verified.
