# Plan: File-Upload Confirmation Storage Authorization

## Goal

Close the manual `confirm-upload` storage-authorization propagation gap by
forwarding persisted job metadata through the async file-upload adapter and
the API confirmation service.

## Task 1: Add failing contract coverage

- Add a shared contract that calls `verify_s3_file_exists()` with synthetic
  approved metadata and asserts the recording storage seam receives it.
- Update the existing API confirm-upload contracts to require and inspect the
  metadata argument.
- Run the focused tests and confirm the pre-change signature fails as
  expected.

## Task 2: Implement the minimal propagation

- Add a keyword-only `job_metadata` argument to
  `FileUploadService.verify_s3_file_exists()`.
- Forward it to `JobFileStorage.verify_exists()`.
- Pass `job.job_metadata` from `DocumentIngestionConfirmationService`.
- Preserve existing bucket defaults and exception behavior.

## Task 3: Verify and hand off bounded evidence

- Run the complete shared storage-authorization contract and API
  job-creation contract.
- Run Ruff check, changed-runtime Pyright, compile, and diff checks.
- Keep real storage/provider calls, private data, and upstream synchronization
  out of scope.
- Record the candidate on the isolated branch and hand the revision to the RA
  evidence workflow.
