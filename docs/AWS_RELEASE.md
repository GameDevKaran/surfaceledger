# SurfaceLedger AWS release

**Public AWS deployment verified on 25 October 2026:** https://2gflnfptor3334dyrlb6fy4jxy0jdiny.lambda-url.us-east-1.on.aws . Nine public browser workflow checks and seven API/security/artifact checks passed. Four actual OpenCV analysis request IDs matched CloudWatch execution reports. The existing tested ECR image was reused unchanged; see [release evidence](LIVE_RELEASE.md). The approved app-specific spending scope is preserved in the private release journal.

The smallest complete release is one AWS Lambda container serving the static interface and executing real OpenCV 5, a private ECR repository and seven-day CloudWatch logs. Its isolated runtime role can write only its own logs. No S3, database, model, domain, provisioned capacity or GCP resources are required. Browser persistence and downloaded originals/reports replace the original planned S3 store.

## Prepared artifacts and local checks

- `Dockerfile`: AWS Python 3.14 base, pinned NumPy/OpenCV 5, x86-64.
- `deployment/registry.json`: private immutable ECR images retained on stack deletion.
- `deployment/application.json`: 1 GB memory, 40-second invocation timeout, 25-second analysis limit, 512 MB temporary disk, HTTPS Function URL and explicit publication switch.
- `lambda_handler.py`: HTTP API-v2 request adapter; a local test or container is not live AWS evidence.
- `scripts/verify-browser.mjs`: actual local/live sample, recapture, upload, export, persistence, deletion, isolated-browser and mobile workflow.

Build locally with `docker buildx build --platform linux/amd64 --provenance=false --load -t surfaceledger:local-check .`. This development image has no release-commit claim. A release image must be built from a clean pushed commit with `--build-arg SOURCE_COMMIT=<exact-40-character-commit>`; record its immutable digest.

AWS's [Python image guide](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) documents the supported runtime/emulator. The image handler is `lambda_handler.handler`. For local emulation, expose container port 8080 on a loopback-only host port and set `SURFACELEDGER_PUBLIC_ORIGIN` to the chosen local test origin. Invoke `/2015-03-31/functions/function/invocations` with an HTTP API-v2 event. Do not set a fake AWS function name or describe emulator evidence as cloud execution.

## Exact scope and deployment sequence

Use only the owner's authorized AWS profile `clauserunner-dev`, region `us-east-1`, and privately recorded authorized account. Verify STS account equality before any write. Keep account identifiers, approval evidence and release journal in the private planning workspace or ignored `.local/`; no credentials belong in source.

1. Preserve the recorded USD10 approval and reference above. Check clean local HEAD equals remote main; source remains private. The tested image source can remain the previously verified commit when only deployment documents/templates change.
2. Inspect only proposed names: `surfaceledger-registry` and `surfaceledger-application` stacks, `surfaceledger` ECR/Lambda and `/aws/lambda/surfaceledger` log group. Stop on an unowned conflict. Existing matching stacks must carry `Application=SurfaceLedger` / `ManagedBy=surfaceledger-release`; never adopt or overwrite an unrelated resource.
3. Reuse the existing `surfaceledger-registry` private ECR repository and immutable image digest recorded below. Do not rebuild or repush the unchanged application. No source publication is involved.
4. Have the account owner/admin create the dedicated `surfaceledger-runtime` execution role with Lambda trust and only write access to this application's log streams. The private planning workspace contains the concrete handoff at `configuration/surfaceledger-iam/`. The deployment user needs only `iam:GetRole` and Lambda-conditioned `iam:PassRole` on that exact role, not IAM creation rights. After verifying the supplied role belongs to the authorized STS account, deploy `deployment/application.json` with required `ExecutionRoleArn`, `ImageUri` at the tested digest, exact image `SourceCommit`, the approval reference, and `Publish=false`. The revised template creates no IAM resources and does not require `CAPABILITY_IAM`. For the current `ROLLBACK_COMPLETE` stack, verify its attempted resources were removed before deleting only that failed application-stack record and recreating it. Preserve the separate registry stack and image.
5. Read the returned HTTPS URL. Set `PublicOrigin` to that exact URL without the trailing slash and update `Publish=true`. Both required public invocation permissions are constrained to this function; direct non-URL public invocation is not granted. Do not add wildcard CORS.
6. Wait for a completed stack/function update. Record stack IDs, image digest, source commit, function ARN, URL, configuration and actual timestamps in `.local/aws-release.json`. Preserve completed steps on interruption; read actual state before retrying. For later updates, reuse the established URL and publication settings.
7. Run the browser verifier with the exact URL and no AWS browser authentication. Retain real request IDs/build hashes/commit evidence in analysis responses, screenshots and reports. Verify origin rejection and timeout/invalid-image behavior. Mark live only after successful public checks; never infer it from stack success.

The original application template was accepted by the read-only CloudFormation validation API on 21 October IST. The revised existing-role template was actually deployed on 25 October after the narrow role handoff. The stack reached UPDATE_COMPLETE and Lambda configuration was read back Active/Successful with the expected source and immutable image.

Local Linux image verification subsequently passed for source `8161eae7b8de9cb54c33e285329ebe5cca272602`; digest `sha256:2ace0b2465ae4bf8023cc93de4771de439f4cddb4907b474ebfb93589478d498`. The actual handler, static UI, OpenCV subprocess, origin guard and temporary cleanup worked under 1 GB/0.6 CPU/read-only root. The emulator label is explicitly local, including when the emulator supplies AWS-shaped request IDs. No live AWS processing is inferred.

The same digest is deployed from the private `surfaceledger` ECR repository. Saved `.local/aws-initial-stack-events.json` preserves the earlier rollback and deleted attempted resources; only that empty owned failed-stack record was recovered. The dedicated role trusts Lambda and writes only its own log streams; the deployment user received only exact-role GetRole and Lambda-conditioned PassRole. Account-wide administration was not granted.

## Quota and cost boundary

The authorized account's read-only Lambda settings returned total concurrency **10**, all unreserved. AWS documents that reservations must leave 100 unreserved, so this plan does **not** claim a one-instance reserved limit. No quota increase or shared-account change is requested. Invocations share the existing account quota; the application has one analysis subprocess per execution environment. Origin checks protect browser requests but do not prevent deliberate public API usage. [Reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html).

Approved allowance: **USD10 total AWS usage before credits, through 16 December 2026**, SurfaceLedger only, including deployment verification, ECR, Lambda, logging and delivery; reference `user-20261021-surfaceledger-aws-usd10`. Estimate **USD2–8** for up to 1,000 analyses, up to 25 billed seconds at 1 GB each, 20,000 additional small interface/health requests, at most two stored images totaling 2 GB, and modest logging/egress. The estimate conservatively ignores free-tier and unverified promotional credits. More traffic or failures can cost more; this is an approval ceiling, not a provider-enforced billing cap.

Compute for the 1,000 analyses is about USD0.42 using USD0.0000166667/GB-second; request charges are USD0.20/million, and private image storage is USD0.10/GB-month. Remaining estimate headroom covers cold starts, interface invocations, logs and delivery. [Lambda pricing](https://aws.amazon.com/lambda/pricing/), [ECR pricing](https://aws.amazon.com/ecr/pricing/).

Keep a private usage record during release checks and inspect this application's actual invocation/duration/log/image usage during active work. Stop additional operator-driven paid work and ask before an observed/projected allowance overrun; do not silently expand spending or disable judged apps. There is no unattended cost monitor or guaranteed billing cap in this milestone.

## Remaining evidence

Public AWS execution, deployment and browser verification are complete. Real owned-camera validation, judging access and owner media remain open. Keep the repository private until explicit per-project publication authorization; judge access is managed by the owner.
