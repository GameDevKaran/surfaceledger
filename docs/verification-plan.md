# SurfaceLedger: verification plan

No tests or evaluations have run. The following are prospective acceptance targets, not results.

## Fixtures and acceptance

20 development and 20 held-out capture sets from separately captured sessions. Coverage intersection-over-union ≥0.90 on the controlled grid; ≥18/20 held-out sets identify their largest deliberately missing region; zero invented source pixels. Report registration rejection rate, false “complete” decisions, processing time and AWS cost. Compare uniform overlap capture plus a simple stitched preview. Test blur, glare, repeated texture, low overlap and nonplanar input; failing a target triggers scope reduction or an honest limitation, not threshold changes after seeing holdout results.

## Demonstration to verify

show missing detail, upload tiles, inspect the uncovered area, recapture it, verify the changed coverage and open original-file evidence. Include one rejected alignment.

## Result record

For each run, record the source commit, fixture version, runtime/provider versions, actual pass and failure counts, latency, cost where relevant, and limitations. Keep development and held-out inputs separate. Report negative findings; freeze the protocol before inspecting held-out results.

A release requires a functioning end-to-end workflow and a clean-session replay. Documentation, repository creation and HTTP availability alone do not establish application correctness.
