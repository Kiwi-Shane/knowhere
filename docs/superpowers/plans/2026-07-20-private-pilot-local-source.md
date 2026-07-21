# Private Local MinerU Pilot Qualification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing opt-in D2 verifier so an authorized local PDF or DOCX can traverse the pinned local MinerU Worker, retrieval, archive, deletion, and cross-scope checks without exposing source content or changing the cloud-default path.

**Architecture:** Keep the existing synthetic integrated probe as the default. Add an explicit `-PrivatePilotSourcePath` plus required `-PrivatePilotRetrievalQuery` mode behind `-LocalMineru`; copy the selected source into the API container only for the run, pass only private-safe status markers to the host, and remove the container copy and all database/object-storage rows in `finally`. The pilot records automated source-integrity and lifecycle evidence only; it cannot manufacture a human baseline, host-level egress proof, or provider approval.

**Tech Stack:** PowerShell 7 verifier, Docker Compose/D2 internal network, Python inline probe, pytest contract tests, pinned local MinerU image/model mount, internal LocalStack S3.

## Global Constraints

- The cloud-default D2 Worker remains unchanged unless `-LocalMineru` is explicitly supplied.
- `-PrivatePilotSourcePath` requires `-LocalMineru`, a regular `.pdf` or `.docx` file, and a non-empty query; invalid inputs fail before container execution.
- Private source paths, source contents, extracted text, and diagnostics containing content remain local/private and are never committed.
- Private mode must not print the absolute source path, source content, or chunk prefixes; it may print only stable pass/fail markers and counts if needed.
- Private mode uses a 1800-second bounded poll for large local extraction, aligned with the local provider process timeout; synthetic mode retains the 240-second bound.
- The probe must clean source objects, result objects, temporary files, database rows, and the copied container source on success and failure.
- This evidence does not claim `offline_verified=true`, human review, provider execution, regulatory readiness, or upstream synchronization.

---

### Task 1: Add the failing verifier contract

**Files:**
- Modify: `apps/api/tests/contract/test_d2_local_mineru_compose_contract.py`
- Modify: `deploy/local-dev/verify-d2.ps1`

**Interfaces:**
- Produces the required verifier surface: `-PrivatePilotSourcePath`, `-PrivatePilotRetrievalQuery`, local-mode gating, private environment forwarding, privacy-safe success marker, and cleanup marker.

- [x] **Step 1: Write the failing test**

Add two tests to the existing local-MinerU contract module:

```python
def test_private_pilot_verifier_requires_local_mode_and_private_inputs() -> None:
    verifier = VERIFIER_PATH.read_text(encoding="utf-8")
    for marker in (
        "[string] $PrivatePilotSourcePath",
        "[string] $PrivatePilotRetrievalQuery",
        "PrivatePilotSourcePath requires -LocalMineru",
        "D2_PRIVATE_SOURCE_PATH",
        "D2_PRIVATE_SOURCE_FILE_NAME",
        "D2_PRIVATE_RETRIEVAL_QUERY",
    ):
        assert marker in verifier, marker


def test_private_pilot_verifier_has_privacy_safe_pass_and_cleanup_markers() -> None:
    verifier = VERIFIER_PATH.read_text(encoding="utf-8")
    for marker in (
        "D2 local MinerU private pilot probe passed",
        "D2_PRIVATE_PILOT=true",
        "base64 -d -i",
        "D2 private source cleanup completed",
    ):
        assert marker in verifier, marker
```

- [x] **Step 2: Run test to verify it fails**

Run:

```powershell
& .\.venv\Scripts\python.exe -m pytest apps/api/tests/contract/test_d2_local_mineru_compose_contract.py -q
```

Expected: the two new tests fail because the current verifier has only the synthetic probe and no private-source interface.

### Task 2: Implement the fail-closed private source mode

**Files:**
- Modify: `deploy/local-dev/verify-d2.ps1`
- Modify: `apps/api/tests/contract/test_d2_local_mineru_compose_contract.py`

**Interfaces:**
- PowerShell parameters: `[switch] $LocalMineru`, `[string] $PrivatePilotSourcePath`, `[string] $PrivatePilotRetrievalQuery`.
- Container environment: `D2_PRIVATE_PILOT=true`, `D2_PRIVATE_SOURCE_PATH`, `D2_PRIVATE_SOURCE_FILE_NAME`, `D2_PRIVATE_RETRIEVAL_QUERY`.
- Python success marker: `D2 local MinerU private pilot probe passed`.

- [x] **Step 1: Validate input before running Docker execution**

Resolve the source path, require a regular file with `.pdf` or `.docx` extension, require a non-empty retrieval query, and throw when a private source is supplied without `-LocalMineru`.

- [x] **Step 2: Copy only the selected source into the API container**

Base64-encode the selected file on the host and stream it through `docker exec -i` into the API container's unique `/tmp/d2-private-source-*` tmpfs path; do not use `docker cp` against the read-only API rootfs. Forward only the container path, basename, and query to the inline probe, and never write the source into the repository.

- [x] **Step 3: Parameterize the existing inline probe**

Use the copied source instead of the generated synthetic PDF in private mode; retain source SHA-256, result-manifest, non-root locator, retrieval, archive exclusion, hard-delete cleanup, and cross-scope checks. Replace marker-content assertions with content-free non-empty/retrieval assertions in private mode.

- [x] **Step 4: Add `finally` cleanup**

Remove the copied source from the API container after the probe regardless of pass/fail, while retaining the existing Python database/object-storage cleanup.

- [x] **Step 5: Run focused tests and syntax checks**

Run:

```powershell
& .\.venv\Scripts\python.exe -m pytest apps/api/tests/contract/test_d2_local_mineru_compose_contract.py -q
$tokens=@(); $errors=@(); $null=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'deploy/local-dev/verify-d2.ps1'), [ref]$tokens, [ref]$errors); if($errors.Count){throw ($errors | Out-String)}; 'PowerShell parse passed'
```

Expected: focused contract tests pass and the verifier parses without errors.

### Task 3: Execute local/private evidence

**Files:**
- Local only: `C:\Users\psc01\pilot-private\private-shadow-20260720\evidence\local-mineru-private-pilot-20260720\`
- Read-only inputs: `C:\Users\psc01\pilot-private\private-shadow-20260720\source\*.pdf`, `*.docx`

- [x] **Step 1: Start the pinned local-MinerU D2 overlay**
- [x] **Step 2: Run the private PDF pilot with a source-supported safe query**
- [x] **Step 3: Run the private DOCX pilot with a source-supported safe query**
- [x] **Step 4: Repeat each run and run invalid-path/invalid-extension/no-local negative checks**
- [x] **Step 5: Check no private source residue remains in the API container, S3 buckets, database, or repository**

### Task 4: Record the evidence without promoting the gates

**Files:**
- Modify: `C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\project_backlog.md`
- Modify: `C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\project_checkpoint.md`
- Modify: `C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\maintenance\v04_program_change_impact_decision_20260719.md`
- Modify: `C:\Users\psc01\OneDrive\文件\cross-repo-worktrees\ra-v04-admission-ai-utility\docs\RA_Codex_Workflow_Runner_Project_SOP_v1.1.docx` only if workflow behavior changes materially.

- [x] **Step 1: Record private source hashes/status counts only**
- [x] **Step 2: Keep human baseline, host no-egress, and provider gates explicitly open**
- [x] **Step 3: Run project health/changed-scope validation**
- [x] **Step 4: Commit and push the Knowhere and RA documentation revisions**
