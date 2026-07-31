# Phase 2 Page-Memory Assist Design

Status: engineering design for `knowhere_page_memory_extractive_v1`.

## Runtime boundary

This profile is a coarse page-navigation layer. It indexes declared native
page text and optional caller-supplied precomputed vectors. It does not call an
LLM, VLM, embedding service, network service, or provider API, and it does not
make a source-sufficiency or RA acceptance decision.

The profile is case-isolated and source/version-bound:

```yaml
summary_enabled: false
agentic_llm_navigation_enabled: false
image_description_vlm_enabled: false
external_model_calls: false
lexical_retrieval: true
visual_retrieval: optional
adjacent_page_expansion: true
case_isolation: true
```

## Frozen implementation paths

The current repository already contains a VLM-oriented worker path under
`apps/worker/app/services/page_memory/`. That path remains unchanged. The
Phase 2 assist contract is intentionally isolated in the following shared
package:

```text
packages/shared-python/shared/services/page_memory/
  __init__.py
  models.py
  contracts.py
  index.py
  query.py
  ranking.py
  storage.py
  deletion.py
```

Focused tests and machine-readable contracts are kept at:

```text
packages/shared-python/shared/tests/page_memory/
schemas/page-memory-record-v1.schema.json
schemas/page-retrieval-result-v1.schema.json
```

Worker jobs and API routes are not activated by this engineering gate. A
future runtime integration must preserve the same case/source/version gates
and must not silently reuse the legacy VLM path.

## Retrieval policy

The frozen ranking weights are lexical `0.50`, visual `0.35`, coarse section
proximity `0.10`, and adjacency `0.05`. Visual retrieval accepts only vectors
supplied by the caller and binds them to
`caller_supplied_precomputed_v1` plus a deterministic artifact hash.

Every imported page result carries an exact source-version page locator and
remains `unverified` / `evidence_lead_only`. Empty retrieval is
`no_result_found`; it is never `verified_absent`.

Ingestion reads only manifest-declared files, verifies their SHA-256 values,
rejects path escape and reparse/symlink paths, and produces deterministic
snapshot identities. Deletion creates a new snapshot so a deleted page cannot
be returned by a prior active query. Adjacent expansion is bounded to one
page per direction.

The RA repository owns its provider-neutral import boundary; this repository
owns the page-memory result contract and retrieval behavior.
