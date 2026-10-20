# Capture-set contract

This milestone accepts one **flat** surface and a geometrically rectified overview of it. The overview is used only to find feature correspondences. Its pixels never count toward capture coverage or appear in the exported preview.

1. Place four visible corner markers just outside the artwork. Keep their placement fixed.
2. Take a straight-on overview and rectify/crop it to the four artwork corners, in top-left, top-right, bottom-right, bottom-left order. This first milestone requires an already rectified reference; automatic corner-marker detection is not implemented.
3. Record the physical width and height of that rectangle in millimetres. These dimensions determine the recapture coordinates.
4. Take overlapping detail photographs. Keep focus/exposure fixed where practical. Include distinctive detail shared with the overview; blank and repeated patterns may be rejected.
5. Keep the reference and captures together, and write a capture-set JSON:

```json
{
  "schema_version": 1,
  "evidence_kind": "camera_capture",
  "planar_surface_confirmed": true,
  "reference": "overview.png",
  "width_mm": 768,
  "height_mm": 512,
  "cell_px": 64,
  "captures": [
    {"id": "left-detail", "file": "left.png"},
    {"id": "right-detail", "file": "right.png"}
  ]
}
```

The operator's planarity confirmation is an assumption, not an algorithmic certification. Lens distortion, folded paper, repeated texture, camera motion and reflections can invalidate that assumption or registration. Use a flat, matte, owned target for the initial camera evaluation.

Images are limited to 25 MB and 16 megapixels each, with 1–32 captures. File paths must stay inside the capture-set directory. Original files remain unchanged. Use a fresh output directory for each run.

The 32-pixel focus windows and coverage thresholds are frozen in `POLICY` version `controlled-planar-v1`. Laplacian variance is a heuristic; smooth artwork can appear weak, and white artwork can resemble glare. A “controlled quality thresholds met” result is not archival certification, a claim of complete physical resolution, or proof that a camera test has occurred.
