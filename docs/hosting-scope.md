# Hosting scope — 18 October 2026

Only Google Cloud project tough-melody-508008-p8 (google-hackathon) is authorized for supporting hosting. Region us-central1 is preferred; planned service name surfaceledger. Project access and billing enabled status are verified. This does not authorize new paid charges. No service, identity, secret or data store for SurfaceLedger has been created.

Use explicit project/region flags. Preserve existing services audiencegraph-web, greenlight and production-control-0909-01a085, their data and identities. Use this application's own identity, secrets and data; never borrow Greenlight's database or existing build buckets. No new cloud project, Cloud SQL, Firebase Authentication or purchased domain is needed by default.

Substantive OpenCV 5 and AWS processing remain mandatory. GCP may support only an auxiliary interface; it cannot replace the required AWS runtime.

The portfolio runbook and exact resource allocation are in core-research/configuration/GCP_DEPLOYMENT_RUNBOOK.md and gcp-service-allocation.json. Recheck names and record commit/image/URL/rollback before deployment. Build/test locally while access or spending gates remain.
