# knowledge-retrieval-result-v1 qualification matrix

Status: `deferred`

This record is the source-owner qualification boundary for the canonical
`knowledge-retrieval-result-v1` schema. It is a synthetic/public readiness
record only. It does not authorize retrieval of private data, add RA authority
to a producer result, or establish source sufficiency.

## Current boundary

The branch publishes the canonical schema and a content-free contract fixture.
The existing native implementation currently produces a portable
`codex-review-package/1.0` package and its derivative manifest; that package
is an observed baseline, not a canonical `knowledge-retrieval-result-v1`
payload. No compatibility claim is made between those shapes without an
explicit producer serializer and qualification run.

## Acceptance matrix

| Qualification target | Current evidence | Disposition |
|---|---|---|
| Hierarchy, section path, and chunk boundaries | Existing package contract tests cover document-tree and block-normalization behavior. | `observed_mechanical_baseline` |
| Table/image linkage and citation export | Existing package/table/page contract tests cover derivative asset references; canonical retrieval-result citation mapping is not implemented. | `partial_mechanical_only` |
| Source allowlist and namespace isolation | Existing worker/API contract suites cover namespace-scoped document and retrieval behavior. | `partial_mechanical_only` |
| Duplicate handling and source-version replacement | Existing lifecycle and ingestion tests cover related document identity/version behavior; no canonical result gold set is attached. | `partial_mechanical_only` |
| Stale invalidation and deletion/purge | Existing lifecycle tests cover invalidation/purge paths; end-to-end canonical result non-retrievability evidence is not recorded. | `not_yet_qualified` |
| Backup/restore | No source-owner qualification fixture in this slice. | `not_assessed` |
| External telemetry and LLM/VLM egress | Local/offline contract tests cover application flags and provider boundaries; host-level network denial is a separate operator control. | `partial_mechanical_only` |
| Result provenance and native locator | The canonical schema requires source/version, block IDs, page range, citation, and an `unverified` native-source status; no runtime serializer emits it yet. | `not_yet_qualified` |
| RA acceptance fields in producer result | Canonical fixture has no `evidence_status`, `readiness_status`, or `regulatory_conclusion`. | `mechanical_pass` |
| Critical gold evidence in top-N and meaning preservation | No retrieval gold-question set or extractive-only drift run is recorded. | `not_assessed` |

The first qualified private profile must remain extractive-only unless a later
bounded decision demonstrates that summary/VLM enrichment does not change
critical meaning. A review-package pass or API retrieval pass alone does not
change this disposition.
