# SurfaceLedger: architecture

The Python worker, browser interface and AWS Lambda deployment are implemented. The public release was verified on 25 October 2026; see [release evidence](LIVE_RELEASE.md).

The input manifest identifies a rectified reference, physical board dimensions and original captures. ORB descriptors and ratio-tested, unique matches feed RANSAC homography estimation. Consensus, reprojection error, spatial spread and projected-boundary checks reject weak geometry. The first milestone requires an already rectified reference; automatic corner-marker detection is deferred.

Each registered capture contributes a projected validity mask and a separate focus/glare qualification mask. Coverage is the union of actual source samples. Reports retain per-cell source contributions and input hashes. Nearest-neighbor previews never fill gaps; a source-index raster identifies the input behind every supported preview pixel. Four-connected deficient cells define the largest physical region needing recapture.

One stateless AWS Lambda container serves the browser interface and runs the real Python/OpenCV pipeline. The Function URL adapter accepts bounded image data, uses generated request-local filenames, runs a bounded vision subprocess and deletes temporary files before responding. Optional IndexedDB persistence and downloaded files keep captures with the user; there is no S3 image store or shared result database. The execution role writes only this function's log streams. Calibration and overlap remain explicit. No curved objects, photogrammetric 3D, OCR, generative filling or archival certification. Input is owned artwork/printed patterns.

## Failure handling and data boundaries

Preserve original inputs and make unavailable evidence explicit. Provider failures must return a visible unresolved state. Decisions that change user or provider state need the confirmation specified above. Record source versions and operation identifiers without exposing credentials.

## Implementation record

`surfaceledger/pipeline.py` owns registration, coverage and exports; `fixtures.py` creates owned synthetic development targets with authored truth; `__main__.py` exposes `version`, `fixtures` and `analyze`. Requirements pin OpenCV 5 and NumPy. The CLI refuses OpenCV 4. No provider SDK or credentials are needed for local development. See `LOCAL_MILESTONE.md` for verification and remaining gates.
