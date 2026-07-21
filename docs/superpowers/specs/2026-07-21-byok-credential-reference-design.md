# BYOK job credential-reference and endpoint authorization design

## Context

The upstream BYOK compatibility review at `ac9d9668` found two independent
boundary failures in the document-ingestion job path:

1. `llm_config.model_dump()` was copied into Job metadata and then into the
   Redis metadata cache. The public request snapshot masked `api_key`, but the
   top-level stored configuration remained raw.
2. `LLMProviderConfig.base_url` was constrained only to a non-empty string. A
   job could therefore name an arbitrary endpoint without an explicit operator
   opt-in or endpoint allowlist.

The preceding cache-identity slice already includes the selected text and
vision model in the retrieval cache shape. This design addresses the storage,
job binding, endpoint admission, and lifecycle boundary without syncing
upstream or changing any existing qualification worktree.

## Goals

- Keep raw BYOK credentials out of Job JSON, Redis metadata, logs, and public
  request snapshots.
- Store the validated per-job configuration only as Fernet ciphertext in a
  dedicated job-scoped record, using the existing `WEBHOOK_MASTER_KEY`
  encryption service.
- Bind the credential record to both `jobs.job_id` and `user.id`; the worker
  must resolve it using the authoritative Job owner, requested worker owner
  when present, active status, and an unexpired timestamp.
- Default-deny BYOK outbound calls until the operator enables the LLM external
  call flag and provides an exact normalized HTTPS endpoint allowlist.
- Validate the endpoint policy both at API admission and again in the worker
  before request-scoped overrides are initialized.
- Revoke/delete credential material after terminal success or final failure,
  delete expired/stale material during the existing sweeper path, and retain
  it across retryable failures until terminal cleanup or expiry.
- Fail closed on legacy raw `llm_config` metadata rather than migrating or
  reusing credentials that may already have been exposed in metadata stores.

## Non-goals and explicit boundaries

- No live provider session, API secret, browser submission, or external HTTP
  call is performed by this change.
- No provider-specific authorization record is introduced; existing
  provider/job authorization work remains a separately gated boundary.
- Retrieval-request BYOK propagation is not persisted by this path and is not
  promoted by this change.
- This does not prove host-level no-egress, provider retention/deletion, native
  or semantic qualification, private-pilot readiness, or regulatory status.
- No upstream fetch, merge, rebase, sync, or promotion is performed.

## Data model

Add `job_llm_credentials` with:

| Field | Boundary |
|---|---|
| `id` | Opaque `jllm_...` identifier referenced by safe Job metadata |
| `job_id` | Unique foreign key to `jobs.job_id`, `CASCADE` on Job deletion |
| `user_id` | Foreign key to `user.id`, retained for owner binding |
| `config_encrypted` | Fernet ciphertext of canonical JSON; never raw JSON |
| `status` | `active`, `revoked`, or `expired` |
| `expires_at` | Bounded by the configured job waiting/processing lifetime |
| `last_used_at` | Worker resolution audit timestamp; no credential content |
| `created_at` / `revoked_at` | Lifecycle timestamps |

The API creates the credential object in the same SQLAlchemy unit of work as
the Job. Job metadata receives only `llm_credential_id` and
`llm_config_present`; `original_request` omits `llm_config` entirely.

## Endpoint policy

The shared policy helper canonicalizes endpoint URLs by trimming whitespace
and trailing slashes, lower-casing the hostname, and preserving the explicit
path/port. It rejects non-HTTPS URLs, credentials in the URL, query strings,
fragments, missing hosts, localhost, and literal loopback/private/link-local/
reserved IP addresses. Every effective text/vision provider endpoint must
match one of the operator's comma-separated exact allowlist entries. An empty
allowlist or disabled `LLM_EXTERNAL_CALLS_ENABLED` rejects BYOK admission.

The policy is deterministic and performs no DNS resolution or network probe;
runtime egress controls remain a separate gate.

## Runtime and failure behavior

### API admission

`DocumentIngestionService` extracts the typed request configuration, validates
the endpoint policy, creates an encrypted credential object, and returns it in
the resolved scope. `DocumentIngestionCreationService` stages it before the
existing JobRepository commit, preserving atomic Job/credential creation. A
failure before commit rolls back both objects; a post-commit upload/scheduling
failure leaves only bounded, expirable ciphertext for the existing sweeper.

### Worker resolution

`ParseJobContext` carries `llm_config` separately from JSON metadata. Context
loading resolves the encrypted record through a sync DB query joined to Job,
checks owner/status/expiry, decrypts and validates the config, and rechecks the
endpoint policy. It never reads a legacy raw config for execution. The parse
run initializes overrides from the separate context field only.

### Cleanup

Successful parse completion and final task failure revoke/delete the
job-scoped record. Retry callbacks do not clean it. The stale-job sweeper
cleans records for jobs it successfully expires and removes expired orphaned
records in the same bounded batch.

## Verification strategy

- TDD unit tests prove no raw config in metadata/snapshots, ciphertext does not
  contain the API key, owner binding, expiry/revocation, legacy fail-closed
  behavior, and endpoint rejection/allowlist matching.
- API contract tests use synthetic requests and fake sessions; no provider or
  database service is contacted.
- Worker tests use fake DB/session boundaries and prove the separate context
  field is used, cleanup occurs only at terminal boundaries, and retries retain
  the record.
- Migration/model checks inspect the new table contract. Focused Ruff,
  Pyright, compile, and adjacent ingestion tests run after implementation.

## Rollback

The work is isolated on `fix/kiwi-shane/byok-credential-reference-20260721`.
The existing candidate worktree and all previously pushed branches remain
untouched. If this slice is not promoted, no runtime branch is changed and the
new branch can be discarded later without rewriting any existing history.
