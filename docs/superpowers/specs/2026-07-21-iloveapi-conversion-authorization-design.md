# iLoveAPI Conversion Authorization Boundary

## Context

Knowhere already keeps iLoveAPI conversion disabled by default, validates the
configured HTTPS endpoint, and checks a job-scoped `iloveapi` authorization in
the document-parse and page-memory entry paths. The lower-level in-memory
`_pptx_bytes_to_pdf_bytes()` function, however, can also be called directly.
That function performs quota acquisition and the complete iLoveAPI
start/upload/process/download sequence without receiving the job metadata.

## Decision

Carry the existing trusted `job_metadata` into `_pptx_bytes_to_pdf_bytes()` and
require `JobMetadataHelper.require_external_call_authorization(...,
provider="iloveapi")` after the existing operator and endpoint checks and
before quota acquisition. Propagate the same metadata from the legacy PPTX
API path and page-memory PPTX normalization.

The existing controls remain authoritative:

- `ILOVEAPI_EXTERNAL_CALLS_ENABLED` remains default-off and fail-closed.
- The configured iLoveAPI endpoint remains HTTPS and allowlist validated.
- All four requests retain explicit timeouts and `allow_redirects=False`.
- No new schema, migration, credential storage, or provider adapter is added.

## Boundaries

The candidate uses only synthetic metadata, fake quota state, and fake HTTP
responses in local contract tests. It does not contact iLoveAPI, upload a
private/customer PPTX, change provider credentials, run a deployment, or
promote the provider/private pilot.

## Acceptance

1. Missing or invalid `iloveapi` job authorization fails before quota setup.
2. Approved synthetic authorization reaches only fake start/upload/process/
   download calls.
3. The legacy PPTX API path and page-memory normalization pass trusted metadata
   into the low-level conversion boundary.
4. Existing endpoint, redirect, parser, and provider authorization contracts
   continue to pass.
