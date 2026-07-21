# File-Upload Confirmation Storage Authorization

## Context

The document-ingestion creation path already carries the persisted job
metadata into the signed upload-URL storage boundary. The manual
`confirm-upload` path loads the same `Job` record, but its file-existence
check used `FileUploadService.verify_s3_file_exists()` without forwarding that
metadata. When remote object storage is enabled, the check therefore bypasses
the job-scoped authorization context at the async adapter boundary.

## Goals

1. Carry the existing `Job.job_metadata` through confirm-upload file
   existence verification.
2. Preserve the existing bucket selection, error mapping, and handoff
   behavior.
3. Prove the propagation with synthetic/local contract tests only.

## Non-goals

- No new schema, authorization type, provider profile, or storage adapter.
- No change to the shared fail-closed authorization rule.
- No live S3, OSS, MinIO, MinerU, provider, private-pilot, or upstream-sync
  operation.
- No claim of storage retention, deletion, destination qualification, or
  runtime promotion.

## Design

The existing metadata object is forwarded unchanged:

```text
Job.job_metadata
  -> DocumentIngestionConfirmationService.confirm_upload
  -> FileUploadService.verify_s3_file_exists
  -> JobFileStorage.verify_exists
  -> object-storage authorization boundary
```

`FileUploadService.verify_s3_file_exists()` accepts an optional keyword-only
`job_metadata` argument and passes it to the synchronous storage adapter
thread. The confirmation service supplies the metadata already loaded with
the authorized job. Local filesystem behavior and existing exception
translation remain unchanged.

## Test strategy

Synthetic contract coverage verifies that:

1. the async file-upload adapter forwards approved metadata to existence
   verification; and
2. the API confirm-upload flow forwards the persisted job metadata before
   starting the uploaded-file workflow.

The tests use recording fakes and the existing local contract fixtures. They
do not contact a storage backend or use credentials.

## Success boundary

This change is complete when the metadata reaches the existing storage
authorization boundary, the focused storage and API contracts pass, and the
change is recorded as a bounded external-call authorization improvement. It
does not close other metadata-less storage seams or promote any provider or
private-pilot runtime.
