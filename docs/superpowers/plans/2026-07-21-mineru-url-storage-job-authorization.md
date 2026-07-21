# Plan: MinerU URL-Mode Job-Scoped Storage Authorization

> **Execution note:** Follow this plan task by task in the isolated worktree
> `fix/kiwi-shane/mineru-url-storage-job-authorization-20260721`.

## Goal

Close the BL-092 MinerU PDF URL-mode propagation gap by carrying the existing
`ParseSession.job_metadata` into source-object verification, source upload, and
presigned download URL calls. Keep local MinerU and direct-upload behavior
unchanged, and prove the boundary with synthetic contract tests.

## Task 1: Add failing contract coverage

Files:

- Add `apps/worker/tests/contract/test_mineru_url_storage_authorization_contract.py`.
- Reuse the existing synthetic metadata shape from
  `apps/worker/tests/contract/test_source_storage_authorization_contract.py`.

Tests to add before implementation:

1. `test_mineru_storage_boundary_rejects_missing_authorization_before_adapter`
   creates a real `JobFileStorage` with a recording adapter, enables remote
   object-storage calls with `S3_TYPE=s3`, calls `verify_upload_exists` without
   metadata, and asserts `PermissionDeniedException` plus zero adapter calls.
2. `test_mineru_storage_boundary_rejects_invalid_authorization_before_adapter`
   repeats the same assertion with `approved=False` metadata.
3. `test_mineru_url_source_helpers_forward_approved_metadata` monkeypatches the
   PDF service storage seam with a recording fake and verifies the same metadata
   object is passed to source verification, source upload, and presigning.
4. `test_mineru_provider_forwards_job_metadata_to_cloud` patches
   `provider.parse_via_full`, invokes cloud `parse_pdf`, and asserts the
   metadata is forwarded while the local path remains untouched.
5. `test_pdf_parser_forwards_job_metadata_to_standard_and_fast_paths` patches
   `parser.parse_pdf` and the Markdown stage, then exercises a normal PDF and a
   one-shard anatomy profile to assert metadata is present in both calls.
6. `test_cached_rendered_pdf_inspection_forwards_job_metadata` patches
   `rendered_transform.get_existing_mineru_source_s3_key` and asserts the
   metadata reaches the cached-source inspection helper.

Run the new file first:

```powershell
uv run pytest apps/worker/tests/contract/test_mineru_url_storage_authorization_contract.py -q
```

The propagation tests must fail against the current signatures/call sites;
the real storage-boundary tests establish the existing fail-closed baseline.

## Task 2: Thread metadata through the MinerU URL-mode seam

Files:

- `apps/worker/app/services/document_parser/providers/mineru/pdf_service.py`
- `apps/worker/app/services/document_parser/providers/mineru/provider.py`
- `apps/worker/app/services/document_parser/formats/pdf/parser.py`
- `apps/worker/app/services/document_parser/formats/pdf/rendered_transform.py`

Implementation steps:

1. Add optional `job_metadata: dict[str, object] | None = None` to
   `_inspect_mineru_source_s3_key`, `get_existing_mineru_source_s3_key`,
   `resolve_mineru_source_s3_key`, and `parse_via_full`.
2. Pass `job_metadata` to `verify_upload_exists`, `upload_source_file`, and
   `generate_upload_download_url` in the PDF service.
3. Add the optional keyword to MinerU provider `parse_pdf`; forward it only to
   cloud `parse_via_full`. Leave `parse_via_local` argument behavior unchanged.
4. Forward existing `parse_pdfs` metadata to the standard parse call, the
   shard fast path, and every parallel shard parse call.
5. Pass metadata from cached rendered-PDF inspection to
   `get_existing_mineru_source_s3_key`.
6. Keep the existing fallback/error logging and direct-upload behavior intact;
   do not change shared storage authorization or external provider policy.

Run the new contract file again and confirm all propagation tests pass.

## Task 3: Run focused regression and static checks

Commands from the repository root:

```powershell
uv run pytest apps/worker/tests/contract/test_mineru_url_storage_authorization_contract.py apps/worker/tests/contract/test_mineru_provider_contract.py apps/worker/tests/contract/test_pdf_shard_cleanup_authorization_contract.py apps/worker/tests/contract/test_source_storage_authorization_contract.py -q
uv run ruff check apps/worker/app/services/document_parser/providers/mineru/pdf_service.py apps/worker/app/services/document_parser/providers/mineru/provider.py apps/worker/app/services/document_parser/formats/pdf/parser.py apps/worker/app/services/document_parser/formats/pdf/rendered_transform.py apps/worker/tests/contract/test_mineru_url_storage_authorization_contract.py
uv run pyright --project pyproject.toml apps/worker/app
```

If the focused tests expose an unrelated environment dependency, preserve the
failure output in the evidence note and run the smallest available local
substitute; do not bypass a failed authorization assertion.

## Task 4: Record bounded evidence and update canonical project records

Files in the RA repository:

- `docs/external_call_authorization_audit_inventory.md`
- `docs/maintenance/external_call_authorization_audit_20260720.md`
- `docs/project_backlog.md`
- `docs/project_checkpoint.md`
- `docs/RA_Codex_Workflow_Runner_Project_SOP_v1.1.docx`

Record only the verified scope:

- MinerU PDF URL-mode source verify/upload/presign now receives existing
  job-scoped metadata.
- Synthetic missing/invalid authorization fails before the storage adapter;
  approved metadata propagation passes.
- No live S3/MinerU call, source-owner/native qualification, private/provider
  pilot promotion, or host-level no-egress proof is implied.
- BL-092 remains open for any other metadata-less external-call seams.

Use the existing canonical audit rows and backlog/checkpoint sections rather
than adding a duplicate rule document. Update the SOP in the same RA change
set because workflow authorization behavior changed. Keep local/private
artifacts out of Git.

## Task 5: Validate, commit, and push

Knowhere branch:

```powershell
git diff --check
git status --short
git add -- <implementation-and-test-files> docs/superpowers/specs/2026-07-21-mineru-url-storage-job-authorization-design.md docs/superpowers/plans/2026-07-21-mineru-url-storage-job-authorization.md
git diff --cached --check
git commit -m "fix: authorize MinerU URL storage per job"
git push -u origin fix/kiwi-shane/mineru-url-storage-job-authorization-20260721
```

RA branch changes, if required by Task 4, are validated and committed/pushed
separately on `codex/ra-v04-admission-ai-utility`. Do not stage generated
client files, private evidence, or any `.worktrees` content. Do not sync with
upstream.

Completion evidence must include fresh test output, both commit hashes, and
push status. Existing worktrees and branches must remain intact.
