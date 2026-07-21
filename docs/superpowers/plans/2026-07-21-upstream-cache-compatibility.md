# Upstream BYOK Cache Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Make the upstream BYOK retrieval cache key accept and partition on the model identities emitted by RetrievalQuery.build_cache_extra().

**Architecture:** Keep the existing _query_cache_key() call graph and SHA-256 digest. Add two explicit optional model parameters to _cache_shape_digest(), normalize absent or whitespace-only values to empty strings, and append the text/vision model identities to the ordered digest payload. Cover the boundary with pure shared-package tests; no Redis, database, provider, or network is involved.

**Tech Stack:** Python 3.11, pytest, pytest-asyncio, Ruff, Pyright, uv workspace.

## Global Constraints

- Work only in the isolated worktree C:\Users\psc01\workspace\knowhere\.worktrees\upstream-cache-compatibility-20260721 on branch fix/kiwi-shane/upstream-cache-compatibility-20260721.
- Do not fetch, merge, rebase, force-push, or synchronize upstream; this branch is an isolated qualification candidate.
- Do not modify the existing codex/knowhere-upstream-sync-candidate worktree or any completed D2/provider/storage worktree.
- Do not put API keys, authorization headers, raw provider configuration, or endpoint URLs into cache keys.
- Keep endpoint identity, base_url validation, raw BYOK metadata retention/deletion, and provider authorization as separate RA-UP-01 blockers.
- Use test-first development: the regression test must fail with the recorded unexpected-keyword error before production code changes.
- Use the project .venv created by uv sync --all-packages; no live service or external provider is required.

---

### Task 1: Add the focused cache-key regression tests

**Files:**
- Create: packages/shared-python/shared/tests/test_retrieval_cache_service.py
- Reference: packages/shared-python/shared/services/retrieval/cache_service.py:34-69

**Interfaces:**
- Consumes: _query_cache_key(**kwargs) from shared.services.retrieval.cache_service.
- Produces: pure tests proving the accepted model-identity fields, deterministic keying, model partitioning, and whitespace normalization contract.

- [ ] **Step 1: Write the failing tests**

Create packages/shared-python/shared/tests/test_retrieval_cache_service.py with:

~~~
from __future__ import annotations

from shared.services.retrieval.cache_service import _query_cache_key


def _key(
    *,
    llm_text_model: str | None = None,
    llm_vision_model: str | None = None,
) -> str:
    return _query_cache_key(
        user_id="user-1",
        namespace="case-1",
        version=0,
        query="find the verified result",
        top_k=5,
        exclude_document_ids=[],
        exclude_sections=[],
        chunk_types=["text"],
        signal_paths=["content"],
        filter_mode="delete",
        channels=["content"],
        channel_weights={"content": 2.0},
        rerank=False,
        threshold=0.0,
        internal_recall_k=20,
        use_agentic=False,
        decomposition_enabled=True,
        llm_text_model=llm_text_model,
        llm_vision_model=llm_vision_model,
    )


def test_cache_key_accepts_byok_model_identity_fields() -> None:
    key = _key(llm_text_model="text-model", llm_vision_model="vision-model")

    assert key.startswith("retrieval:query:user-1:case-1:v0:")


def test_cache_key_changes_when_text_model_changes() -> None:
    assert _key(llm_text_model="text-model-a") != _key(
        llm_text_model="text-model-b"
    )


def test_cache_key_changes_when_vision_model_changes() -> None:
    assert _key(llm_vision_model="vision-model-a") != _key(
        llm_vision_model="vision-model-b"
    )


def test_cache_key_is_deterministic_and_normalizes_absent_model_values() -> None:
    assert _key(llm_text_model="text-model", llm_vision_model="vision-model") == _key(
        llm_text_model="text-model", llm_vision_model="vision-model"
    )
    assert _key(llm_text_model=None) == _key(llm_text_model="")
    assert _key(llm_vision_model="  vision-model  ") == _key(
        llm_vision_model="vision-model"
    )


def test_cache_key_does_not_expose_representative_secret_or_endpoint_text() -> None:
    key = _key(
        llm_text_model="text-model",
        llm_vision_model="vision-model",
    )

    assert "sk-test-secret" not in key
    assert "https://provider.invalid/v1" not in key
~~~

- [ ] **Step 2: Run the tests to verify the expected red state**

Run from the qualification worktree:

~~~
$env:PYTHONPATH = "packages/shared-python;apps/api;apps/worker"
& ".\.venv\Scripts\pytest.exe" packages/shared-python/shared/tests/test_retrieval_cache_service.py -q
~~~

Expected result before production changes: collection succeeds and the first model-identity call fails with TypeError: _cache_shape_digest() got an unexpected keyword argument 'llm_text_model'. Do not change the test to make this failure pass.

### Task 2: Implement the explicit model-identity digest boundary

**Files:**
- Modify: packages/shared-python/shared/services/retrieval/cache_service.py:34-69
- Test: packages/shared-python/shared/tests/test_retrieval_cache_service.py

**Interfaces:**
- Consumes: the failing _query_cache_key() calls from Task 1.
- Produces: _cache_shape_digest(..., llm_text_model: str | None = None, llm_vision_model: str | None = None) -> str with deterministic model-aware identity.

- [ ] **Step 1: Add the minimal implementation**

Extend the _cache_shape_digest() keyword-only signature after decomposition_enabled:

~~~
    llm_text_model: str | None = None,
    llm_vision_model: str | None = None,
~~~

Immediately before constructing extra, normalize the values:

~~~
    normalized_text_model = (llm_text_model or "").strip()
    normalized_vision_model = (llm_vision_model or "").strip()
~~~

Append the two normalized values, in text-then-vision order, to the existing extra = "|".join([...]) list after str(decomposition_enabled):

~~~
            normalized_text_model,
            normalized_vision_model,
~~~

Do not change _query_cache_key(), the Redis functions, or provider configuration code. Do not add a generic **kwargs escape hatch.

- [ ] **Step 2: Run the focused tests to verify green**

Run:

~~~
$env:PYTHONPATH = "packages/shared-python;apps/api;apps/worker"
& ".\.venv\Scripts\pytest.exe" packages/shared-python/shared/tests/test_retrieval_cache_service.py -q
~~~

Expected result: 5 passed and no failures. The test must exercise the real _query_cache_key() and _cache_shape_digest() functions.

### Task 3: Run adjacent regression and static checks

**Files:**
- Modify: none beyond Task 2
- Test: packages/shared-python/shared/tests/test_retrieval_cache_service.py
- Check: packages/shared-python/shared/services/retrieval/cache_service.py

**Interfaces:**
- Consumes: the green model-aware cache-key implementation.
- Produces: local qualification evidence with no external calls.

- [ ] **Step 1: Run shared retrieval tests**

Run:

~~~
$env:PYTHONPATH = "packages/shared-python;apps/api;apps/worker"
& ".\.venv\Scripts\pytest.exe" packages/shared-python/shared/tests apps/api/tests/contract/test_retrieval_contract.py apps/worker/tests/contract/test_page_memory_retrieval_contract.py -q
~~~

Expected result: the new five tests pass. The two known upstream-candidate failures in test_page_memory_vlm_limiter.py may remain because their fixture still supplies a legacy one-argument get_openai_client lambda; report those as pre-existing and do not alter that unrelated fixture in this slice.

- [ ] **Step 2: Run Ruff on the changed Python files**

Run:

~~~
& ".\.venv\Scripts\ruff.exe" check packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/tests/test_retrieval_cache_service.py
~~~

Expected result: exit code 0 with no findings.

- [ ] **Step 3: Run Pyright for the shared package**

Run:

~~~
& ".\.venv\Scripts\pyright.exe" packages/shared-python/shared
~~~

Expected result: exit code 0, with no new errors attributable to this slice.

- [ ] **Step 4: Inspect the final diff and boundary**

Run:

~~~
git diff --check
git diff -- packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/tests/test_retrieval_cache_service.py
git status --short
~~~

Expected result: only the cache service and its focused test are modified after the already committed design/plan documents; the diff contains no API key, endpoint, request-body, or live-call code.

### Task 4: Commit and publish the isolated qualification candidate

**Files:**
- Modify: none
- Commit: the design, plan, implementation, and focused tests from this branch

**Interfaces:**
- Consumes: fresh test, lint, typecheck, and diff evidence from Task 3.
- Produces: a pushed branch that remains isolated from the pinned fork and upstream synchronization.

- [ ] **Step 1: Stage only the intended files**

Run:

~~~
git add docs/superpowers/specs/2026-07-21-upstream-cache-compatibility-design.md docs/superpowers/plans/2026-07-21-upstream-cache-compatibility.md packages/shared-python/shared/services/retrieval/cache_service.py packages/shared-python/shared/tests/test_retrieval_cache_service.py
git diff --cached --check
git diff --cached --stat
~~~

Expected result: no whitespace errors and only the four listed paths are staged.

- [ ] **Step 2: Commit the candidate**

Run:

~~~
git commit -m "fix: include BYOK models in retrieval cache identity"
~~~

Expected result: a new commit on fix/kiwi-shane/upstream-cache-compatibility-20260721.

- [ ] **Step 3: Push only the qualification branch**

Run:

~~~
git push origin fix/kiwi-shane/upstream-cache-compatibility-20260721
~~~

Expected result: the candidate branch is pushed. Do not create a PR, merge it, or change the fork's pinned baseline in this plan.

- [ ] **Step 4: Verify the published branch state**

Run:

~~~
git status --short
git rev-parse HEAD
git rev-parse origin/fix/kiwi-shane/upstream-cache-compatibility-20260721
git log -1 --oneline
~~~

Expected result: empty status, matching local/remote commit IDs, and a commit message describing BYOK cache identity. Report the known unrelated baseline failures separately if they remain.
