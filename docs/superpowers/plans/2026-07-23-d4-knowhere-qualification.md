# Knowhere D4 retrieval qualification plan

## Baseline

- repository: `Kiwi-Shane/knowhere`
- live default branch: `main`
- live default head at worktree creation:
  `ade8595a79c1e0c02ea8de8f76b79250a464ba7b`
- D1 schema: `schemas/knowledge-retrieval-result-v1.schema.json`
- D1 fixture: `examples/contracts/knowledge-retrieval-result-v1/example.json`
- no upstream synchronization or private-data execution

## Tasks

- [ ] Add D4 tests first for explicit locator serialization, result
  qualification, fail-closed control aggregation, and scoped hard deletion.
- [ ] Add the opt-in source-owned result serializer and technical qualification
  validator in the shared retrieval boundary.
- [ ] Add user-scoped hard-delete lifecycle and storage cleanup, preserving the
  existing archive path and cache-version invalidation behavior.
- [ ] Add the synthetic D4 control harness and report runner using generated
  identifiers, temporary local state, and no external destinations.
- [ ] Run focused tests, relevant API/worker regressions, Ruff, and repository
  cleanliness/private-artifact checks.
- [ ] Bind the D4 evidence packet to the final source revision, D1 schema and
  fixture hashes, and the live default preflight. Record deferred RA/native/
  private/release gates explicitly.
- [ ] Commit and push the Knowhere feature branch, then update the RA D4
  descriptor/evidence/checkpoint only after the Knowhere revision is verified.

## Verification commands

```text
python -m pytest -q \
  packages/shared-python/shared/tests/test_knowledge_retrieval_result_serializer.py \
  packages/shared-python/shared/tests/test_retrieval_qualification.py \
  apps/worker/tests/qualification/test_knowhere_d4_qualification.py

python -m pytest -q \
  apps/api/tests/contract/test_documents_contract.py \
  apps/api/tests/contract/test_retrieval_contract.py \
  apps/api/tests/contract/test_dashboard_token_permission_contract.py

ruff check packages/shared-python/shared/services/retrieval \
  packages/shared-python/shared/services/storage/job_file_storage.py \
  apps/api/app/api/v1/routes/documents.py \
  apps/api/app/repositories/document_repository.py \
  apps/api/app/services/documents/lifecycle_service.py
```

The qualification result is technical evidence only. A passing D4 result does
not start E-E, D8, D9, private processing, or release.
