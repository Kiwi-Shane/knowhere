# Local MinerU Default Production Ingestion Design

## Status

Approved for implementation by the owner on 2026-08-08: the default production
PDF ingestion provider is local MinerU.

## Objective

Promote the already-qualified local MinerU provider from explicit opt-in to the
application default for PDF ingestion. Preserve the existing standard parser
seam, validated artifact boundary, bounded local execution controls, and
fail-closed behavior.

## Context

The local provider already runs MinerU in a separate process, validates the
versioned artifact manifest and source hash, publishes `full.md`, images, and a
sanitized log, and removes temporary raw work. The standard PDF parser consumes
the published `full.md` through the existing downstream parser.

The previous design intentionally kept cloud as the default. That decision is
superseded for this work package by the owner's explicit decision to make local
MinerU the default production ingestion path.

## Considered approaches

1. **Selected: change the provider default and document explicit cloud
   rollback.** Reuse the existing local provider and runtime preflight. This is
   the smallest change and does not duplicate parser logic.
2. **Replace the standard parser with a new MinerU retrieval adapter.**
   Rejected for this package because it would change downstream parsing and
   retrieval semantics beyond the qualified provider seam.
3. **Keep cloud as default and route only a canary queue to local.** Rejected
   because it contradicts the owner's explicit default-production decision;
   the separate-deployment rollback boundary remains available.

## Scope

### In scope

- Set `MINERU_PROVIDER` default to `local`.
- Keep local runtime preflight enabled by default and fail startup when the
  configured local runtime is unusable.
- Preserve local process isolation, concurrency-one defaults, artifact
  validation, sanitized logs, and no implicit cloud fallback.
- Update the operator guide so cloud is an explicit rollback override rather
  than the normal default.
- Update focused provider/configuration contracts and document the deployment
  requirement for `MINERU_LOCAL_PROJECT_PATH` and `MINERU_LOCAL_UV_EXECUTABLE`.

### Out of scope

- Changing the MinerU parser implementation or model/backend settings.
- Adding cloud fallback or automatic retry after a local failure.
- Changing DOCX routing.
- Enabling automatic answer authority, semantic answer acceptance, evidence
  promotion, unattended workflow, or Pro as a verification authority.
- Adding raw PDFs, MinerU outputs, or private evidence to Git.
- Changing the RA retrieval contract or the separate RA/Knowhere remediation
  worktrees.

## Runtime behavior

- With no `MINERU_PROVIDER` override, PDF ingestion selects `local`.
- Local mode requires a configured, validated MinerU checkout and `uv`
  executable. Missing or invalid configuration fails the worker preflight; it
  does not silently select cloud.
- A local parse invokes the existing isolated MinerU runner exactly once for
  the request. The provider publishes only the validated downstream artifacts
  and sanitized log.
- A local parse failure is surfaced as a bounded local-provider error and does
  not retry through cloud.
- To roll back, deploy a separately configured worker with
  `MINERU_PROVIDER=cloud`; do not mutate a busy worker in place.

## Acceptance criteria

1. `MineruConfig().MINERU_PROVIDER == "local"`.
2. The provider contract proves the default path selects local and the cloud
   path remains available only through an explicit configuration value.
3. Existing local provider, runtime preflight, capacity, artifact, and
   integration contracts remain green.
4. The local production guide states the required local runtime configuration,
   no-fallback behavior, and explicit cloud rollback.
5. No private source or generated MinerU output is changed or staged.
6. Retrieval candidates remain navigation-only and require native verification;
   this change does not establish semantic answer correctness or automatic
   authority.

## Verification

- Focused RED/GREEN provider and configuration tests.
- Focused runtime preflight and local process contract tests.
- Focused real local MinerU integration test when the pinned local runtime is
  available; otherwise report it as not executed rather than inferring a pass.
- Ruff on changed Python files and final Git scope/status review.
