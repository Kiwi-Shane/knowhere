# Provider-Aware Retrieval Cache Partitioning Design

## Goal

Close the remaining RA-UP-01 cache-boundary gap on the isolated Knowhere
remediation branch: retrieval and workflow-plan cache entries must be
partitioned by the effective text and vision provider endpoints as well as
their model identities. Keep the fork pinned and qualify only this isolated
candidate; do not synchronize upstream or activate a provider runtime.

## Context

The existing cache shape already includes effective BYOK text and vision model
identities, but it does not include the corresponding provider endpoint
identity. Two allowed OpenAI-compatible providers using the same model names
can therefore address the same user/namespace/query cache entry. The current
BYOK remediation removes raw credentials from durable job metadata, so the
cache change must not reintroduce API keys, encrypted credential references, or
raw endpoint text into Redis keys or logs.

## Selected approach

1. Resolve the effective text and vision providers from `LLMConfig` in the
   existing `RetrievalQuery.build_cache_extra()` path.
2. Canonicalize each non-empty endpoint with the existing
   `normalize_provider_endpoint()` policy helper. This reuses exact HTTPS,
   credential-free, query-free, and non-local endpoint normalization without
   making cache partitioning an allowlist or provider-execution gate.
3. Pass the canonical endpoint identities into the existing
   `_cache_shape_digest()` for retrieval-query and workflow-plan keys. The
   endpoint values are inputs to the final SHA-256 digest only; they are never
   concatenated into the Redis key, emitted in logs, or persisted as metadata.
4. Keep absent endpoints represented by the existing empty-value normalization.
   Requests that use server defaults retain the current cache behavior because
   no request-scoped endpoint is present.
5. Preserve every public cache function signature and TTL. No cache deletion,
   retention, Redis migration, provider call, or database operation is part of
   this slice.

## Alternatives considered

### Include raw endpoint text in the Redis key

Rejected. It would partition correctly but makes endpoint disclosure and key
format drift unnecessary risks. The existing digest boundary already provides
an opaque key.

### Add a credential-reference or API-key fingerprint to the cache key

Rejected. The retrieval cache contract has no stable request-scoped credential
reference, and a credential fingerprint would expand secret-lifecycle scope
without addressing the recorded endpoint-identity defect.

### Add a new cache namespace or schema version

Rejected. The existing cache-shape digest is the canonical partition boundary;
changing namespace/version would add migration and invalidation machinery for a
mechanical key-shape correction.

## Error and privacy boundaries

- Invalid or local endpoint values fail closed through the existing endpoint
  normalization helper before a cache key is generated; retrieval's existing
  cache-error handling treats that as a cache miss and provider admission stays
  independently fail-closed.
- API keys, encrypted credential references, request bodies, and raw provider
  output never enter the cache-shape inputs.
- Endpoint identity is tested for partitioning and canonicalization, while the
  final key is tested to contain neither representative endpoint nor secret
  text.
- This implementation does not prove egress, provider retention/deletion,
  provider authorization, production equivalence, RA acceptance, or upstream
  compatibility.

## Acceptance cases

- Same query/model with different text endpoints produces different retrieval
  keys.
- Same query/model with different vision endpoints produces different keys.
- Canonically equivalent endpoint forms (for example a trailing slash) produce
  the same key.
- Different text and vision endpoints remain independently represented and do
  not collapse into one channel.
- `RetrievalQuery.build_cache_extra()` forwards endpoint identities but never
  forwards `api_key` or credential-reference material.
- Existing model, absent-value, deterministic, TTL, and workflow-plan behavior
  remains unchanged.

## Gate status

This is a bounded repeated privacy/traceability risk under RA-UP-01. It is
candidate-scope implementation evidence only. The branch remains isolated from
the pinned fork and upstream; retention/deletion and host-level egress remain
separate gates.
