# Terminal-Job BYOK Credential Cleanup Boundary

## Goal

Close the cleanup race left after terminal-job resolution was made fail-closed:
when a task failure observes a Job that is already terminal, remove the
job-scoped encrypted credential without deleting credentials for an active
retryable Job.

## Existing gap

The worker failure handler deleted credentials only when its own
`finalize_job_failure()` call returned true. A concurrent finalizer or a
redelivered task can make that call return false because the Job is already
`done` or `failed`. In that case, ciphertext remained until the expiry sweeper
ran. The resolver correctly rejected terminal jobs, but cleanup was not
immediate or race-aware.

## Design

1. Add a conditional delete that removes a credential only when the
   authoritative Job row is in the shared `TERMINAL_STATES` set.
2. Call that conditional cleanup after every failure-finalization attempt.
   A false finalization result therefore cleans a concurrently terminal Job,
   while a still-active Job remains protected for retry.
3. Use the same terminal-scoped method in stale-job cleanup after the state
   transition succeeds.
4. Keep the existing unconditional delete for success/explicit terminal
   paths whose caller already owns the lifecycle decision.

## Boundary

This is local database lifecycle evidence only. It does not prove provider-side
retention/deletion, host-level egress, production deployment behavior, private
pilot readiness, RA acceptance, or upstream compatibility.

## Acceptance cases

- A failed/done Job's credential is deleted by terminal-scoped cleanup.
- A running Job's credential is not deleted by the same method.
- Failure handling invokes terminal-scoped cleanup even when finalization
  reports that the Job was already terminal.
- Retryable active Jobs retain their credential for the retry path.
