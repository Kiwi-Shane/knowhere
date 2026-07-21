# MinerU URL-Mode Job-Scoped Storage Authorization

## Context

The result-artifact and retrieval storage authorization work already makes the
shared `JobFileStorage` boundary require an approved `object_storage`
authorization when remote object storage calls are enabled. The MinerU PDF
URL-mode path can reach that boundary through three operations:

- verify whether the source object already exists;
- upload a local source when the object is absent; and
- generate a presigned download URL for the MinerU URL task.

`ParseSession.job_metadata` already enters the PDF adapter and is already used
by shard cleanup. The remaining URL-mode calls currently omit it, so the
authorization contract is not enforced at this parser seam.

## Goals

1. Carry the existing per-job metadata through the standard, fast shard, and
   cached-rendered-PDF MinerU URL-mode paths.
2. Pass that metadata to every `JobFileStorage` operation used by URL mode.
3. Preserve the existing local MinerU provider behavior and the existing
   direct-upload fallback behavior.
4. Prove the boundary with synthetic contract tests that do not contact S3,
   MinerU, or a private provider.

## Non-goals

- No new schema, authorization type, adapter, or provider profile.
- No change to the shared storage authorization implementation.
- No change to direct MinerU upload authorization or provider-session
  qualification.
- No live object-storage, MinerU, AIWB, private-pilot, or upstream-sync work.
- No claim that source-owner/native MinerU qualification or host-level
  no-egress verification is complete.

## Design

The existing metadata object is forwarded without copying or reinterpreting it:

```text
ParseSession.job_metadata
  -> PdfParseAdapter
  -> parse_pdfs
  -> provider.parse_pdf
  -> parse_via_full / URL-mode source helpers
  -> JobFileStorage(..., job_metadata=job_metadata)
```

The cached rendered-PDF inspection uses the same helper and receives the same
metadata before any object-storage verification. The shard fast path and each
parallel shard receive the metadata so that source verification, temporary
shard upload, and URL presigning use the same job authorization. Local parsing
continues to receive only its existing arguments; the metadata is not used to
change local execution.

The existing storage service remains the fail-closed enforcement point. If
metadata is missing or invalid, `JobFileStorage` raises before its storage
adapter is called. The MinerU URL-mode helper retains its current fallback
handling for storage-preparation failures; this slice verifies that the
underlying adapter is never reached without authorization and that approved
metadata is forwarded intact.

## Test strategy

Contract tests will use a recording fake `JobFileStorage` seam and synthetic
authorization metadata. They will cover:

1. missing and invalid metadata are rejected by the real storage boundary
   before a fake adapter operation can run;
2. approved metadata reaches verify, upload, and presign calls unchanged;
3. the provider forwards metadata to the full MinerU seam while local provider
   delegation remains unchanged;
4. `parse_pdfs` forwards metadata through the standard and shard fast paths;
5. cached rendered-PDF source inspection forwards metadata.

Assertions will inspect only call arguments and local control flow. The tests
will not make network calls, use real credentials, or assert provider output.

## Success boundary

This change is complete when the URL-mode storage operations are metadata-aware,
the focused contract tests and relevant parser/provider regressions pass, and
the change is recorded as a bounded BL-092 authorization-seam improvement. It
does not promote the MinerU producer compatibility profile, start a private or
provider pilot, or close the broader metadata-less external-call audit.

## Rollback

The change is isolated on
`fix/kiwi-shane/mineru-url-storage-job-authorization-20260721`. A rollback can
revert its commit without changing the existing D2 worktree, the result-artifact
authorization branch, or the RA branch.
