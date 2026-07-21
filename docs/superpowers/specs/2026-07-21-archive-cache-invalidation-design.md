# Archive Cache Invalidation Boundary

## Problem

Document retrieval responses are versioned by a user/namespace Redis cache
version. Archiving an active document bumps that version after the database
commit. An idempotent archive request for a document that is already archived
returned before performing the same invalidation. If the first invalidation
was unavailable or failed outside the application boundary, a later authorized
archive request could not provide another cleanup attempt.

## Decision

Every successful archive request, including an idempotent request for an
already-archived document, attempts retrieval-cache namespace invalidation.
The database and graph mutations remain limited to the active-to-archived
transition. Cache invalidation remains a best-effort post-commit effect and
does not roll back the document state.

## Safety boundary

- The namespace is taken from the user-owned document record.
- No raw retrieval response, provider credential, endpoint, or provider output
  is included in the invalidation operation.
- The change covers the existing retrieval cache version mechanism only.
- It does not activate `knowledge-retrieval-result-v1`, prove canonical
  result non-retrievability, qualify native/semantic gold, or establish host
  egress denial.

## Acceptance evidence

The API contract test records that an authorized archive request for an
already-archived document invokes invalidation once with the owning user and
document namespace. Existing active-document archive tests continue to cover
the state transition and graph removal.
