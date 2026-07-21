# BYOK credential-reference implementation plan

> Execute this plan in the isolated `byok-credential-reference-20260721`
> worktree only. Do not fetch, merge, rebase, sync, or modify the existing
> candidate or qualification worktrees.

## 1. Establish failing contracts first

- Add focused tests for the endpoint policy, safe Job metadata, encrypted
  credential serialization, owner binding, expiry/revocation, and legacy raw
  metadata fail-closed behavior.
- Add API/worker contract tests with fakes for staging and separate
  `ParseJobContext.llm_config` resolution.
- Run the focused tests and record the expected failures before implementation.

## 2. Add the schema-owned credential boundary

- Add the `JobLLMCredential` SQLAlchemy model and import it in the shared model
  registry.
- Add one Alembic migration after `fbe1c2d3e4f5` with the unique Job FK,
  user-owner FK, encrypted payload, lifecycle columns, and expiry/status
  indexes.
- Add a shared credential service for canonical JSON encryption/decryption,
  async API staging, sync worker resolution, and bounded cleanup.

## 3. Add endpoint admission policy

- Add default-off `LLM_EXTERNAL_CALLS_ENABLED` and an exact
  `LLM_ALLOWED_PROVIDER_ENDPOINTS` setting.
- Implement deterministic HTTPS endpoint normalization and rejection of
  embedded credentials, query/fragment data, local/private literal IPs, and
  non-allowlisted endpoints.
- Apply the same policy at API credential staging and worker resolution.

## 4. Remove raw metadata persistence and wire atomic creation

- Make `JobMetadataHelper.create_from_request()` omit `llm_config` from both
  stored metadata and `original_request`; preserve only presence/reference
  metadata.
- Pass the generated Job ID into scope resolution and attach the staged
  credential object to the same SQLAlchemy unit of work before the existing
  JobRepository commit.
- Preserve v1/no-BYOK behavior and existing source/document scope checks.

## 5. Resolve and clean up in the worker

- Extend `ParseJobContext` with a separate typed config field.
- Resolve the encrypted record using Job/user binding and expiry before
  `init_llm_overrides()`; legacy raw metadata must raise a fail-closed error.
- Delete/revoke at terminal success/final failure and in stale-job expiry;
  do not clean on retry.

## 6. Verify and publish the isolated candidate

- Run focused tests, changed-runtime Ruff/Pyright/compile, migration contract
  checks, and the smallest relevant adjacent ingestion selections.
- Review the diff for raw-key literals, endpoint leaks, unrelated changes, and
  private artifacts.
- Commit and push the isolated branch only. Do not create a PR, merge, or
  upstream-sync action.
- Record evidence and the non-promotion boundary in the RA maintenance/
  checkpoint/backlog files only after the Knowhere verification is complete.
