# Dependency notices

SurfaceLedger's original code and generated fixture patterns are MIT licensed.

- OpenCV 5 and the pinned `opencv-python-headless` distribution: Apache 2.0; the packaging repository also retains its own MIT notices. The installed wheel includes its license and third-party license files. See [OpenCV's Python packaging license information](https://pypi.org/project/opencv-python-headless/5.0.0.93/) and [OpenCV source](https://github.com/opencv/opencv).
- NumPy: BSD-3-Clause, with bundled component notices retained in its distribution. See [NumPy licensing](https://numpy.org/doc/stable/license.html).
- Development dependencies retain their installed distribution notices. They are not copied into this repository.

Do not remove wheel license files when packaging the worker. In particular, bundled video/media dependencies may have additional terms; this application does not require video decoding.
