# Terminal-Job BYOK Credential Cleanup Implementation Plan

## Scope

Implement the bounded lifecycle cleanup described in
`2026-07-21-terminal-job-credential-cleanup-design.md` on
`fix/kiwi-shane/terminal-job-credential-cleanup-20260721`.

Constraints: preserve the pinned fork, do not fetch/sync/merge/rebase, do not
touch other worktrees, do not call providers, and do not process private
sources.

## Steps

- [x] Add RED contracts for terminal-only deletion and the already-terminal
      failure-finalization race.
- [x] Add conditional terminal cleanup to the shared credential service and
      wire worker failure/stale-job paths to it.
- [x] Run focused, adjacent, lint, type, compile, and diff validation.
- [x] Record candidate evidence and the non-promotion boundary.
- [ ] Commit, push, and verify local/remote parity without upstream sync.

## Evidence boundary

The candidate can establish only local conditional deletion behavior against
synthetic contract data. Provider retention/deletion, host-level egress,
production equivalence, RA acceptance, runtime promotion, and upstream
synchronization remain unqualified.

## Implementation evidence (2026-07-21)

- [x] TDD RED observed for both the missing terminal-scoped service method and
      the already-terminal failure-finalization cleanup race.
- [x] Worker cleanup/stale/parse-failure selection passed `7` tests with `10`
      unrelated tests deselected.
- [x] API BYOK contract passed `2` tests; the expanded shared selection passed
      `43` tests.
- [x] Ruff check/format, Pyright, Python compile, and `git diff --check`
      passed for changed runtime and contract files.
- [x] Full shared suite recorded `54 passed` and the same two unrelated
      page-memory VLM fixture failures caused by legacy one-argument
      `get_openai_client` lambdas.
- [ ] Provider retention/deletion, host-level egress, production deployment,
      private-pilot readiness, RA acceptance, runtime promotion, and upstream
      synchronization remain out of scope. The fork remains pinned and
      `sync_authorized=false`.
