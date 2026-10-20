# SurfaceLedger: architecture

Local worker implemented; cloud and web components remain planned.

The input manifest identifies a rectified reference, physical board dimensions and original captures. ORB descriptors and ratio-tested, unique matches feed RANSAC homography estimation. Consensus, reprojection error, spatial spread and projected-boundary checks reject weak geometry. The first milestone requires an already rectified reference; automatic corner-marker detection is deferred.

Each registered capture contributes a projected validity mask and a separate focus/glare qualification mask. Coverage is the union of actual source samples. Reports retain per-cell source contributions and input hashes. Nearest-neighbor previews never fill gaps; a source-index raster identifies the input behind every supported preview pixel. Four-connected deficient cells define the largest physical region needing recapture.

The planned Python/OpenCV worker on AWS will process signed uploads from a web UI; S3 will store originals and reports with short-lived access. The substantive AWS computation has not run. Calibration and overlap remain explicit. No curved objects, photogrammetric 3D, OCR, generative filling or archival certification. Input is owned artwork/printed patterns.

## Failure handling and data boundaries

Preserve original inputs and make unavailable evidence explicit. Provider failures must return a visible unresolved state. Decisions that change user or provider state need the confirmation specified above. Record source versions and operation identifiers without exposing credentials.

## Implementation record

`surfaceledger/pipeline.py` owns registration, coverage and exports; `fixtures.py` creates owned synthetic development targets with authored truth; `__main__.py` exposes `version`, `fixtures` and `analyze`. Requirements pin OpenCV 5 and NumPy. The CLI refuses OpenCV 4. No provider SDK or credentials are needed for local development. See `LOCAL_MILESTONE.md` for verification and remaining gates.
