# D2 local MinerU integrated retrieval implementation plan

## Task 1: Lock the verifier contract before implementation

1. Extend `apps/api/tests/contract/test_d2_local_mineru_compose_contract.py` or
   the existing D2 verifier contract with required integrated-probe markers:
   `parse_task`, `run_retrieval_query`, `source_sha256`, archive/delete checks,
   and the stable success line.
2. Run the focused contract test and record the expected failure before adding
   the verifier probe.

## Task 2: Add the local-only integrated probe

1. Add a guarded PowerShell here-string after worker health checks in
   `deploy/local-dev/verify-d2.ps1`.
2. In the worker container, generate a deterministic synthetic PDF, compute its
   SHA-256, create a file-ingestion job, upload the source, and enqueue the
   existing `app.core.tasks.document_ingestion_tasks.parse_task` signature.
3. Poll the database for terminal status and assert result publication,
   document metadata traceability, result ZIP manifest/source identity, chunk
   locator, and retrieval identity.
4. Assert cross-user/cross-namespace isolation, archive exclusion, hard-delete
   storage cleanup, and post-delete retrieval non-visibility.
5. Always clean synthetic rows, files, and storage objects; emit a stable
   success line only after every assertion passes.

## Task 3: Run verification against the pinned local runtime

1. Run the focused contract test, PowerShell parse check, and changed-scope
   Python checks.
2. Start the existing D2 local MinerU overlay without rebuilding unrelated
   services.
3. Run `verify-d2.ps1 -LocalMineru`, capture the integrated probe output, and
   confirm the stack is restored to its prior cloud-default idle state.

## Task 4: Update the RA checkpoint and revision history

1. Record the exact integrated evidence and remaining BL-094/BL-095 gates in
   the RA checkpoint/backlog.
2. Run the smallest relevant Knowhere and RA health checks.
3. Stage only project-governance/code/docs changes, commit, and push; keep
   local model files, pilot evidence, and DOCX/private artifacts untracked.
