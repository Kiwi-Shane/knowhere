# D2 Local MinerU Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Integrate a pinned local MinerU runtime into an opt-in D2 Worker overlay while preserving the characterized cloud-default D2 harness.

**Architecture:** Extend content-free preflight with an optional model-root check. Build a dedicated Linux Worker image from a named MinerU source context, mount models read-only, and add a compose overlay that replaces the D2 Worker only when explicitly selected. Add verifier mode and update the canary runbook.

**Tech Stack:** Python 3.12, Pydantic, pytest, Ruff, Docker BuildKit/Compose, PowerShell, YAML, Celery/gevent.

## Global Constraints

- Standard D2 remains cloud-default and retains its five-service contract.
- Local overlay is opt-in and mutually exclusive with the cloud Worker for the same project and queues.
- MinerU installation uses uv sync --locked --no-dev --extra pipeline.
- Worker, local-job, and shard concurrency remain 1; local failures never fall back to cloud.
- Model root is read-only; missing source, runtime, adapter, model root, disk, or memory fails closed.
- No private source, model files, pilot evidence, secrets, or generated DOCX files enter Git.
- Offline requested is not offline verified; no upstream sync or host egress attestation is claimed.
- Preserve existing dirty readiness, upstream-candidate, and MinerU worktrees.

---

### Task 1: Model-root preflight

**Files:**
- Modify: packages/shared-python/shared/core/config/mineru.py
- Modify: apps/worker/app/services/document_parser/providers/mineru/runtime_preflight.py
- Test: apps/worker/tests/contract/test_mineru_runtime_preflight_contract.py

**Interfaces:**
- Input: current local runtime config.
- Output: MINERU_LOCAL_MODEL_ROOT string, boolean models check, stable models_missing error code.

- [ ] Write failing tests for a missing configured model directory and an existing model directory. Update the ready-status fixture to expect models=true and keep the cloud-bypass fixture unchanged.

- [ ] Run:
    
    & 'C:\Users\psc01\workspace\knowhere\.worktrees\d2-local-mineru-worker-20260720\.venv\Scripts\python.exe' -m pytest apps/worker/tests/contract/test_mineru_runtime_preflight_contract.py -q
    
    Expected: FAIL because the setting and models check are absent.

- [ ] Implement MINERU_LOCAL_MODEL_ROOT with default empty string. Add it to the runtime protocol and add models: models_missing to the stable error map. Resolve only the optional directory and add models: root-is-empty-or-directory to checks. Keep status serialization path-free and file-list-free.

- [ ] Re-run the focused pytest; expected PASS. Commit:
    
    git add packages/shared-python/shared/core/config/mineru.py apps/worker/app/services/document_parser/providers/mineru/runtime_preflight.py apps/worker/tests/contract/test_mineru_runtime_preflight_contract.py
    git commit -m "feat: fail closed when local MinerU models are missing"

### Task 2: D2 local overlay contract

**Files:**
- Create: apps/api/tests/contract/test_d2_local_mineru_compose_contract.py

**Interfaces:**
- Input: local overlay, local Dockerfile, and path-stable model JSON.
- Output: static contract for provider selection, named build context, pinned revision, read-only model mount, and D2 restrictions.

- [ ] Write the contract before runtime files. Load deploy/local-dev/docker-compose.d2-local-mineru.yml with the existing Compose tag loader. Assert service set is worker-only; Dockerfile is deploy/docker/Dockerfile.worker.local-mineru; build has mineru-source named context and required MINERU_SOURCE_REVISION; environment has local provider, startup preflight, project /opt/mineru, uv /usr/local/bin/uv, Python /opt/mineru/.venv/bin/python, model root /mnt/models/mineru, model source local, config /opt/mineru/mineru.json, and both concurrency values 1. Assert no ports, read_only, cap_drop ALL, no-new-privileges, and a read-only /mnt/models/mineru bind mount whose source is the required MINERU_MODEL_ROOT Compose variable. Assert Dockerfile contains named-context copies, locked pipeline install, source revision label, and local offline environment. Assert model JSON is exactly the three-key contract: models-dir.pipeline /mnt/models/mineru, models-dir.vlm empty, model-source local, config_version 1.3.2.

- [ ] Run:
    
    & 'C:\Users\psc01\workspace\knowhere\.worktrees\d2-local-mineru-worker-20260720\.venv\Scripts\python.exe' -m pytest apps/api/tests/contract/test_d2_local_mineru_compose_contract.py -q
    
    Expected: FAIL because the three runtime files do not exist.

- [ ] Commit the test-only contract:
    
    git add apps/api/tests/contract/test_d2_local_mineru_compose_contract.py
    git commit -m "test: specify D2 local MinerU overlay contract"

### Task 3: Pinned local image and opt-in overlay

**Files:**
- Create: deploy/docker/Dockerfile.worker.local-mineru
- Create: deploy/docker/mineru.local.json
- Create: deploy/local-dev/docker-compose.d2-local-mineru.yml

**Interfaces:**
- Input: operator variables MINERU_SOURCE_CONTEXT, MINERU_SOURCE_REVISION, and MINERU_MODEL_ROOT.
- Output: knowhere-worker:d2-local-mineru with /opt/mineru, its Linux virtualenv, /usr/local/bin/uv, and /mnt/models/mineru.

- [ ] Create deploy/docker/mineru.local.json with no credentials or host paths:
    
    {
      "models-dir": {
        "pipeline": "/mnt/models/mineru",
        "vlm": ""
      },
      "model-source": "local",
      "config_version": "1.3.2"
    }

- [ ] Add a BuildKit Dockerfile using named context mineru-source. The MinerU builder copies only pyproject.toml, uv.lock, README.md, LICENSE.md, and mineru/, installs uv, runs UV_PROJECT_ENVIRONMENT=/opt/mineru/.venv uv sync --locked --no-dev --extra pipeline, and writes source-revision.txt from the required revision arg. Mirror current worker runtime dependencies and appuser setup; copy MinerU venv/source/uv/config into the final image. Set local provider, project, uv, Python, model root, startup preflight, offline/model-source flags, UV_OFFLINE, HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, and MODELSCOPE_OFFLINE. Add an OCI source-revision label; no cloud URL, API key, fallback, or port.

- [ ] Add a worker-only Compose overlay after docker-compose.dev.yml and docker-compose.d2.yml. Use required Compose interpolation for the source context, source revision, and model root. Preserve the D2 container identity, secret, resource limits, restrictions, heartbeat, and queue set. Override provider and all local runtime paths; add the model bind mount at /mnt/models/mineru read_only true; keep concurrency 1. Do not edit docker-compose.d2.yml.

- [ ] Run both new overlay contracts and Task 1 contracts; expected PASS. Commit:
    
    git add deploy/docker/Dockerfile.worker.local-mineru deploy/docker/mineru.local.json deploy/local-dev/docker-compose.d2-local-mineru.yml
    git commit -m "feat: add opt-in D2 local MinerU worker"

### Task 4: Local verifier and runbook

**Files:**
- Modify: deploy/local-dev/verify-d2.ps1
- Modify: apps/api/tests/contract/test_d2_hardened_compose_contract.py
- Modify: docs/guides/local-mineru-production-canary.md

**Interfaces:**
- Input: verify-d2.ps1 -LocalMineru and the three required Compose variables.
- Output: local provider/model-mount assertions plus existing D2 health, lifecycle, backup/restore, rollback, and negative-egress checks.

- [ ] Add failing static assertions for LocalMineru, the local overlay filename, MINERU_PROVIDER=local, MINERU_LOCAL_MODEL_ROOT=/mnt/models/mineru, and ReadOnly. Run the contract and observe failure.

- [ ] Add a [switch] LocalMineru parameter. When selected, append the overlay to existing compose args and use the same project name. Assert effective local provider/model root and a read-only /mnt/models/mineru mount. Preserve all existing restrictions, health, synthetic lifecycle, backup/restore, rollback, HTTPS-negative checks, and no-down behavior.

- [ ] Run:
    
    & 'C:\Users\psc01\workspace\knowhere\.worktrees\d2-local-mineru-worker-20260720\.venv\Scripts\python.exe' -m pytest apps/api/tests/contract/test_d2_hardened_compose_contract.py -q
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path deploy/local-dev/verify-d2.ps1), [ref]$null, [ref]$errors)
    if ($errors) { throw $errors }

- [ ] Add an integrated D2 qualification section to the existing local MinerU canary guide. Require source SHA and model-root checks, then render, build, start, and run verify-d2.ps1 -LocalMineru. State that cloud/local are mutually exclusive, evidence remains outside Git, offline_requested is not offline_verified, and this gate does not start a private pilot or provider review job.

- [ ] Commit:
    
    git add deploy/local-dev/verify-d2.ps1 apps/api/tests/contract/test_d2_hardened_compose_contract.py docs/guides/local-mineru-production-canary.md
    git commit -m "test: verify D2 local MinerU runtime mode"

### Task 5: Integrated gate validation and RA evidence

**Files:**
- Modify RA worktree C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\project_checkpoint.md
- Modify RA worktree C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\project_backlog.md
- Modify RA worktree C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\maintenance\v04_program_change_impact_decision_20260719.md

**Interfaces:**
- Input: Knowhere SHA, tests, Compose config/build/start result, and verifier output.
- Output: exact evidence-supported BL-093 status; BL-094 and BL-095 remain open until their separate gates pass.

- [ ] Run targeted worker/API contracts, Ruff on changed Python files, and git diff --check. Expected all pass.

- [ ] With the three operator variables validated, run Compose config --quiet using dev, d2, and local overlay files. Expected exit 0. If Docker Desktop or source/model context is unavailable, record the limitation and do not claim integrated qualification.

- [ ] If the stack renders and builds, run compose up and verify-d2.ps1 -LocalMineru. Expected local preflight ready, healthy API/Worker, no ports, internal network, lifecycle/isolation/backup/restore/rollback pass, and API/Worker external HTTPS probes fail. Do not run a real private corpus or provider session here.

- [ ] Update the three RA docs with branch/SHA, source label, preflight and verifier results, warnings, and exact BL-093 status. Keep raw private evidence and model bundles outside Git; keep BL-094/BL-095 open.

- [ ] Run:
    
    & 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\.venv\Scripts\python.exe' tools/check_governance_consistency.py
    & 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\.venv\Scripts\python.exe' tools/run_project_health_check.py --allow-dirty
    git -C 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility' status --short
    git -C 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility' add docs/project_checkpoint.md docs/project_backlog.md docs/maintenance/v04_program_change_impact_decision_20260719.md
    git -C 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility' commit -m "Record D2 local MinerU qualification boundary"
    git -C 'C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility' push

Run final clean-state RA health check after the commit. Never stage local Word drafts, evidence directories, model bundles, or .qa material.

## Self-review

- Spec coverage: Tasks 1–3 cover model-root preflight, pinned image, source/model boundary, overlay, cloud-default preservation, and no fallback; Task 4 covers verifier/runbook; Task 5 covers evidence/version-control.
- Placeholder scan: all repository paths and filenames are concrete; operator values are explicit required Compose variables.
- Type consistency: MINERU_LOCAL_MODEL_ROOT is a string consumed by preflight; overlay supplies /mnt/models/mineru; verifier checks the same value; model JSON maps pipeline to the same path.
