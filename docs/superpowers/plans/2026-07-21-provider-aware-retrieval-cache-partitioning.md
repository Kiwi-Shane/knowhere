# Provider-Aware Retrieval Cache Partitioning Implementation Plan

> For agentic workers: use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Partition retrieval and workflow-plan cache keys by effective provider endpoint identity without persisting raw endpoint or credential material.

**Architecture:** Reuse the existing LLMConfig effective-provider resolution and normalize_provider_endpoint helper. Carry canonical text/vision endpoint identities through RetrievalQuery.build_cache_extra into the existing SHA-256 cache-shape digest. Do not add a schema, Redis migration, namespace, TTL, provider call, or external runtime.

**Tech Stack:** Python 3.11+, Pydantic, pytest, Ruff, Pyright, and the existing shared-python package.

## Global Constraints

- Work only in isolated branch fix/kiwi-shane/cache-partitioning-20260721, based on candidate 19f089f7255bcdb505d7883ece5bbdec90ba67fa.
- Do not fetch, merge, rebase, synchronize, or force-push upstream.
- Preserve existing cache API signatures and TTL constants.
- Do not put API keys, encrypted credential references, raw request bodies, or provider output in cache keys, logs, or tracked files.
- Reuse normalize_provider_endpoint; do not create a second endpoint-policy implementation.
- Evidence is candidate-scope only and does not claim retention/deletion, egress, production promotion, RA acceptance, or qualification.

---

### Task 1: Add failing cache partition tests

Files:
- Modify: packages/shared-python/shared/tests/test_retrieval_cache_service.py
- Create: packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py

Interfaces:
- Consume existing _query_cache_key and RetrievalQuery.from_parameters.
- Produce failing tests for endpoint-aware key identity and query-level propagation.

- [ ] Step 1: Extend the cache helper and add RED assertions.

Add llm_text_endpoint and llm_vision_endpoint arguments to the existing _key helper and pass them to _query_cache_key. Add tests whose exact assertions are:

~~~python
def test_cache_key_changes_when_text_endpoint_changes() -> None:
    assert _key(llm_text_endpoint="https://one.example.test/v1") != _key(
        llm_text_endpoint="https://two.example.test/v1"
    )


def test_cache_key_changes_when_vision_endpoint_changes() -> None:
    assert _key(llm_vision_endpoint="https://one.example.test/v1") != _key(
        llm_vision_endpoint="https://two.example.test/v1"
    )


def test_cache_key_normalizes_endpoint_trailing_slash() -> None:
    assert _key(llm_text_endpoint="https://provider.example.test/v1/") == _key(
        llm_text_endpoint="https://provider.example.test/v1"
    )
~~~

- [ ] Step 2: Add the RED query-propagation test.

Create test_retrieval_query_cache_identity.py. Use a real LLMConfig with text provider endpoint https://provider.example.test/v1/ and vision provider endpoint https://vision.example.test/v1. Construct RetrievalQuery.from_parameters with db=cast(AsyncSession, object()), user_id user-1, namespace case-1, query find the verified result, top_k 5, and empty exclusions. Assert build_cache_extra returns canonical llm_text_endpoint and llm_vision_endpoint values, does not contain api_key, and does not contain either representative secret in repr(extra).

- [ ] Step 3: Verify RED.

Run:
~~~powershell
python -m uv run pytest packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py -q
~~~

Expected: the endpoint keyword is rejected by the current cache helper and the query test fails because endpoint fields are absent. Do not change production code before observing this failure.

### Task 2: Implement endpoint-aware cache-shape propagation

Files:
- Modify: packages/shared-python/shared/services/retrieval/execution/query_request.py
- Modify: packages/shared-python/shared/services/retrieval/cache_service.py

Interfaces:
- Query produces llm_text_endpoint and llm_vision_endpoint.
- Existing digest and extra-parameter paths consume them.

- [ ] Step 1: Resolve canonical endpoints in build_cache_extra.

Import normalize_provider_endpoint. For each non-None effective text or vision provider, keep its model and set the endpoint to normalize_provider_endpoint(provider.base_url). Return both endpoint fields next to the existing model fields. Never return API keys or credential references.

- [ ] Step 2: Include endpoints in _cache_shape_digest.

Add optional llm_text_endpoint and llm_vision_endpoint parameters. Normalize missing values using the existing empty-string convention and append both canonical endpoint values after the normalized model values in the hashed extra list. Leave _query_cache_key, _workflow_plan_cache_key, Redis calls, and TTL constants unchanged.

- [ ] Step 3: Verify GREEN.

Run the Task 1 pytest command. Expected: all existing and new tests pass, including endpoint canonicalization and secret omission.

### Task 3: Add compatibility and fail-closed regression coverage

Files:
- Modify: packages/shared-python/shared/tests/test_retrieval_cache_service.py
- Modify: packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py

- [ ] Step 1: Add channel and absent-value assertions.

Add these exact behaviors:

~~~python
def test_cache_key_keeps_text_and_vision_endpoint_channels_distinct() -> None:
    assert _key(
        llm_text_endpoint="https://text.example.test/v1",
        llm_vision_endpoint="https://vision.example.test/v1",
    ) != _key(
        llm_text_endpoint="https://vision.example.test/v1",
        llm_vision_endpoint="https://text.example.test/v1",
    )


def test_absent_endpoint_values_are_deterministic() -> None:
    assert _key(llm_text_endpoint=None) == _key(llm_text_endpoint="")
    assert _key(llm_vision_endpoint=None) == _key(llm_vision_endpoint="")
~~~

Add a query test with base_url http://localhost/v1 and assert LLMEndpointPolicyError is raised by normalize_provider_endpoint before cache extras are produced.

- [ ] Step 2: Run the expanded shared selection.

~~~powershell
python -m uv run pytest packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py packages/shared-python/shared/tests/test_llm_config.py packages/shared-python/shared/tests/test_byok_credential_reference.py -q
~~~

Expected: all selected tests pass with no provider, Redis, database, or network call.

### Task 4: Validate and record candidate evidence

Files:
- Modify: docs/maintenance/ra_up_01_knowhere_upstream_impact_decision_20260719.md
- Modify: docs/qualification/knowledge-retrieval-result-v1.md

- [ ] Step 1: Run quality checks.

~~~powershell
python -m uv run ruff check packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/services/retrieval/execution/query_request.py packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py
python -m uv run ruff format --check packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/services/retrieval/execution/query_request.py packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py
python -m uv run pyright packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/services/retrieval/execution/query_request.py packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py
python -m compileall -q packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/services/retrieval/execution/query_request.py
git diff --check
~~~

Expected: all commands exit zero. Record unrelated baseline failures without claiming them fixed.

- [ ] Step 2: Append a bounded evidence note.

Record candidate SHA, test counts, endpoint partitioning behavior, no-provider/no-network boundary, and unchanged stay_pinned/sync_authorized=false disposition. Do not alter qualification status or claim retention/deletion/egress proof.

### Task 5: Review, commit, push, and verify clean state

Files:
- Stage only the two production files, the two test files, and the two evidence documents.

- [ ] Step 1: Review staged scope.

~~~powershell
git status --short
git diff --cached --check
git diff --cached --stat
python -m uv run python tools/validate_generated_artifacts.py
~~~

Expected: no private source, provider output, credential, local runtime, or generated artifact is staged.

- [ ] Step 2: Commit and push the isolated candidate.

~~~powershell
git add packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/services/retrieval/execution/query_request.py packages/shared-python/shared/tests/test_retrieval_cache_service.py packages/shared-python/shared/tests/test_retrieval_query_cache_identity.py docs/maintenance/ra_up_01_knowhere_upstream_impact_decision_20260719.md docs/qualification/knowledge-retrieval-result-v1.md
git commit -m "fix: partition retrieval cache by provider endpoint"
git push --set-upstream origin fix/kiwi-shane/cache-partitioning-20260721
~~~

- [ ] Step 3: Verify clean candidate state.

~~~powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/fix/kiwi-shane/cache-partitioning-20260721
~~~

Expected: empty worktree, equal local/remote commit IDs, and RA-UP-01 remains pinned with no synchronization.

