# Terminal-Job BYOK Resolution Boundary

## Goal

Prevent worker-side BYOK credential resolution for jobs already in a terminal
state. A stale credential row must not be enough to authorize decryption after
the job has reached `done` or `failed`.

## Existing gap

`JobLLMCredentialService.resolve_sync()` checked the credential owner,
credential lifecycle, expiry, and endpoint policy, but it did not inspect the
authoritative `jobs.status`. The worker loads the parse context before its
state gate, so a redelivered terminal job could reach credential decryption
before cleanup removed the row.

## Design

1. Select the owning Job status together with the credential and owner ID.
2. Reject `done` and `failed` jobs with the existing
   `JobLLMCredentialResolutionError` before decrypting the encrypted payload.
3. Keep pending/running/converting behavior unchanged; these are the active
   worker lifecycle states that may resolve a credential.
4. Reuse the canonical `TERMINAL_STATES` set from the shared state machine.
   Do not create a second terminal-state list or a new schema/migration.

## Boundary

This is a local fail-closed resolution guard. It does not prove provider
retention/deletion, host-level egress, cleanup reliability, production
deployment behavior, RA acceptance, or upstream compatibility.

## Acceptance cases

- A `done` job with an otherwise active credential is rejected before decrypt.
- A `failed` job with an otherwise active credential is rejected before decrypt.
- An active `running` job still resolves when owner, expiry, and endpoint
  policy checks pass.
- Existing missing-reference, owner-mismatch, expiry, encryption, and endpoint
  policy behavior remains unchanged.
