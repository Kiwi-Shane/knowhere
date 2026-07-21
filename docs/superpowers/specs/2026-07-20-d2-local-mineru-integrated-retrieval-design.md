# D2 local MinerU integrated retrieval qualification

## Objective

Close the missing WP-02/BL-093 implementation gate with one repeatable,
synthetic flow that exercises the real local MinerU worker seam and the
retrieval-serving lifecycle. This is a qualification probe, not a production
client or provider run.

## Scope and boundary

- Run only when `verify-d2.ps1 -LocalMineru` is selected.
- Generate a public synthetic PDF inside the worker container and record its
  SHA-256 in job `document_metadata`.
- Use the existing `parse_task` Celery entrypoint, local object storage, result
  ZIP publication, retrieval query, archive path, and hard-delete path.
- Keep the probe fail-closed: a missing result, missing locator, scope leak,
  stale visibility, failed cleanup, or local-worker fallback is a failure.
- Remove every synthetic database row and storage object in a `finally` block.

## Qualification assertions

1. The uploaded source is processed by `MINERU_PROVIDER=local` through the
   existing worker task and reaches `done` with a `JobResult`.
2. Result ZIP metadata identifies the source file, and the published document
   metadata preserves the source SHA-256.
3. At least one published chunk exists with a non-root section/locator path;
   retrieval of a unique marker returns the generated document and that path.
4. The same marker is invisible under a different user and namespace.
5. Archive removes the document from retrieval, and hard delete removes the
   document, result rows, upload, result ZIP/raw artifacts, and retrieval hit.
6. The probe emits a stable success line so the PowerShell verifier cannot pass
   on partial or diagnostic-only output.

## Non-goals

- No real provider session, API secret, external review job, destination, or
  retention policy is invoked.
- No host-level no-egress claim is made; the existing container negative probe
  remains the only network assertion.
- No new shared schema, package archetype, or reusable runtime service is
  introduced. The probe extends the existing D2 verifier and its contract
  test.
