# Plan: MinerU Result Download Authorization

## Goal

Close the direct polling/result-ZIP metadata authorization gap while
preserving the existing MinerU opt-in and pinned-download controls.

## Task 1: Add failing contract coverage

- Assert missing `mineru` job authorization fails before status/quota work.
- Assert approved metadata reaches the provider-returned result ZIP boundary.
- Assert `parse_via_full()` forwards the metadata into polling.

## Task 2: Implement the bounded guard

- Add optional job metadata to `poll_mineru_task()`.
- Reuse `JobMetadataHelper.require_external_call_authorization()` with
  provider `mineru` after the existing operator/endpoint checks.
- Forward metadata from `parse_via_full()` to the polling helper.

## Task 3: Verify and hand off bounded evidence

- Run focused MinerU polling, provider, URL-storage, returned-URL,
  remote-input, Ruff, Pyright, compile, and diff checks.
- Attempt the worker suite and distinguish existing infrastructure/order
  failures from this candidate.
- Keep live provider calls, private data, deployment, and upstream
  synchronization out of scope.
