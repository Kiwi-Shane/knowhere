# Source URL Download Authorization

## Context

Knowhere's URL-ingestion path already validates HTTP(S) URLs, resolves DNS,
pins the resolved address, and disables redirects. It nevertheless reached
the URL validation/optional `HEAD` inspection and the final file download
without an explicit operator opt-in or a job-scoped authorization record.
That left a user-provided source URL as an outbound HTTP boundary outside the
existing provider and object-storage authorization contracts.

## Goals

1. Require explicit `SOURCE_URL_EXTERNAL_CALLS_ENABLED=true` before source URL
   validation, optional content-type inspection, or content download in
   staging/production.
2. Require the existing traceable job authorization contract with provider
   `source_url` before worker URL-ingestion calls that carry job metadata.
3. Propagate the same job metadata through URL extension resolution and file
   download.
4. Preserve the existing SSRF validation, DNS pinning, no-redirect behavior,
   local filesystem storage, and development-only local test path.

## Non-goals

- No new database table, migration, provider credential, or customer-data
  authorization schema.
- No allowlist expansion, live URL request, provider/private-pilot execution,
  deployment, or upstream synchronization.
- No automatic authorization of production/customer URLs from a public job
  request.
- No claim that generic remote parser asset loading has a production-ready
  job-metadata propagation path; calls without trusted metadata remain blocked
  when this opt-in is enabled.

## Design

The existing external-call authorization shape is reused with one new provider
key and one operator setting:

```text
URL source request
  -> operator opt-in before URL validation / optional HEAD
  -> job metadata with source_url authorization
  -> pinned, no-redirect file download
  -> existing object-storage upload and verification authorization
```

`source_url` authorizations use the same approved test classifications
(`synthetic`, `megaforce_test`, or `fda_test`) and required traceability fields
as the existing provider contracts. Development/local contract runs may use
the existing private-host exception when the operator setting is disabled;
production and staging do not.

## Test strategy

Contract tests use monkeypatched DNS, HTTP clients, and pinned-transfer fakes.
They assert that disabled or missing authorization fails before URL validation
or transfer, approved metadata reaches the transfer boundary, worker URL
helpers preserve the metadata, and existing API/worker synthetic URL contracts
still pass. No live remote endpoint or provider credential is used.

## Success boundary

This change is complete when the source URL preflight and download boundaries
are operator-gated, the worker path carries job-scoped authorization, and the
focused API/worker/shared contracts pass. It does not establish a production
URL allowlist, customer-data approval, retention/deletion behavior, private
pilot readiness, or regulatory qualification.
