# Working browser application — 21 October 2026

The stateless HTTP application uses the existing real OpenCV 5 pipeline. The interface provides reference/detail uploads, physical calibration, source/quality masks, deficient-region guidance, added recapture, per-source evidence, report/PNG/capture-set export, optional IndexedDB save/reload and explicit local deletion.

Seven new backend tests passed across the initial six-test run and the targeted runtime-label follow-up, including actual HTTP/OpenCV processing, origin/body/method/path guards, image-header allocation bounds, fixed internal filenames, invalid input and the Lambda adapter contract. The preceding 17 pipeline tests remain valid; pipeline code was unchanged.

Browser verification uses real HTTP requests, not simulated responses. Saved evidence is `.local/browser/verification.json`, desktop/mobile screenshots and raw WebM. The synthetic gap measured 82.49% source coverage; adding the bridge yielded 99.35% and 96/96 supported cells. A blank capture yielded zero coverage. Local persistence, download fidelity, deletion, separate-browser isolation and mobile layout passed. Local results do not establish AWS execution or real camera accuracy.

No server-side result database or shared image store is needed. Inputs/results live only in a request-specific temporary directory, which is removed before responding; optional persistence belongs to the user's browser. This simplifies the original S3 design while retaining the intended meaningful AWS OpenCV computation when deployed. The overview must already be rectified; automatic marker detection remains unimplemented.

Application bounds are 4 MB request JSON, 2.8 MB decoded images total, 1.5 MB per image, six detail captures, approximately one megapixel for the overview and two per capture. The vision subprocess has a 25-second processing limit; failures return explicit errors. No model or generative filling is used.

The Linux Lambda image also passed actual handler/static-interface/OpenCV processing and foreign-origin rejection checks under 1 GB memory, 0.6 CPU and a read-only root. Temporary capture directories were absent after processing. Image source commit: `8161eae7b8de9cb54c33e285329ebe5cca272602`; local manifest digest: `sha256:2ace0b2465ae4bf8023cc93de4771de439f4cddb4907b474ebfb93589478d498`. This image has not been pushed to AWS.

The first emulator check caught a provenance-label defect: the AWS emulator supplies AWS-shaped identifiers even though it runs locally. The fix defaults to local evidence; only the deployed template opts into the AWS runtime label. The failed and passing reports are retained separately in `.local/container/`; no failed result was described as verified cloud execution.

Pending: owner-approved AWS costs, actual public AWS deployment/browser verification, real owned camera evaluation and final media. Source remains private; the owner handles judge access and Devpost.
