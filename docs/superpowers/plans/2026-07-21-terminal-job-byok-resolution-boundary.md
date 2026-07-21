# Terminal-Job BYOK Resolution Boundary Implementation Plan

## Scope

Implement the isolated fail-closed guard described in
`2026-07-21-terminal-job-byok-resolution-boundary-design.md` on
`fix/kiwi-shane/credential-terminal-boundary-20260721`.

Constraints: preserve the pinned fork, do not fetch/sync/merge/rebase, do not
touch other worktrees, and do not add provider calls or external runtime
state.

## Steps

- [x] Add a failing terminal-job resolution test covering the old two-column
      result unpacking boundary.
- [x] Include authoritative Job status in the credential resolution query and
      reject terminal jobs before decryption.
- [x] Update focused fakes and preserve active-job, owner, expiry, and endpoint
      policy coverage.
- [x] Run focused, adjacent, lint, type, compile, and diff validation.
- [x] Record candidate evidence and the non-promotion boundary.
- [ ] Commit, push, and verify local/remote parity without upstream sync.

## Evidence boundary

The candidate can establish only that the local resolver refuses terminal-job
credential decryption under the focused synthetic contract. Provider-side
retention/deletion, host-level egress, production equivalence, RA acceptance,
and runtime promotion remain unqualified.

## Implementation evidence (2026-07-21)

- [x] TDD RED observed before the guard: a terminal-job result containing
      authoritative status could not be safely handled by the old two-column
      resolver boundary and did not produce the required terminal rejection.
- [x] Focused BYOK credential tests passed: `14 passed`.
- [x] Expanded shared selection passed: `43 passed` across BYOK credential
      lifecycle, metadata privacy, endpoint policy, cache identity, and
      LLMConfig contracts.
- [x] API BYOK contract passed: `2 passed`; worker stale-job sweeper contract
      passed: `2 passed`.
- [x] Ruff check/format, Pyright, Python compile, and `git diff --check`
      passed for changed implementation/tests.
- [x] Full shared suite had `54 passed` and two pre-existing failures in
      `test_page_memory_vlm_limiter.py`; those failures are unrelated to this
      terminal-job guard and remain unchanged from the prior candidate
      baseline.
- [ ] Provider retention/deletion, host-level egress, production deployment,
      RA acceptance, runtime promotion, and upstream synchronization remain
      out of scope. The fork remains pinned and `sync_authorized=false`.
