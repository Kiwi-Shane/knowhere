# Demo Materialization Storage Authorization

## Context

The API's canonical demo materialization path creates a completed
`demo_materialization` Job and uploads a result bundle before persisting that
Job. The upload previously omitted the same job metadata that was later saved
with the Job, so the existing remote object-storage authorization boundary did
not receive an authorization context for this production call site.

## Goals

1. Create the existing job metadata before demo result upload.
2. Mark the canonical demo payload as `synthetic` and authorize only the
   existing `object_storage` provider boundary.
3. Pass that exact metadata to result upload and persist it on the Job.
4. Preserve demo materialization, publication, retry/idempotency, and local
   filesystem behavior.

## Non-goals

- No new schema, authorization type, provider profile, or storage adapter.
- No live storage or provider operation, deployment, or runtime promotion.
- No authorization for customer/private sources or external provider parsing.
- No change to the shared fail-closed object-storage policy.

## Design

The existing metadata object is created once and forwarded unchanged:

```text
canonical demo source + job id
  -> Job metadata with synthetic object_storage authorization
  -> ResultStorage.upload(job_metadata=...)
  -> Job(job_metadata=...)
```

The authorization record uses the canonical demo source as `source_scope`, a
job-specific deterministic authorization ID, and the internal demo materializer
as the approver identity. This permits the existing default-deny remote storage
gate to distinguish an explicitly configured synthetic demo operation from an
unscoped result upload.

## Test strategy

The existing API demo contract uses a recording result-storage fake to assert
that the uploaded metadata is identical to the persisted Job metadata and that
the object-storage authorization is approved, correctly identified, and
classified as synthetic. No storage backend or credential is used.

## Success boundary

This change is complete when the demo upload and persisted Job share the same
approved synthetic authorization metadata and the full demo contract passes.
It does not establish remote destination, retention/deletion, host egress,
provider/private-pilot readiness, or production qualification.
