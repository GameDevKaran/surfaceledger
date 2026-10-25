# SurfaceLedger public release — 25 October 2026

Application: https://2gflnfptor3334dyrlb6fy4jxy0jdiny.lambda-url.us-east-1.on.aws

Repository: https://github.com/GameDevKaran/surfaceledger (private, MIT).

The existing tested image was deployed to AWS Lambda through CloudFormation. Image source: `8161eae7b8de9cb54c33e285329ebe5cca272602`. Immutable image digest: `sha256:2ace0b2465ae4bf8023cc93de4771de439f4cddb4907b474ebfb93589478d498`. The function was read back Active with a Successful update and the exact image/source. Documentation changes after that commit do not imply a different deployed application.

## Verified behavior

Nine browser checks passed against public HTTPS: gap analysis, added recapture, IndexedDB save/reload, downloaded report fidelity, 390px layout, rejected capture, explicit deletion, real file-picker upload and an independent browser's empty state. Seven API/security/artifact checks passed: actual Lambda runtime/source provenance, response protections, all three served UI assets matching the image source, foreign-origin rejection, missing-origin rejection, malformed JSON and invalid capture-set errors. Earlier local checks were retained, not repeated.

All four browser-triggered analyses used OpenCV 5.0.0 and NumPy 2.4.3 on AWS. Their returned request IDs matched CloudWatch execution reports:

| Input | Source coverage | Supported cells | Outcome |
|---|---:|---:|---|
| Authored synthetic gap | 82.49% | 80 / 96 | Recapture required |
| Added synthetic bridge capture | 99.35% | 96 / 96 | Controlled thresholds met |
| Blank synthetic detail | 0% | 0 / 96 | Registration rejected |
| Synthetic images through file picker | 82.49% | 80 / 96 | Upload path and analysis verified |

The UI rounds percentages to one decimal place. All 96 cells passing does not mean every pixel was captured. These are synthetic development measurements, not real-camera accuracy or a user study. The original real-camera/held-out evaluation remains unmeasured.

## Security and persistence

The dedicated execution role trusts Lambda and can write only this function's log streams. Public permissions are restricted to this Function URL. The application checks its exact canonical origin, limits image dimensions/bytes/count, uses fixed internal filenames and enforces a 25-second analysis budget. The function has 1 GB memory and a 40-second invocation timeout. Content policy, MIME protection and rejection of foreign/missing origins were checked on the public service.

Server processing is request-local; optional saved captures/reports live in the user's browser. Save/reload, explicit deletion and browser isolation passed. This is a bounded release check, not a complete penetration test or guarantee against deliberate public API usage.

## Demonstration — about 150 seconds

1. Open the public app. Point out the OpenCV 5 / AWS Lambda runtime label and the clearly labeled synthetic sample.
2. Load the gap and inspect coverage. Show the missing strip, 82.5% displayed coverage and suggested recapture region.
3. Add the sample recapture and inspect again. Show 99.4% displayed coverage and 96 supported cells; explain the remaining pixel-coverage limitation.
4. Try the rejected capture. Show zero coverage and the registration explanation.
5. Save a successful capture set, reload and download its report. Show actual input hashes, runtime/source provenance and the AWS request ID.
6. Clear the saved set and reload. State the limits: planar input, prepared rectified overview, fixed quality thresholds and no generative filling.

Desktop/mobile screenshots, exported JSON, raw technical video, provider configuration and request-matched logs are preserved under ignored `.local/live-browser/`. Final narration, owned-camera evidence and any personal experience must reflect what the owner actually does.
