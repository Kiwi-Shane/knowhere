# Knowhere D4 Qualification Packet

Date: 2026-07-23  
Status: `qualified_bounded`  
Repository: `Kiwi-Shane/knowhere-private`  
Qualification revision: `68aa931363656424a3a37f34b7db95d67245bad9`

## Decision

The bounded D4 Knowhere qualification is technically qualified for the
synthetic, offline control plane. The result is not a production runtime
release, does not establish RA evidence acceptance, and does not authorize
private-data processing.

The runner bound its result to the exact qualification revision and passed all
13 controls for `CASE-SYN-A` and `CASE-SYN-B`:

- contract edge;
- source/version traceability;
- extraction-block linkage;
- source allowlist;
- cross-case isolation;
- citation;
- stale invalidation;
- scoped deletion;
- backup/restore;
- default-deny egress;
- disabled telemetry;
- private-data boundary; and
- deferred RA evidence state.

## Contract identity

The canonical `knowledge-retrieval-result-v1` contract remains owned by
Knowhere. The D1 frozen publication evidence is retained:

- schema: `schemas/knowledge-retrieval-result-v1.schema.json`
- fixture: `examples/contracts/knowledge-retrieval-result-v1/example.json`
- D1 schema SHA-256:
  `54307e0c42ebf737af897b691badda18fd6c673f64aef3cf7eb961dab0123c4a`
- D1 fixture SHA-256:
  `14994fd3527301fd1da03c5ed9b867dcd145c3578b333f3bdc27e13dc1ea236c`
- D1 publication revision:
  `b9cd8004933690c2c33eb8c01a91874337a3b945`

The D4 worktree resolves the schema and fixture to the same Git blobs:
`182f3197c8c629d055546ef74c5a4219b19600b2` and
`c1759a2ee18d88b9b05ac7be49c622575ac58df6`, respectively. Its raw Windows
checkout SHA-256 values differ because of line-ending normalization; the
normalized fixture is equal and no contract content was changed.

## Evidence and verification

Primary runner:

```text
uv run python scripts/run_d4_qualification.py
```

Result: `technical_completion=qualified`, 13 controls passed, 0 controls
failed, `ra_evidence_state=deferred`, and `release_decision=defer`.

The focused D4 suite passed 9 tests. The related API hard-delete, dashboard
permission, telemetry, documents, retrieval, and worker contract suites also
passed in the local qualification environment. Fault injection of
`cross_case_isolation` produced the expected nonzero failure, confirming the
fail-closed control path.

## Boundary and deletion controls

The qualification covers synthetic case-scoped deletion across document
metadata, sections, chunks, graph data, retrieval hit statistics, job/result
records, upload objects, raw result objects, result ZIPs, retrieval markers,
and bounded backup state. Active ingestion is refused rather than silently
deleted. Cross-case identifiers remain isolated.

The serializer is opt-in and requires an explicit native locator. It emits
source-owned retrieval data only; it does not make a source-sufficiency,
native-verification, regulatory, or release decision. Knowhere does not become
an RA evidence authority through this qualification.

## Explicitly deferred

The following remain closed:

- private source or private corpus processing;
- provider, LLM, or VLM execution;
- upstream synchronization;
- native MinerU semantic-gold qualification;
- native-source verification and RA acceptance;
- production remote/vector/memory-provider deletion;
- production backup retention/recovery and host firewall enforcement;
- D5-D7 runtime edges;
- D8 private shadow pilot; and
- D9 active runtime release.

GitHub Actions billing/spending-limit failures are recorded as remote CI not
verified and are not used as the D4 release gate. Local contract and static
verification remain the evidence for this bounded engineering qualification.

## Handoff

This packet is ready for RA to synchronize the bounded D4 consumer descriptor
and evidence state. The RA release gate remains closed until the deferred
native-source, runtime-edge, private-pilot, and release controls are separately
qualified.
