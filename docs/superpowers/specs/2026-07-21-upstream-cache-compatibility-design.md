# Upstream BYOK Cache Compatibility Design

## Status

Approved by standing operator authorization on 2026-07-21. This is an
isolated qualification change only. It does not authorize upstream
synchronization, merge, rebase, promotion, or provider execution.

## Goal

Make the upstream BYOK retrieval cache path accept the model-identity fields
already emitted by `RetrievalQuery.build_cache_extra()` and include those
fields in the existing cache identity without persisting or exposing
credentials.

## Context

The recorded RA-UP-01 comparison found that the upstream retrieval request
builder emits `llm_text_model` and `llm_vision_model`, while the unchanged
`_cache_shape_digest()` signature does not accept them. The existing
`_query_cache_key()` forwards extra cache fields into that function, so a
BYOK retrieval request can fail with an unexpected-keyword `TypeError` before
retrieval runs.

The model identities affect LLM-backed retrieval behavior and therefore must
participate in the cache identity. API keys, raw provider configuration, and
provider secrets must not enter the cache key. Provider endpoint identity is a
separate RA-UP-01 blocker and remains out of scope for this slice.

## Considered approaches

1. **Explicit model parameters in the existing digest (selected).** Add two
   optional keyword-only parameters and append their normalized values to the
   existing deterministic payload. This is the smallest compatible fix,
   preserves the current call graph, and makes the cache contract visible in
   the function signature.
2. **Accept arbitrary extra cache fields with `**kwargs`.** This avoids future
   signature errors but weakens the cache contract, makes accidental fields
   easier to add, and can silently change cache partitioning. It is rejected
   for this qualification slice.
3. **Redesign cache identity around a typed provider descriptor.** This would
   address endpoint identity and provider partitioning more completely, but
   it is a separate security/data-lifecycle design that depends on the
   unresolved endpoint authorization and secret-retention decisions. It is
   deferred rather than bundled into this compatibility fix.

## Scope

### Cache contract

Modify `packages/shared-python/shared/services/retrieval/cache_service.py` so
`_cache_shape_digest()` accepts:

```python
llm_text_model: str | None = None
llm_vision_model: str | None = None
```

The values are trimmed for identity and represented as empty strings when
absent. Both values are appended to the existing ordered payload before the
SHA-256 digest is computed. The existing normalization of query, filters,
channels, and weights remains unchanged.

The public async cache functions remain API-compatible. `_query_cache_key()`
continues to forward only explicitly supported extra fields to the digest.
No API key, URL, authorization header, raw `LLMConfig`, or request body is
accepted by this change.

### Regression coverage

Add focused shared-package tests that:

- call `_query_cache_key()` with the two model fields and prove the previous
  unexpected-keyword failure is gone;
- prove changing the text model changes the key;
- prove changing the vision model changes the key;
- prove the key is deterministic for the same model identities; and
- prove representative secret and endpoint strings are absent from the key.

The test uses the pure key-building boundary and does not start Redis, call a
provider, or make network requests.

### Qualification evidence

Record the red/green test commands, focused package tests, Ruff result,
Pyright result, and the explicit non-goals in the implementation plan and
branch commit history. The branch is a candidate for review only; it is not a
promotion or upstream-sync result.

## Error handling and compatibility

The fix is fail-closed with respect to the previous `TypeError`: the explicit
model fields are accepted and encoded. Missing model fields retain the
default `None` behavior. Cache entries created before this change naturally
miss because the digest payload gains the model-identity positions; no
migration or deletion job is required for this isolated qualification.

If a future caller needs endpoint-aware partitioning, it must use a separate
approved design that specifies endpoint allowlisting, egress policy,
authorization scope, and secret lifecycle before changing this key contract.

## Non-goals

- No upstream fetch, merge, rebase, or synchronization.
- No change to the pinned fork branch or existing completed worktrees.
- No provider session, live LLM call, Redis service, database, or external
  network call.
- No raw API-key persistence/deletion remediation.
- No `base_url` validation or endpoint allowlist.
- No provider/job/tenant authorization implementation.
- No claim that RA-UP-01 is promoted, resolved, or release-ready.

## Verification plan

1. Write the focused regression test and run it before the implementation;
   observe the expected unexpected-keyword failure.
2. Add only the explicit model parameters and payload fields.
3. Run the focused regression test and the relevant shared retrieval tests.
4. Run Ruff on changed Python files and Pyright on the shared package.
5. Review the diff for secret/endpoint leakage, run `git diff --check`, and
   verify that no external call or upstream synchronization occurred.
