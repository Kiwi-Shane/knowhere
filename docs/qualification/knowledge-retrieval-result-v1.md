# `knowledge-retrieval-result-v1` D4 qualification boundary

## Status

`qualified_bounded`; native-source verification, RA acceptance, private
runtime, and release remain deferred.

This record is source-owner technical evidence for the Knowhere retrieval
boundary. It does not make a source-sufficiency or regulatory decision.

## Scope

D4 covers the canonical result serializer and the fail-closed controls for:

- source and source-version traceability;
- explicit MinerU extraction-block linkage;
- request-scoped source allowlisting;
- two-case isolation;
- native citation rooted in the accepted source version;
- stale memory-snapshot and explicit invalidation rejection;
- user-scoped document hard deletion and retrieval-cache invalidation;
- bounded synthetic backup/restore;
- synthetic default-deny external destinations;
- disabled telemetry in the synthetic control plane.

The serializer is opt-in and is not wired into the existing public retrieval
route. It requires caller-supplied source/version and native-locator context;
it never derives a native block ID from `chunk_id`.

## Verification

Run from the Knowhere repository root:

```text
uv run python scripts/run_d4_qualification.py
```

The runner binds the synthetic result context to the current Git `HEAD` and
returns `technical_completion=qualified` only when every control passes. The
fault-injection path must fail closed:

```text
uv run python scripts/run_d4_qualification.py --fault cross_case_isolation
```

The focused source-owner suite covers serializer boundaries, allowlist and
locator validation, stale/invalidation rejection, the two-case synthetic
control plane, and fail-closed aggregation. API contract tests cover active
ingestion refusal, storage-prefix safety, terminal hard deletion, peer
preservation, and read-only dashboard permission denial.

## State boundary

```yaml
technical_completion: qualified
ra_evidence_state: deferred
release_decision: defer
private_data: false
provider_execution: false
native_source_verification: false
aiwb_direct_query: false
```

This D4 evidence does not qualify MinerU extraction fidelity, remote/vector/
memory-provider deletion, production backup retention, host firewall policy,
private-data processing, provider execution, D5-D7 runtime edges, E-E, or D9.
