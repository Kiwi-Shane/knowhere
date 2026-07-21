# Plan: Source URL Download Authorization

## Goal

Close the outbound source URL authorization gap while preserving existing URL
hardening and synthetic/local contracts.

## Task 1: Add failing contract coverage

- Assert that source URL download rejects missing job authorization before URL
  validation when the operator opt-in is enabled.
- Assert that production source URL operations reject a disabled operator opt-in
  before DNS/URL validation.
- Assert that approved metadata reaches the pinned transfer and worker URL
  upload helper.
- Assert that URL extension resolution is also blocked before DNS when the
  operator opt-in is disabled.

## Task 2: Implement the bounded gate

- Add the default-off `SOURCE_URL_EXTERNAL_CALLS_ENABLED` setting.
- Centralize source URL operator and job authorization checks.
- Gate URL extension validation/optional `HEAD` inspection and the final pinned
  download.
- Thread job metadata through worker extension resolution and download.
- Preserve authorization exception types instead of converting them to a
  generic URL validation error.

## Task 3: Verify and hand off bounded evidence

- Run focused shared, worker, and API contracts, Ruff, changed-runtime
  Pyright, compile, and diff checks.
- Keep live URL/provider/storage calls, private data, deployment, and upstream
  synchronization out of scope.
- Record the candidate on its isolated branch and hand it to the RA evidence
  workflow as a non-merged, non-qualified safety candidate.
