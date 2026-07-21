# MinerU Result Download Authorization

## Context

The cloud MinerU path already requires the default-off
`MINERU_EXTERNAL_CALLS_ENABLED` setting and the normal worker parse route
checks a job-scoped `mineru` authorization before entering the provider. The
polling helper then downloads the provider-returned result ZIP through the
existing pinned URL helper, but its direct polling entry point did not carry
or verify the same job authorization. This left the final provider-result
download outside the explicit job boundary.

## Goals

1. Require the existing traceable `mineru` job authorization at the start of
   `poll_mineru_task()` after the operator opt-in and endpoint checks.
2. Pass the trusted metadata from `parse_via_full()` into polling so normal
   cloud MinerU execution reaches that guard.
3. Keep the existing result ZIP URL validation, DNS pinning, redirect block,
   archive traversal, symlink, and artifact filtering controls unchanged.

## Non-goals

- No live MinerU session, API key, provider result, private source, or
  customer data.
- No new schema, database table, migration, provider credential, or retention
  claim.
- No change to local MinerU behavior, upstream synchronization, deployment,
  or private-pilot qualification.
- No automatic authorization synthesis at the provider boundary.

## Design

```text
parse_via_full(job_metadata)
  -> poll_mineru_task(job_metadata)
  -> existing operator/endpoint checks
  -> existing traceable mineru job authorization
  -> MinerU status request
  -> pinned provider-returned result ZIP download
```

The shared `JobMetadataHelper` remains the authorization source of truth. The
poller fails closed before quota acquisition or status/result network work
when metadata is missing or invalid. The existing outer worker gate remains
in place as defense in depth; this candidate closes the direct polling seam.

## Test strategy

Synthetic contracts use fake quota/session/download boundaries. They assert
that missing authorization stops before a status request, approved metadata
allows polling and result ZIP extraction, and `parse_via_full()` forwards the
same metadata. Existing MinerU URL, redirect, provider, and remote-input
contracts remain in the validation set. No live external call is made.

## Success boundary

This candidate is complete when the direct MinerU polling/result-download
entry point is job-authorized, focused contracts and changed-runtime checks
pass, and the change is recorded as isolated bounded evidence. It does not
prove provider retention/deletion, host-level no-egress, provider
qualification, private-pilot readiness, production equivalence, or RA
acceptance.
