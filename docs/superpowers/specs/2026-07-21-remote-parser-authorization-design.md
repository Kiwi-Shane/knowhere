# Remote Parser Input Authorization

## Context

The worker's shared `load_file_bytes()` helper already routes HTTP(S) input
through the guarded `JobFileStorage.download_file_from_url()` boundary. The
source-URL authorization candidate added operator and job authorization at
that boundary, but several parser entry points did not forward the trusted
job metadata held by `ParseSession`/`PageMemoryInput`. A production remote
parser input could therefore be rejected even when the job was authorized,
while the call sites were not explicit about the authorization context.

## Goals

1. Carry the existing job metadata from parser orchestration into every worker
   parser path that can load an HTTP(S) source through `load_file_bytes()`.
2. Preserve the existing source-URL operator opt-in, job authorization,
   validation, DNS pinning, and no-redirect controls.
3. Keep all new parameters optional so local filesystem parsing and existing
   direct parser callers remain compatible.
4. Cover text, image, DOCX, XLSX, PPTX, HTML, Markdown, and page-memory PPTX
   input paths with synthetic contract tests.

## Non-goals

- No new authorization schema, database table, migration, or provider
  credential.
- No direct network call, customer/private source, deployment, provider pilot,
  or upstream synchronization.
- No claim that all remote content embedded inside third-party parser libraries
  is authorized; this change covers Knowhere's explicit `load_file_bytes()`
  entry points only.

## Design

```text
ParseSession / PageMemoryInput
  -> format adapter / normalizer
  -> parser entry point
  -> load_file_bytes(job_metadata=...)
  -> guarded source-URL authorization + pinned transfer
```

The existing metadata object is passed by reference through the synchronous
worker parser call chain. No authorization is synthesized at a parser layer;
when production source-URL calls are enabled, missing or invalid metadata
continues to fail closed in the shared storage boundary.

## Test strategy

Contract tests use synthetic authorization metadata and recording storage
doubles. They verify metadata reaches the guarded downloader and is forwarded
by the parser adapters. Existing remote-input, source-storage, URL-upload,
HTML, document-profile, and MinerU URL-storage contracts remain in the
focused validation set. No live URL, provider session, secret, or private
source is used.

## Success boundary

This candidate is complete when all explicit worker `load_file_bytes()` paths
receive the available job metadata, focused contracts and changed-runtime
static checks pass, and the change is recorded as a non-merged safety
candidate. It does not establish provider/private-pilot readiness, egress
proof, retention/deletion behavior, or regulatory qualification.
