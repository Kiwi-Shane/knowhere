# Plan: Demo Materialization Storage Authorization

## Goal

Close the API canonical-demo result upload gap by propagating an existing,
synthetic object-storage authorization context through the result bundle upload
and the completed demo Job record.

## Task 1: Add failing contract coverage

- Extend the demo result-storage fake to record `job_metadata`.
- Query the persisted demo Job metadata and assert it matches the upload
  metadata and contains the approved synthetic object-storage record.
- Run the focused demo materialization test and confirm it fails because the
  upload receives no metadata.

## Task 2: Implement the minimal propagation

- Build the demo Job metadata before result upload.
- Add the existing `object_storage` authorization record with canonical-demo
  scope and synthetic classification.
- Pass the same metadata to `ResultStorage.upload()` and `Job` construction.

## Task 3: Verify and hand off bounded evidence

- Run the complete API demo contract, Ruff, changed-file Pyright, compile, and
  diff checks.
- Keep live storage/provider calls, private data, deployment, and upstream
  synchronization out of scope.
- Record the candidate on the isolated branch and hand it to the RA evidence
  workflow.
