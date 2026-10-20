# Working browser application — 21 October 2026

The stateless HTTP application uses the existing real OpenCV 5 pipeline. The interface provides reference/detail uploads, physical calibration, source/quality masks, deficient-region guidance, added recapture, per-source evidence, report/PNG/capture-set export, optional IndexedDB save/reload and explicit local deletion.

Six new backend tests passed, including an actual HTTP request through the vision worker, origin/body/method/path guards, image-header allocation bounds, fixed internal filenames, invalid input and the Lambda adapter contract. The preceding 17 pipeline tests remain valid; pipeline code was unchanged.

Browser verification uses real HTTP requests, not simulated responses. Saved evidence is `.local/browser/verification.json`, desktop/mobile screenshots and raw WebM. The synthetic gap measured 82.49% source coverage; adding the bridge yielded 99.35% and 96/96 supported cells. A blank capture yielded zero coverage. Local persistence, download fidelity, deletion, separate-browser isolation and mobile layout passed. Local results do not establish AWS execution or real camera accuracy.

No server-side result database or shared image store is needed. Inputs/results live only in a request-specific temporary directory, which is removed before responding; optional persistence belongs to the user's browser. This simplifies the original S3 design while retaining the intended meaningful AWS OpenCV computation when deployed. The overview must already be rectified; automatic marker detection remains unimplemented.

Application bounds are 4 MB request JSON, 2.8 MB decoded images total, 1.5 MB per image, six detail captures, approximately one megapixel for the overview and two per capture. The vision subprocess has a 25-second processing limit; failures return explicit errors. No model or generative filling is used.

Pending: Linux Lambda-image verification, owner-approved AWS costs, actual public AWS deployment/browser verification, real owned camera evaluation and final media. Source remains private; the owner handles judge access and Devpost.
