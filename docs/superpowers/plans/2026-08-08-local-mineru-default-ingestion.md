# Implementation Plan: Local MinerU Default Production Ingestion

> **Execution note:** Use the `superpowers:executing-plans` skill to execute
> this plan task by task, preserving the RED/GREEN checkpoints.

**Goal:** Make the existing validated local MinerU provider the default PDF
ingestion provider while retaining explicit cloud rollback and no implicit
fallback.

**Design:** Reuse the existing local provider boundary in Knowhere. Change
only the provider default and the operator-facing deployment contract; do not
replace the downstream Markdown parser or change RA authority/retrieval
semantics.

**Worktree:** `E:\Codex\20-worktrees\knowhere\mineru-default-production-ingestion-20260808`

## Task 1: Establish the failing default contract

**Files:**

- Modify: `apps/worker/tests/contract/test_mineru_provider_contract.py`

1. Rename the cloud-default test to describe explicit cloud rollback.
2. Assert `MineruConfig().MINERU_PROVIDER == "local"` as the application
   default.
3. Keep the explicit cloud delegation assertions so the rollback path remains
   covered.
4. Run the focused test and confirm it fails only because the production
   default is still `cloud`.

Command:

```powershell
python -m pytest -q --noconftest -p no:cacheprovider `
  apps/worker/tests/contract/test_mineru_provider_contract.py `
  -k "default or cloud_provider"
```

## Task 2: Switch the production default to local

**Files:**

- Modify: `packages/shared-python/shared/core/config/mineru.py`

1. Change the `MINERU_PROVIDER` default from `cloud` to `local`.
2. Update the description to state that local is the default and cloud is an
   explicit rollback override.
3. Do not add fallback logic or change any local runner settings.
4. Re-run the Task 1 focused test and confirm GREEN.

## Task 3: Update the operator contract

**Files:**

- Modify: `docs/guides/local-mineru-production-canary.md`
- Add: `docs/superpowers/plans/2026-08-08-local-mineru-default-ingestion.md`

1. State that local MinerU is the application default.
2. Require `MINERU_LOCAL_PROJECT_PATH`, `MINERU_LOCAL_UV_EXECUTABLE`,
   startup preflight, and concurrency-one settings for a usable deployment.
3. State that cloud is selected only by an explicit separate deployment
   override and that local failures never fall back to cloud.
4. Preserve the canary, observation, and rollback boundaries.

## Task 4: Run focused validation

Run the existing local-provider contract, runtime-preflight contract, local
capacity contract, artifact contract, process contract, and the guarded real
local MinerU integration test when the pinned runtime is available.

Commands:

```powershell
python -m pytest -q --noconftest -p no:cacheprovider `
  apps/worker/tests/contract/test_mineru_provider_contract.py `
  apps/worker/tests/contract/test_mineru_runtime_preflight_contract.py `
  apps/worker/tests/contract/test_mineru_local_capacity_contract.py `
  apps/worker/tests/contract/test_mineru_artifact_contract.py `
  apps/worker/tests/contract/test_local_mineru_process_contract.py
```

If the real runtime is configured, run the existing integration test with
`RUN_LOCAL_MINERU_E2E=1`; otherwise record it as not executed.

## Task 5: Final scope and delivery checks

1. Run Ruff on changed Python files.
2. Run `git diff --check`, inspect the exact changed-path list, and confirm no
   raw source or generated MinerU output is staged.
3. Run the project-required health check if the repository environment allows
   it; report any unrelated baseline failure separately.
4. Commit the completed implementation and documentation as one focused
   revision.
5. Push the branch and open a Draft PR only after all required checks and
   scope review pass.

## Explicit non-claims

This change does not qualify semantic answer correctness, automatic answer
authority, evidence promotion, unattended workflow, or Pro as a verification
authority. Retrieval outputs remain candidates/navigation evidence and retain
the native-verification boundary.
