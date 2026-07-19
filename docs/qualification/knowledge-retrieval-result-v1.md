# knowledge-retrieval-result-v1 qualification matrix

Status: `deferred`

This record is the source-owner qualification boundary for the canonical
`knowledge-retrieval-result-v1` schema. It is a synthetic/public readiness
record only. It does not authorize retrieval of private data, add RA authority
to a producer result, or establish source sufficiency.

## Current boundary

The branch publishes the canonical schema, a content-free contract fixture,
and an opt-in pure serializer. The serializer requires explicit request,
memory-snapshot, source-version, retrieval-configuration, and native-locator
context; it does not infer extraction block IDs from database chunk IDs. The
existing native implementation still produces a portable
`codex-review-package/1.0` package and its derivative manifest; that package
is an observed baseline, not an automatically compatible
`knowledge-retrieval-result-v1` payload. The serializer is not wired into the
active retrieval routes and does not change the edge status.

## Acceptance matrix

| Qualification target | Current evidence | Disposition |
|---|---|---|
| Hierarchy, section path, and chunk boundaries | Existing package contract tests cover document-tree and block-normalization behavior. | `observed_mechanical_baseline` |
| Table/image linkage and citation export | Existing package/table/page contract tests cover derivative asset references; the opt-in serializer carries explicitly supplied table/image IDs and native citation text without deriving them from chunk IDs. | `partial_mechanical_only` |
| Source allowlist and namespace isolation | Existing worker/API contract suites cover namespace-scoped document and retrieval behavior. | `partial_mechanical_only` |
| Duplicate handling and source-version replacement | Existing lifecycle and ingestion tests cover related document identity/version behavior; no canonical result gold set is attached. | `partial_mechanical_only` |
| Stale invalidation and deletion/purge | Existing lifecycle tests cover invalidation/purge paths; end-to-end canonical result non-retrievability evidence is not recorded. | `not_yet_qualified` |
| Backup/restore | No source-owner qualification fixture in this slice. | `not_assessed` |
| External telemetry and LLM/VLM egress | Local/offline contract tests cover application flags and provider boundaries; host-level network denial is a separate operator control. | `partial_mechanical_only` |
| Result provenance and native locator | The opt-in serializer requires source/version, explicit block IDs, page range, native citation, and emits the fixed `unverified` native-source status; no active retrieval route or gold result set is wired. | `partial_mechanical_only` |
| RA acceptance fields in producer result | Canonical fixture has no `evidence_status`, `readiness_status`, or `regulatory_conclusion`. | `mechanical_pass` |
| Critical gold evidence in top-N and meaning preservation | No retrieval gold-question set or extractive-only drift run is recorded. | `not_assessed` |

The first qualified private profile must remain extractive-only unless a later
bounded decision demonstrates that summary/VLM enrichment does not change
critical meaning. A review-package pass or API retrieval pass alone does not
change this disposition.

## Canonical serializer implementation note

On 2026-07-18, `shared.services.retrieval.knowledge_retrieval_result` added an
opt-in serializer for one already-ranked retrieval row. Its context and
locator dataclasses require explicit producer-owned identity and native
provenance; invalid hashes, page ranges, missing block IDs, missing native
references, non-finite scores, and score-less rows fail closed. The serializer
preserves retrieval score components and adds a derivative-content warning
when the assembled row is a summary or other non-native representation. It
does not call a database, expose RA/readiness fields, or alter the existing
public retrieval routes. Focused contract tests cover the shape and the
fail-closed boundaries; qualification, source-owner gold results, and runtime
activation remain outstanding.

## Synthetic canonical cross-edge projection observation

On 2026-07-18, the two completed public MinerU canonical manifests from the
paired smoke run were loaded in memory by the opt-in serializer at producer
revision `1190d5753784827cb871774fe384de0930c98a05`. One first-page block from
each fixture produced a `knowledge-retrieval-result-v1` projection with 21
root fields, one explicit extraction block, `native_source_verification_status:
unverified`, and `not_source_sufficiency_decision: true`. The test.pdf table
record and image record were also projected separately with one explicit table
link and one explicit image link, respectively.

No database, active retrieval route, production memory snapshot, or result
file was used. The memory/configuration IDs and hashes were synthetic, and the
projection preserved the source-version and native block/page locator without
turning the extraction derivative into source evidence. This is a bounded
cross-edge mechanical observation only; no gold retrieval result, native-source
adjudication, source sufficiency decision, or runtime promotion is implied.

## Synthetic cross-edge observation

On 2026-07-18, the public MinerU fixture `test.pdf` was parsed locally and its
validated legacy artifact bundle was consumed by the Knowhere review-package
builder. The source SHA was
`ae9e3f14cc3bea88dd0ce4e2715b3b03561378501318df61f0889df207aed25b`; the
resulting package inventory contained 22 hashed files, 5 blocks, 1 table, 1
page, and 2 extraction findings, with no temporary build directory left
behind. Application offline mode was requested, while host-level network
denial remained unverified.

This is bounded WP-05 edge characterization only. The output carried the
legacy `knowhere-mineru-artifacts/1.0` MinerU manifest inside a derivative
review package; it did not emit a canonical `knowledge-retrieval-result-v1`
payload, retrieval gold result, or RA acceptance disposition. The
qualification status therefore remains `deferred` and the runtime edge
remains `declared_not_runtime`.

## Canonical field-boundary audit

The same two public MinerU manifests were loaded in memory by the opt-in
serializer for a field-boundary audit. Each projection had 21 root fields and
one explicit extraction block; the test.pdf projection carried one explicit
table link and one explicit image link. No RA authority field or
`source_sufficiency_decision` field was emitted, while
`native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. This is a content-free
mechanical audit with no database, active route, or runtime activation; the
qualification status remains `deferred`.

## Synthetic fail-closed serializer smoke observation

On 2026-07-18, the five existing canonical serializer contract tests passed
with synthetic rows and contexts. They cover missing explicit native locators,
refusal to derive extraction block IDs from `chunk_id`, invalid snapshot
hashes, reversed native page ranges, and non-finite retrieval scores. The
serializer therefore rejects these unsafe inputs without database access,
route activation, or an RA disposition. This is mechanical boundary evidence
only; source-owner qualification, gold retrieval results, and runtime
activation remain outstanding.
