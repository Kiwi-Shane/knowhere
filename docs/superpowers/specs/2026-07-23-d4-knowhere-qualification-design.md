# Knowhere D4 retrieval qualification

## Objective

Qualify the source-owned Knowhere retrieval boundary against the live `main`
baseline after D1 contract publication. The gate must prove deterministic
traceability and lifecycle controls without treating a retrieval result as
native-source verification, RA acceptance, or release evidence.

## Scope

The D4 slice covers:

- an opt-in serializer for `knowledge-retrieval-result-v1` that requires an
  explicit native locator and never derives extraction blocks from a database
  chunk identifier;
- fail-closed result qualification for contract identity, source allowlisting,
  source/version matching, extraction-block linkage, citation, stale snapshots,
  invalidation, and forbidden RA-owned fields;
- user-scoped document hard deletion of database, graph, retrieval-cache, queue,
  upload, result-ZIP, and raw-result state, with an active-ingestion refusal;
- a synthetic two-case qualification harness for isolation, deletion,
  backup/restore, default-deny external destinations, disabled telemetry, and
  the separate technical/RA/release state boundary;
- contract and API tests that use generated identifiers and local synthetic
  storage only.

## Non-goals

- no private source or private corpus;
- no provider, LLM, VLM, or corpus credential execution;
- no upstream synchronization;
- no direct AIWB-to-Knowhere query or credential export;
- no native-source verification, source sufficiency, regulatory conclusion,
  owner acceptance, or runtime release decision;
- no claim that a local synthetic stack proves host-level firewall policy.

## Ownership boundary

Knowhere owns retrieval-result serialization and the technical qualification
checks. RA owns source registration, native-source verification, retrieval
acceptance, evidence state, and release. The canonical JSON schema remains the
D1 source-owned contract; this change adds interpretation and lifecycle tests,
not a second result schema.

## Fail-closed rules

1. A result without an explicit native locator is rejected.
2. A source not in the request allowlist is rejected.
3. A mismatched request, source version, extraction block, memory snapshot, or
   invalidation state is rejected as stale or mislinked.
4. Any RA-owned authority field in a producer result is rejected.
5. Any active ingestion job blocks hard deletion.
6. Hard deletion refuses an upload key outside the job-owned upload prefix.
7. Any failed synthetic control changes the aggregate qualification to
   `mechanical_fail`; no warning-only promotion is permitted.

## Evidence state

The D4 report may conclude `technical_completion: qualified` for the bounded
Knowhere controls only. It must keep `ra_evidence_state: deferred` and
`release_decision: defer`, and must record that no private data or provider was
used.
