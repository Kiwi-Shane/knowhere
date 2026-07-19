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

## Bounded public-manifest cross-edge observation

On 2026-07-19, one newly generated public MinerU canonical manifest for
`demo/pdfs/demo2.pdf` was loaded in memory by the opt-in serializer. The
producer was MinerU `3.4.4` at revision
`6450b02c2d1c2fb0ef2c9369037bbe3c6663d052`; the Knowhere serializer was
observed at revision `a25a9729da84c213dd45ebcea3ddeb37532b49a1`. Three
explicit projections were produced from producer-owned page-block locators,
including the available table/image links.

All three projections had 21 root fields and passed the
`knowledge-retrieval-result-v1` schema with zero errors. No RA authority field
was emitted; `native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. The observation used no
database, memory snapshot service, active retrieval route, or runtime
activation. It is a mechanical cross-edge check only, and the qualification
status remains `deferred` pending source-owner gold retrieval results, native
adjudication, stale/deletion evidence, and the other acceptance targets above.

## Native and OCR public-manifest projection observation

On 2026-07-19, the current public native-text and OCR canonical manifests
from the paired MinerU runs were loaded in memory by the opt-in serializer.
The MinerU implementation revision was
`6450b02c2d1c2fb0ef2c9369037bbe3c6663d052`; the Knowhere checkout was observed
at `2189341293c4bd0bd26d6dd06022d481c5ef9e68`. One explicit page-block
projection was produced for each manifest using producer-owned block IDs and
page locators; the native-text projection also carried one explicit image
link.

Both projections had 21 root fields and passed the
`knowledge-retrieval-result-v1` schema with zero errors. No RA authority field
was emitted; `native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. The observation used no
database, memory snapshot service, active retrieval route, or runtime
activation. It expands native/OCR mechanical cross-edge coverage only; gold
retrieval results, semantic meaning preservation, native adjudication,
stale/deletion evidence, and qualification remain deferred.

## Synthetic DOCX structure projection observation

On 2026-07-19, the existing synthetic DOCX fixture generated by
`apps/worker/tests/fixtures/codex_export/generate_docx_fixture.py` was loaded
from its completed MinerU canonical manifest in memory. MinerU was observed at
implementation revision `6450b02c2d1c2fb0ef2c9369037bbe3c6663d052`; the
Knowhere checkout was `092a908c827e9f391b384d885dd2bb7e1b763b48`. One explicit
table projection and one explicit image projection were produced from
producer-owned block IDs, table IDs, image IDs, and page locators.

Both projections had 21 root fields and passed the
`knowledge-retrieval-result-v1` schema with zero errors. No RA authority field
was emitted; `native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. The source manifest's
parser-derived logical page locator was preserved without implying physical
DOCX pagination. The observation used no database, memory snapshot service,
active retrieval route, or runtime activation; gold retrieval, semantic
meaning preservation, and qualification remain deferred.

## Producer sentinel boundary

The paired MinerU DOCX run included a producer-side synthetic sentinel smoke
with 20/20 predefined category checks matched. Knowhere did not treat those
checks as retrieval gold: no top-N question set, database result, active route,
memory snapshot service, or semantic adjudication was used. The observation
therefore provides no retrieval meaning-preservation or source-owner
qualification evidence; the canonical retrieval-result disposition remains
`deferred`.

## MinerU manifest consumption boundary

The 2026-07-19 active-path source audit compared the source-owned MinerU
`document-extraction-manifest-v1` schema with the current worker boundary.
The active `parse_task` path returns `ParseOutput`, converts its parsed
dataframe through `dataframe_to_chunks`, and publishes Knowhere document
rows/chunks through the existing lifecycle services. The active path has no
consumer reference for `document-extraction-manifest-v1`,
`extraction_run_id`, `source_version_id`, or a canonical manifest hash.

Knowhere's local-provider seam does validate a separate
`knowhere-mineru-artifacts/1.0` `mineru_manifest.json` containing source
filename/size/SHA-256 and local artifact hashes. The result ZIP also emits a
Knowhere application `manifest.json`. These are useful artifact-integrity and
result-package records, but they are not the source-owned canonical
`document-extraction-manifest-v1` and are not evidence of canonical manifest
consumption by the active worker path. The legacy `codex-review-package/1.0`
export path is likewise outside this active worker-to-retrieval edge.

Accordingly, the current evidence closes local MinerU extraction followed by
non-semantic worker publication and active lexical-route consumption only.
WP-05 canonical manifest consumption, source/version/extraction-run lineage,
idempotency, and recovery evidence remain unqualified; D5 is not promoted and
no implementation change is authorized by this observation. The disposition
remains `deferred`.

## Chinese-only DOCX projection observation

On 2026-07-19, the completed MinerU manifest for the existing
`apps/worker/tests/fixtures/sample_chinese_600chars.docx` fixture was loaded
in memory by the opt-in serializer. MinerU was observed at image-contained
revision `6450b02c2d1c2fb0ef2c9369037bbe3c6663d052`; the Knowhere checkout was
observed at `8ab1acae17106c363ac9f2495ada1b2642af1f69`. One explicit
producer-owned page-block projection was produced.

The projection had 21 root fields and passed the
`knowledge-retrieval-result-v1` schema. No RA authority field was emitted;
`native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. No database, memory snapshot
service, active retrieval route, top-N question set, or runtime activation was
used.

This is Chinese-only mechanical cross-edge coverage. The fixture is not a
Traditional-Chinese-plus-English bilingual gold set, and the projection does
not establish retrieval meaning preservation, native adjudication, source
sufficiency, or qualification; the disposition remains `deferred`.

## Synthetic PDF page-structure projection observation

On 2026-07-19, the completed MinerU manifest for the existing
`apps/worker/tests/fixtures/sample_3pages.pdf` corpus fixture was loaded in
memory by the opt-in serializer. MinerU was observed at image-contained
revision `6450b02c2d1c2fb0ef2c9369037bbe3c6663d052`; the Knowhere checkout was
observed at `07f5afad068deee8df7c258e4240f3f185447098`. Three explicit
producer-owned page-block projections were produced.

All three projections had 21 root fields and passed the
`knowledge-retrieval-result-v1` schema. No RA authority field was emitted;
`native_source_verification_status` remained `unverified` and
`not_source_sufficiency_decision` remained true. No database, memory snapshot
service, active retrieval route, top-N question set, or runtime activation was
used. The producer manifest contained no table or image record for this run,
so no such links were asserted.

This is page-structure mechanical cross-edge coverage only. It does not
establish table/image fidelity, retrieval meaning preservation, native
adjudication, source sufficiency, or qualification; the disposition remains
`deferred`.

## Native-source concordance handoff boundary

On 2026-07-19, the paired MinerU native DOCX observation used source-side
metadata and token extraction from the existing synthetic generator fixture.
The run was `EXT-WP03-20260719-DOCX-NATIVE-GOLD-RUN1` with input SHA-256
`70f9dabe1368d59714a678c928dfab60defb2a91a0d7b4b49b0e17f3715aed03`. MinerU
reported a completed canonical manifest with 1 parser-derived logical page,
12 page blocks, 2 tables, 1 image, 5 outputs, 0 errors, and no fallback. A
source-derived comparison found all 55 normalized source tokens and all
source table-cell tokens in the derivative outputs; this included preserving
`sub`/`sup` contents while treating other markup as field boundaries.

Knowhere treats this as producer-side mechanical handoff evidence only. No
database, memory snapshot, active retrieval route, top-N question set, or
semantic adjudication was used in this slice, and no retrieval-result
projection or qualification status was inferred from the concordance. Native
verification remains `unverified`, `not_source_sufficiency_decision` remains
true, and the retrieval qualification disposition remains `deferred`.

## Candidate gold-question and retrieval boundary preflight

On 2026-07-19, a separate MinerU preparation run used the existing synthetic
DOCX generator and produced a completed canonical manifest with run identity
`EXT-WP03-20260719-DOCX-GOLD-PREP-RUN1` and input SHA-256
`83c43e25c9e1359b2a9be605fd6ecf1308470531c0619ab589c59c49c1cb446e`. The
preparation packet contained 7 bounded source-derived question categories and
explicit `content_list_v2` artifact locators. All 7/7 categories passed the
mechanical source/derivative preflight, including the 55-token source set and
6/6 table/image structure checks.

This did not create a retrieval result. No Knowhere database, memory snapshot,
active route, ranking/top-N question set, or serializer projection was used;
the packet remains `pending_human_adjudication`, and the top-N status remains
`not_run_active_route_disabled`. No native verification or source-sufficiency
decision was inferred; retrieval qualification remains `deferred`.

## Required fixture-family handoff boundary

On 2026-07-19, a temporary local synthetic/public fixture batch supplied 10
completed MinerU manifests for the remaining input families: Traditional
Chinese plus English DOCX, multi-column/header-footer PDF, footnote PDF,
cross-page table PDF, rotated-page PDF, a 12-page long PDF, two same-basename
files with different SHA-256 values, and superseded v1/v2 files. Every valid
manifest had zero errors and no fallback. The corrupt and encrypted inputs
both failed closed with exit code 2 and no canonical manifest.

Knowhere did not load these results into a database or active memory snapshot,
did not invoke an active retrieval route, and did not create top-N result
objects. The cross-page-table producer output had no table record, and the
producer manifest did not by itself prove footnote, multi-column, or rotated
meaning preservation. Duplicate and superseded SHA evidence is an inventory
boundary only; no replacement, stale, deletion, or retrieval-lifecycle
behavior was tested. Native verification, gold retrieval results, semantic
meaning preservation, and qualification remain deferred.

## Candidate top-N preflight and retrieval contract observation

On 2026-07-19, the existing public cross-edge review package
`cross-edge-native-text-20260718-run3` was used for a memory-only candidate
ranking preflight. The source document identity was
`doc_ae9e3f14cc3bea88` with source SHA-256
`ae9e3f14cc3bea88dd0ce4e2715b3b03561378501318df61f0889df207aed25b`; the
five producer-owned extraction blocks were addressed by explicit locators.
The memory snapshot was `MEM-CODEX-CROSS-EDGE-NATIVE-TEXT-RUN3` with block
snapshot SHA-256
`22b908ed9c3189d075a7343153cbb4840cb2bd30eaa8b53acf71f52970d46b46`.

Four bounded fixture questions covering image/caption, formula, paragraph,
and table locators were ranked with the existing `content_bm25` path at
`top_k=3`. All 4/4 expected producer block IDs appeared in the candidate
top-three. The image/caption expected block ranked second because another
derivative block shared caption/number tokens; the other three expected
blocks ranked first. Each candidate was passed through the opt-in
`knowledge-retrieval-result-v1` serializer with explicit source-version and
native-locator context. The serialized boundary retained
`native_source_verification_status: unverified` and
`not_source_sufficiency_decision: true`. Knowhere was observed at revision
`0026c9895b6f3f97268b01a6233cbeb326022a05`, and the retrieval configuration
SHA-256 was
`bf7afab3816cc98ae3c418cf98b70b00eed6b18e09e38f29e0a47cbe0271276f`.

This was a candidate preflight only: it used no Knowhere API, worker,
database, vectors, memory service, or active route. The expected mapping is
fixture preparation, not human/native gold adjudication. It does not establish
semantic meaning preservation, source sufficiency, stale-version behavior,
deletion-negative retrieval, cross-case isolation, or qualification.

The same Knowhere revision then passed the existing DB-backed API contract
surfaces using a private local PostgreSQL 17.10 test process: the retrieval
contract suite passed 15/15 tests, and the documents contract suite passed
17/17 tests. These tests mechanically cover authenticated namespace scoping,
active-document selection, document and section exclusion, reference
hydration boundaries, current chunk listing, and archived/missing page-citation
negative paths. The retrieval run emitted 12 existing deprecation warnings;
no test failure was observed.

The qualification disposition remains `deferred`. The contract results expand
mechanical route and storage-boundary evidence but do not promote the opt-in
serializer, activate a runtime edge, or close the native/human semantic-gold,
meaning-preservation, stale/deletion, or source-owner qualification gates.

## Native page-render and derivative visual concordance boundary

On 2026-07-19, a local rendered page for the public package
`cross-edge-native-text-20260718-run3` was visually compared with its
producer-owned structured blocks and derivative assets. The visible page
contained a figure/caption, displayed equation, paragraph, rotated complex
table/caption, and page number. The existing five-block package mapped those
regions to explicit image, interline-equation, paragraph, table, and
page-number locators, and the figure/equation assets matched their page
regions.

The table image retained the visible rotated presentation and the HTML
derivative retained the four data rows and three columns. The accompanying
metadata marked the CSV representation `lossy_complex` and recorded
rowspan/colspan warnings, so the CSV was not treated as a lossless semantic
table result. This is an AI-assisted visual/mechanical observation only; it is
not native-source adjudication, retrieval gold, meaning-preservation proof,
source sufficiency, stale/deletion evidence, or qualification. The
qualification disposition remains `deferred`.

## DB-backed revision and archive negative-path observation

On 2026-07-19, a one-off contract probe used the existing local PostgreSQL
17.10 test runtime and the existing API routes to retain two job-result
revisions under one document ID, switch `documents.current_job_result_id` to
the newer revision, and query the active retrieval route. The old revision's
chunk remained physically retained for inspection, but it did not appear in
the current retrieval scope; returned rows were from the current revision
only. The probe also exercised the canonical archive route and observed zero
results for the current marker after the document became archived.

The route's small-corpus optimization returns the current in-scope row even
when an unmatched marker is queried, so the probe intentionally asserted
absence of the old revision rather than treating an unmatched-query empty
result as proven. This is DB-backed current-revision/archive route evidence
only. It does not prove hard deletion, vector/memory-snapshot deletion,
canonical result lifecycle semantics, source-version identity completeness,
cross-case isolation, or qualification; the disposition remains `deferred`.

## Current-head contract recheck

On 2026-07-19, the same Knowhere revision
`b1db01a802cfbffcb7ccbadb4e14e47e3489a6e6` was rechecked with the worktree's
`.venv` and the explicit PostgreSQL 17.10 `pg_ctl` test executable. The
archive-focused selection passed 3/3 tests; the complete documents contract
suite passed 17/17; and the complete retrieval contract suite passed 15/15
with 12 existing deprecation warnings and no test failures. This revalidates
the current-head mechanical API/archive/retrieval contract boundary only. It
does not prove hard deletion, object-storage/vector/memory deletion, native
or human semantic gold, source sufficiency, or qualification; the
disposition remains `deferred`.

## Active localhost API startup observation

On 2026-07-19, the current Knowhere revision was started through the existing
`uvicorn main:app` entry point on `127.0.0.1:5505` using the worktree `.venv`,
a newly created synthetic PostgreSQL database, filesystem object storage, no
provider keys, and `TELEMETRY_ENABLED=false`. Database migrations completed;
`GET /health` returned HTTP 200 with the expected healthy service payload; and
`GET /openapi.json` returned HTTP 200 with 42 routes. The API process was
stopped after the probe and the dedicated synthetic database was dropped.
This is active API startup/health/OpenAPI evidence only. It does not establish
worker startup, ingestion, active retrieval against producer artifacts,
host-level egress denial, telemetry exhaustiveness, deletion behavior, source
sufficiency, or qualification; the disposition remains `deferred`.

## Active localhost retrieval observation

On 2026-07-19, the current Knowhere revision
`b1db01a802cfbffcb7ccbadb4e14e47e3489a6e6` was started again through the
existing `uvicorn main:app` entry point on `127.0.0.1:5505`, with
`TELEMETRY_ENABLED=false`, no provider keys, filesystem object storage, and
an isolated synthetic PostgreSQL database. After migrations completed, a
synthetic authenticated user, current document/job-result revision, section,
and text chunk were inserted directly into that isolated database. The actual
`POST /api/v1/retrieval/query` route then returned HTTP 200 with
`router_used=small_corpus_all`, one result, non-empty `evidence_text`
containing the seeded marker, and an empty `answer_text`. The result carried
the expected document, section, and chunk identifiers; the response's
`referenced_chunks` list was empty and is not treated as positive citation
evidence.

The API process was stopped, the dedicated database was dropped, and port
`5505` was verified free. This is active API retrieval evidence against
directly seeded synthetic rows only. It does not establish worker startup,
MinerU producer ingestion, retrieval against producer-owned artifacts, native
or human semantic gold, source sufficiency, deletion behavior, host-level
egress denial, telemetry exhaustiveness, or qualification; the disposition
remains `deferred`.

## Active localhost worker startup observation

On 2026-07-19, the current Knowhere worker implementation baseline
`b1db01a802cfbffcb7ccbadb4e14e47e3489a6e6` was started through the existing
`worker.py` entry point with the lockfile-resolved project-local Python 3.11
runtime, a dedicated synthetic PostgreSQL database, Redis database 14,
filesystem storage, `MINERU_PROVIDER=cloud`, no provider keys, and
`TELEMETRY_ENABLED=false`. No task was enqueued. The worker wrote a fresh
heartbeat with PID `23224`; the observed worker/beat process tree remained
present, and Redis database 14 contained the expected six Celery/RedBeat
startup keys.

The pre-existing Knowhere `.venv` uses Python 3.13; a bounded comparison
probe failed before readiness because Celery 5.4's beat path calls the removed
Python 3.13 `logging._acquireLock` API. This is recorded as an environment
compatibility boundary, not a source-code qualification result. The
Python 3.11 probe was the selected startup observation for this slice. The
worker and beat processes were stopped, the heartbeat was removed, Redis
database 14 was flushed, and the dedicated PostgreSQL database was dropped.

This establishes worker/beat startup and heartbeat mechanics only. It does
not establish task execution, MinerU parsing, producer-artifact ingestion,
active result publication, source-owner gold, native or human semantic
adjudication, source sufficiency, deletion, egress, telemetry exhaustiveness,
or qualification; the disposition remains `deferred`.

## Checked-in worker publication contract observation

On 2026-07-19, the existing contract
`apps/worker/tests/contract/test_parse_task_contract.py::test_parse_task_should_process_uploaded_file_through_real_contract_boundaries`
passed `1 passed in 20.57s` with the project-local Python 3.11 runtime and
the locked worker dev/test environment. The contract used the existing
synthetic XLSX fixture and exercised source upload, Celery eager task
dispatch, job completion, result-ZIP publication, job/document chunk
creation, document sections, and Redis task status/progress assertions. The
pytest PostgreSQL process and contract storage were cleaned up.

This adds mechanical worker publication evidence for a non-PDF parser path.
It does not establish local MinerU PDF execution through the full task,
producer-artifact ingestion, native or human semantic gold, retrieval
top-N/source sufficiency, deletion, or qualification; the disposition
remains `deferred`.

## Active localhost worker daemon non-PDF publication observation

On 2026-07-19, the existing `worker.py` daemon was started with
`CELERY_TASK_ALWAYS_EAGER=false`, the project-local Python 3.11 worker
runtime, a dedicated synthetic PostgreSQL database, Redis database 14,
filesystem object storage, `MINERU_PROVIDER=cloud` with no provider keys,
and `TELEMETRY_ENABLED=false`. The existing synthetic XLSX fixture was
uploaded with source key
`uploads/job_worker_daemon_01_a1496a857807.xlsx` (6,438 bytes; SHA-256
`791055b0b09b95f8ca52e60940abb13d75f27fd90a99d2e327d79bef10d7cd0d`). The
task was enqueued on `document_ingestion_low` with Celery task ID
`6beec9fb-fdd6-4041-9bb6-4369ea181d07`; the live daemon, rather than eager
dispatch, consumed it. The worker heartbeat identified PID `24852`, and
the worker log recorded successful `parse_task` completion.

The isolated job finished with status `done`, no error code or message,
`page_count=2`, and `credits_charged=0`. The result row recorded document
ID `doc_2b9136bbc5dd`, job-result ID `679ff223-89b6-47e5-9f5e-0a5bc96f2c3b`,
result key `results/job_worker_daemon_01_a1496a857807.zip`, result size
1,901 bytes, and checksum
`5bbc2ee42a530c27368a87827dc3b6cfa410322f69598587eb98e559e8928eab`.
The filesystem result object had the same size and SHA-256; one document
section and one published table chunk were present. Redis recorded task
status `done` with progress `100`, `storage_completed=True`,
`delivery_mode=url`, and `stored_count=0`.

The daemon emitted Windows `cp950` `UnicodeEncodeError` warnings while
writing emoji-bearing log messages to its console sink, but the task
completed and its result/publication records were committed. This is an
observed logging-environment warning, not a task-success or result-integrity
failure. The exact worker/beat process tree was stopped after capture; the
heartbeat and temporary root were removed, Redis DB14 returned to zero keys,
and the dedicated database was dropped.

This closes only live daemon queue consumption and non-PDF result
publication for the existing synthetic XLSX contract path. It does not
establish local MinerU PDF execution through the worker task, producer-owned
artifact ingestion, retrieval top-N/source sufficiency, native or human
semantic gold, vector publication, telemetry exhaustiveness, deletion,
egress, or qualification; the disposition remains `deferred`.

## Active localhost worker-produced retrieval route observation

On 2026-07-19, the live daemon publication path was connected to the actual
API retrieval route using a second isolated synthetic run. The daemon used
`CELERY_TASK_ALWAYS_EAGER=false`, the project-local Python 3.11 runtime,
isolated PostgreSQL, Redis database 15, filesystem object storage, no provider
keys, and `TELEMETRY_ENABLED=false`. It consumed Celery task
`04a087f4-721c-4c6b-b9f6-9a160950d37c` from `document_ingestion_low` and
completed job `job_worker_retrieval_83b6463d32f0` with status `done` and
`page_count=2`. The result row recorded document ID `doc_2db4ccdfcc8c`, one
document section, one table chunk
(`2616669a-1a1f-566b-a037-3edcc8753bc4`), result key
`results/job_worker_retrieval_83b6463d32f0.zip`, result size 1,902 bytes, and
checksum
`1966e5f5fe9f14b2eb5e9e4a4fa88e7ba3019e8220a9e4709cc2a509332cdb5e`.

Using a dedicated synthetic API key for the same worker user, the active API
`POST /api/v1/retrieval/query` route returned HTTP 200 for namespace
`worker-contract`. The response used `router_used=small_corpus_all`, returned
one result with `chunk_type=table`, score `1.0`, the same chunk and document
IDs as the worker publication, and the expected synthetic source file and
section path. `evidence_text` was non-empty (123 characters),
`answer_text` was empty, and `referenced_chunks` was empty; the route was
therefore not treated as citation or answer-generation evidence. The worker
log again showed a Windows `cp950` emoji `UnicodeEncodeError` warning while
the task completed successfully.

This establishes a mechanical worker-produced-document-to-active-retrieval
route link for a non-PDF synthetic XLSX path. It does not establish MinerU
PDF execution through the worker, ranked top-N behavior (the one-chunk route
used the small-corpus path), citation projection, vector publication,
producer-owned artifact ingestion, native or human semantic gold, source
sufficiency, telemetry, deletion, egress, or qualification. The API and
worker/beat processes, port 5005, Redis DB15, isolated database, and temporary
root were cleaned up and verified; the disposition remains `deferred`.

## Active localhost local MinerU artifact seam observation

On 2026-07-19, the existing public/synthetic fixture
`apps/worker/tests/fixtures/sample_3pages.pdf` (736 bytes; SHA-256
`B1DD4D86D2B7C6505E35D972D0074EC08A7431013DD95E926BA92C7FBF165B1D`) was
passed through the current local MinerU provider path with the project-local
Python 3.11 worker runtime, `uv 0.11.29`, MinerU checkout revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`, and offline flags. No cloud
provider key was supplied. The direct `parse_pdf` seam returned exit code
0 and produced `full.md`, an images directory, and a sanitized
`logs/mineru.log` file of 7,031 bytes; `full.md` was 0 bytes.

The observation proves only that the local process/output seam can return
success and create the expected output locations. Because the extracted
Markdown was empty, it provides no content, native concordance, or semantic
meaning evidence. No worker task, producer-artifact ingestion, Knowhere
publication, retrieval top-N result, source-owner gold, source sufficiency,
or qualification gate was exercised. The temporary output and process were
cleaned up; the disposition remains `deferred`.

## Active localhost local MinerU non-empty artifact and native concordance observation

On 2026-07-19, the MinerU checkout's existing public fixture
`tests/unittest/pdfs/test.pdf` (one page, 125,121 bytes; SHA-256
`AE9E3F14CC3BEA88DD0CE4E2715B3B03561378501318DF61F0889DF207AED25B`) was
passed through the standard local provider `parse_pdf` seam with the
project-local Python 3.11 worker runtime, `uv 0.11.29`, MinerU revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`, pipeline backend, and offline
flags. No cloud provider key was supplied. The seam returned exit code 0 and
created a non-empty `full.md` of 1,098 bytes (SHA-256
`773b6533ff1536ebef0fc5788c43fa67527033f6d09cb3c86a60b5b9e14d0c8d`), three
image assets, and a sanitized `logs/mineru.log` of 5,931 bytes.

A bounded native-text comparison using Poppler 25.07.0 found 49 of 52 native
unique tokens in the Markdown (94.23% mechanical unique-token coverage).
Controlled markers for the figure caption, table caption, displayed content,
and paragraph text were present. An AI-assisted page-render check found the
three extracted asset classes (figure, table, and equation) in corresponding
native-page regions. These are mechanical/text and visual concordance
observations only; they are not human native-source adjudication or semantic
meaning-preservation proof. No worker task, producer-artifact ingestion,
Knowhere publication, retrieval top-N result, source-owner gold, source
sufficiency, or qualification gate was exercised. The temporary output and
process were cleaned up; the disposition remains `deferred`.

## Local MinerU public repeat-three canary observation

On 2026-07-19, the existing local MinerU canary corpus was run through the
repository's `validate_codex_export_corpus.py` contract with three public PDF
fixtures, `repeat=3` (nine runs total), pipeline backend, `auto` method,
144-DPI rendering, offline mode, the project-local Python 3.11 runtime,
`uv 0.11.29`, and MinerU revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`. The local runtime preflight was
also rerun with the plan defaults of 10 GiB minimum free disk and 8 GiB
minimum available memory: all project, uv, Python, adapter, temp-writable,
disk, and memory checks were true (`ready=true`). The observed preflight
values were 244,022,784,000 free-disk bytes and 11,079,454,720 available
memory bytes.

The canary report recorded `runs=9`, `completed=9`, `failed=0`,
`expectation_mismatches=0`, and `reproducibility_failures=0`; all nine runs
had verified artifacts, matched the expected completed status, and were
reproducible. Per-fixture maxima were: `canary-unit-pdf` 22.804 seconds and
2,035,503,104 peak RSS bytes; `canary-small-ocr` 40.597 seconds and
2,622,230,528 peak RSS bytes; and `canary-table-pdf` 92.355 seconds and
5,158,113,280 peak RSS bytes (4.804 GiB). The run output retained only in
the private QA area contained zero active `.run-*` or `.mineru-local-*`
directories after completion, and no canary process remained.

This is repeatability, artifact-shape, and mechanical canary evidence for
the direct local MinerU export path. The measured peak RSS is recorded for
operator memory-limit comparison; no deployment/container memory limit was
asserted here. Findings such as table-fidelity or hierarchy observations are
not human meaning-preservation adjudication. The run does not establish full
worker-task MinerU execution, producer-to-Knowhere publication, retrieval
top-N, native/human semantic gold, source sufficiency, 24-hour operational
stability, firewall/egress isolation, rollback, or qualification; the
disposition remains `deferred`.

## Local MinerU public canary native/asset mechanical concordance

The same private repeat-three output was checked mechanically against its
preserved native PDF using Poppler 25.07.0. The representative run was
`run-001`; the repeated runs were additionally checked for stable source,
derivative, structured-tree, and asset-count signatures. For
`canary-unit-pdf`, the native PDF had one page and one embedded image object;
the package rendered one page, preserved three MinerU asset files mirrored by
three raw-image files with identical SHA-256 sets, resolved one Markdown image
reference, and exported one HTML/metadata table. The normalized native-text
token coverage was 89.58% (48 native unique tokens; the metric is mechanical
and tokenizer-dependent).

For `canary-small-ocr`, the native PDF reported eight pages and 496 embedded
image objects, while the requested/rendered package pages were 1 and 2. The
native text extraction contained no comparable alphanumeric/CJK token set, so
native-text coverage is not applicable; this fixture remains an OCR/image
path observation rather than a text-fidelity result. For `canary-table-pdf`,
the native PDF had six pages and 14 embedded image objects; the package
selected/rendered pages 1, 2, 4, and 5, preserved 19 mirrored asset/raw-image
files, resolved eight Markdown image references, exported two HTML/metadata
tables, and produced 93.64% normalized native-text unique-token coverage
(1,100 native unique tokens).

Across all three runs of each fixture, source, `document.md`,
`structured/blocks.jsonl`, and `structured/document_tree.json` SHA-256
signatures were singletons, asset counts were stable, and all checked image
references resolved. These checks establish native-file identity, package
asset linkage, and repeatable mechanical concordance only. They do not close
human/native semantic gold, meaning preservation, critical-cell adjudication,
source sufficiency, or any worker-task, producer-publication, retrieval,
security, operational-stability, rollback, or qualification gate; the
disposition remains `deferred`.

## Bounded worker task local MinerU execution boundary

On 2026-07-19, an isolated worker-task probe used the existing
`parse_task`/Celery eager dispatch path, project-local Python 3.11 runtime,
filesystem object storage, Redis database 14, and the public MinerU
`test.pdf` fixture
(`AE9E3F14CC3BEA88DD0CE4E2715B3B03561378501318DF61F0889DF207AED25B`). The
source upload, database job creation, one-page workload estimation, PyMuPDF
page probe, and native-page render child processes all completed. The
isolated database required the repository's existing `upgrade heads` target
and standalone user-table bootstrap; the generic `upgrade head` target is
ambiguous because the repository has two Alembic heads.

The task then entered the existing coarse document-profile stage and attempted
the configured `qwen3.6-flash` Ali provider. With no `ALI_API_KEYS`
configured, it raised `LLMServiceException` before reaching the local
MinerU `parse_pdf` seam. No worker-task MinerU artifact, job result,
chunk publication, result ZIP, or Knowhere retrieval record was produced.
This is an environment/provider-admission boundary, not evidence that the
local MinerU process seam or direct extraction failed. The eager exception,
synthetic database, Redis DB14 state, temporary workspace, and child
processes were cleaned up; the disposition remains `deferred`.

## Local-only worker task MinerU execution observation

On 2026-07-19, the same public MinerU `test.pdf` fixture was run through the
existing `parse_task`/Celery eager path in a separate isolated PostgreSQL
database and Redis DB15 with filesystem object storage. The worker used the
project-local Python 3.11 runtime, MinerU revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`, `MINERU_PROVIDER=local`, pipeline
backend, offline flags, no cloud provider key, and empty
`IMAGE_MODEL`/`NORMOL_MODEL`/`HIERARCHY_LLM_MODEL` settings so the existing
deterministic profile and heading fallbacks were exercised. The direct parser
seam first completed profile/anatomy, local MinerU extraction, heading
fallback, and Markdown/table/image downstream processing with three rows and
1,098-byte `full.md`.

The actual worker task then completed source upload, database job creation,
one-page workload estimation, PyMuPDF probing, local MinerU parsing, chunk
conversion, result publication, and workspace cleanup. The representative
result was `task_successful=true`, job `status=done`, `page_count=1`, three
job chunks, one document section, a 38,781-byte result ZIP, Redis task status
`done` with progress `100` and message `Task complete!`, and no remaining task
workspace. The ZIP contained `full.md`, `manifest.json`, `chunks.json`,
`doc_nav.json`, `debug/trace.json`, `debug/anatomy_map.json`, one image asset,
and one table asset. No cloud fallback was invoked.

The worker path also reproducibly logged an existing trace-persistence gap:
`document_page_plan.doc_profile` flush failed because the JSONB bind received
a tuple-keyed `Counter` in the profile payload. The task continued and the
result ZIP was published, but this means database-side profile-plan
traceability was not proven by this run; the explicit artifact trace remained
available in the ZIP. This is a worker trace/serialization issue, not evidence
of local MinerU extraction failure, and it must be resolved or explicitly
dispositioned before any complete traceability or qualification claim.

This observation closes only the local-provider path through the existing
worker task and non-semantic result publication for this one-page public
fixture. It does not establish retrieval top-N/source sufficiency, vector
publication, native or human semantic gold, meaning preservation, deletion,
telemetry exhaustiveness, egress isolation, rollback, long-run stability, or
qualification; the disposition remains `deferred`.

## Public-canary worker expansion

On 2026-07-19, two additional public MinerU canary fixtures were run through
the same existing `parse_task`/Celery eager path in the isolated PostgreSQL
database, Redis DB15, and filesystem object-storage runtime described above.
Both runs used the project-local Python 3.11 worker runtime, MinerU revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`, `MINERU_PROVIDER=local`, pipeline
backend, offline flags, empty cloud-key configuration, and no configured
profile/heading model.

The `demo/pdfs/small_ocr.pdf` source (SHA-256
`c48baa1997e719d414061bea6ca197ce36f1c47341837fbfbc976bbb1d226998`) completed
as job `job_small-ocr_32450ecd`: eight-page workload, two job chunks, two
document sections, result ZIP size 17,648 bytes, Redis task status `done` with
progress `100`, and no remaining task workspace. The ZIP contained
`full.md`, `manifest.json`, `chunks.json`, `doc_nav.json`, and debug
trace/anatomy artifacts. The task result reported zero stored vectors and no
cloud key was present.

The `demo/pdfs/demo2.pdf` source (SHA-256
`9e94e95637356e1599510436278747d1150a3dfb822233bdc77a9dcb9a4fc6e4`) completed
as job `job_table-pdf_9e12f192`: six-page workload, 21 job chunks, 12 document
sections, result ZIP size 235,738 bytes, Redis task status `done` with progress
`100`, and no remaining task workspace. The ZIP contained `full.md`, eight
image assets, two HTML table assets, manifest/chunk/navigation files, and debug
trace/anatomy artifacts. The task result again reported zero stored vectors
and no cloud key was present.

Both expanded runs reproduced the same `document_page_plan.doc_profile` JSONB
flush failure caused by a tuple-keyed `Counter`; the page-plan rows therefore
did not provide database-side profile traceability even though artifact trace
files and result publication remained available. The table fixture also logged
`Lock already expired or stolen` during final lock release after its roughly
93-second parse; the task still finalized successfully. This is an additional
lease/long-task operational gap that must be dispositioned before stability or
complete qualification claims.

This expansion strengthens the local-provider worker and non-semantic result
publication boundary across unit, OCR/image-heavy, and table/image-rich public
fixtures. It does not establish retrieval top-N/source sufficiency, vector
publication, native or human semantic gold, meaning preservation, deletion,
telemetry exhaustiveness, egress isolation, rollback, long-run stability, or
qualification; the disposition remains `deferred`.

## Checked-in local MinerU integration test observation

On 2026-07-19, the repository-provided real local MinerU integration test
`apps/worker/tests/integration/test_local_mineru_provider_integration.py`
was run with the public MinerU `test.pdf` fixture, Python 3.11 worker
runtime, `uv 0.11.29`, pipeline backend, offline flags, and no cloud
provider key. The test passed `1 passed in 24.90s`. Its assertions exercised
the real `parse_pdfs` local-provider path, downstream `full.md` handling,
log creation, and the absence of cloud fallback or temporary local-run
artifacts.

This is checked-in integration-contract evidence for the provider seam only.
It does not exercise the full worker task profile stage, producer-to-Knowhere
publication, retrieval top-N, human/native semantic gold, source sufficiency,
or qualification; the disposition remains `deferred`.

## Local MinerU worker publication to active retrieval route

On 2026-07-19, a separate isolated cross-edge observation used the existing
`parse_task`/Celery eager path with the public MinerU `test.pdf` fixture
(`AE9E3F14CC3BEA88DD0CE4E2715B3B03561378501318DF61F0889DF207AED25B`). The
local-only Python 3.11 worker used MinerU revision
`cebf5078a3ed2990260caa03110b0bab82a16b64`, `MINERU_PROVIDER=local`, pipeline
backend, offline flags, filesystem object storage, and Redis DB15. The same
isolated PostgreSQL database was then read through the active Knowhere
retrieval route with authenticated user and namespace scope.

The worker completed job `job_cross_edge_761543b515dd` with `status=done`,
three job chunks, three published `document_chunks`, one `document_section`,
and result/document linkage through job result
`c5805703-bed9-49b8-8a04-b270e641e63e` and document
`doc_7aaa424fed2c`. The worker task reported Redis `done`/100% progress and
zero stored vectors. A subsequent `POST /api/v1/retrieval/query` using the
same user/namespace and the extracted `Figure` marker returned HTTP 200,
router `small_corpus_all`, one result, and 688 characters of evidence. The
returned source identified `mineru-cross-edge-test.pdf`, the same document,
and `Root`; `answer_text` remained empty as designed. This is direct evidence
that the current worker publication rows can be consumed by the active
retrieval route, not merely a memory-only or synthetic-row observation.

The response still had an empty `referenced_chunks` list, used lexical
small-corpus retrieval, and did not establish vector retrieval, ranked
top-N/source sufficiency, citation projection, semantic meaning preservation,
native/human gold, deletion, telemetry, egress, rollback, long-run stability,
or qualification. The previously observed tuple-keyed `Counter` JSONB
trace-persistence gap remained in the worker boundary. The isolated database,
nine probe Redis keys, and temporary filesystem root were removed after the
observation; the disposition remains `deferred`.

## Active retrieval response to RA acceptance boundary

The cross-edge response remained the native API `RetrievalQueryResponse` shape
(`namespace`, `query`, `router_used`, `evidence_text`, `results`, and related
runtime fields); it did not emit the opt-in canonical
`knowledge-retrieval-result-v1` serializer payload. Required canonical
source/version identity, memory-snapshot and configuration hashes, native page
and extraction-block locators, citation, and fixed `unverified`/
`not_source_sufficiency_decision` fields were not present in the active route
response. The empty `referenced_chunks` list therefore cannot be treated as a
native citation locator.

The current serializer/schema contract tests passed 7/7, and the RA-side
document-runtime CLI/contract tests passed 30/30 against their controlled
fixtures. No active local-MinerU route response was passed through the
canonical serializer or RA `verify-result`, and no acceptance record or
runtime authorization was created. WP-06 therefore remains
`declared_not_runtime`/`pending_source_owner`; the disposition remains
`deferred`.

## Existing worker lifecycle idempotency and recovery controls

After the user-level PostgreSQL 15 portable runtime was installed and added
to the user PATH, the existing worker contract suite
`apps/worker/tests/contract/test_parse_task_contract.py` passed 13/13. The
suite exercised real lifecycle boundaries for successful result publication,
result ZIP creation, a second job with the same parsed content, concurrent
billing initialization, terminal-job skip without outputs, missing-source
failure cleanup, parse-failure refund, and PDF page-limit rejection. The
existing stale-job sweeper contract passed 2/2 for durable expiry failure
state and duplicate-Beat lock handling.

Static review also confirms that the existing success finalizer reuses a
`JobResult` by `job_id`, replaces its job chunks inside the lifecycle
transaction, and applies a document-current-result/stale-completion guard
when publishing document revisions. This is bounded job-lifecycle
idempotency/recovery evidence. It does not connect those controls to
`document-extraction-manifest-v1`, source-version or extraction-run lineage,
partial canonical-manifest replay, or source-owner recovery semantics.
Therefore it strengthens the mechanical worker lifecycle observation only;
WP-05 D5 remains deferred and no qualification or edge-promotion claim is
made.

## Retrieval isolation and reference projection contract observation

On 2026-07-19, the existing API retrieval contract suite
`apps/api/tests/contract/test_retrieval_contract.py` passed 15/15 with the
project root API runtime, isolated PostgreSQL contract process, and fake
Redis boundary. The suite covered authenticated user/namespace scoping,
default namespace behavior, empty-query handling, classic top-k routing,
agentic root/discovery reference projection, table-artifact exclusion from
VLM input, out-of-scope reference rejection, same-chunk-id disambiguation
across documents and sections, request validation, and document/section
exclusion filters. Twelve existing deprecation warnings were reported.

This is mechanical retrieval isolation and API reference-projection evidence
against controlled seeded rows. It is not evidence that active local-MinerU
publication supplies canonical source/version identity, ranked production
top-N/source sufficiency, native semantic gold, or RA acceptance locators;
the active cross-edge observation still returned an empty
`referenced_chunks` list. WP-04/WP-06 qualification gates remain deferred.

## Page locator and citation-asset contract observation

On 2026-07-19, the existing page-memory retrieval and node-assembler contract
suites passed 26/26. The contracts covered page/table search-text projection,
summary-over-raw-content assembly, page-number asset URL generation,
page-citation asset precedence over lazy page-PDF fallback, artifact allowlist
and referenced-file filtering, source-PDF page cropping/cache reuse,
reference hydration, page ownership/order behavior, and preservation of
page-citation assets in node rows.

This is mechanical artifact/locator and retrieval-hydration evidence. It does
not establish that the locator came from a reviewed native source, that
MinerU extraction blocks are linked, that semantic meaning is preserved, or
that a source is sufficient for RA use. The active local-MinerU response
still lacked canonical locators and had empty `referenced_chunks`; WP-06
native verification, human gold, and acceptance remain deferred.

## Active retrieval top-N and namespace-isolation probe

On 2026-07-19, an isolated active API-route probe seeded three distinct
synthetic documents in one user/namespace and one decoy document in a second
namespace. A `POST /api/v1/retrieval/query` with `use_agentic=false` and
`top_k=2` returned HTTP 200, `router_used=classic_topk`, exactly two results,
and two distinct document IDs. Both result IDs belonged to the requested
namespace; the decoy was absent. The active route logged ranked scores of
1.0000 and 0.4920 for the returned rows.

This closes only active-route mechanical top-N truncation and namespace
isolation for controlled synthetic rows. It does not establish a gold ranking
set, producer-manifest/source-version linkage, vector retrieval, semantic
meaning preservation, source sufficiency, or RA acceptance. The probe also
reproduced two Windows cp950 console encoding warnings for emoji log markers;
the route/test completed successfully and no data-state failure was observed.
WP-04 qualification and WP-06 acceptance remain deferred.

## Archive and current-revision negative contract recheck

The current-head API document contracts passed 4/4 for the selected archive
and negative-path cases: authenticated namespace document listing, archived
page-citation-source rejection, canonical archive route persistence, and
legacy archive route persistence. These checks confirm archive-state and
current-route visibility behavior for controlled rows. They do not establish
hard deletion, object-storage deletion, vector or memory-snapshot deletion,
canonical result lifecycle, or source-version completeness; WP-04 deletion
qualification remains deferred.

## Current-head contract regression recheck

On 2026-07-19, the existing worker-side qualification and lifecycle contract
group was rerun from the current Knowhere head with the project-local Python
3.11 worker environment and the portable PostgreSQL runtime. The selected
MinerU provider/runtime/artifact, canonical retrieval-result serializer,
page-memory retrieval and node-assembly, parse-task, and stale-job suites
completed with `82 passed, 1 skipped` in 30.62 seconds. The selected API
retrieval and document/archive contract group completed with `32 passed` and
12 existing deprecation warnings in 184.13 seconds.

This is current-head regression evidence only. It confirms that the existing
mechanical contract baseline remains reproducible after the environment
qualification work; it does not add a canonical manifest consumer, source
version or extraction-run lineage, vector publication, native/human semantic
gold, source-sufficiency decision, hard deletion proof, or RA acceptance
authorization. WP-03/WP-04/WP-05/WP-06 qualification and runtime edge
promotion remain deferred, and no implementation change was made.

## Cross-repository contract boundary revalidation

On 2026-07-19, the RA document-runtime contract validator passed the existing
`pass`, `knowhere_to_ra`, and `mineru_to_knowhere` fixture roots. Each result
kept the runtime-disabled and producer-qualification-explicit boundary. The
four existing `synthetic-runtime-evidence-v1` records also passed structural
and semantic validation, retaining their recorded `failed` or `blocked`
statuses. Knowhere's canonical retrieval-result serializer and producer
contract tests passed 7/7. The pinned producer schema hashes matched the RA
records: MinerU `8d649b58e6748ae7d1fbd021d76b3c154d544044a37fd357b3e6bcdf03f25def`
and Knowhere `54307e0c42ebf737af897b691badda18fd6c673f64aef3cf7eb961dab0123c4a`.

This revalidation confirms contract identity and fail-closed metadata
boundaries only. It does not establish active manifest consumption, active
canonical result emission, native-source verification, source sufficiency,
deletion completeness, or RA acceptance authorization; qualification and
runtime edge promotion remain deferred.

## Current-head telemetry contract revalidation

On 2026-07-19, the existing API self-hosted telemetry contract suite passed
`23 passed` in 0.50 seconds from the project API environment. The suite covers
anonymous event/property allowlisting, removal of unknown and non-scalar or
sensitive values, installation identity, startup/shutdown/heartbeat events,
batch sizing and flushing, API request metrics snapshots, aggregate telemetry,
and explicit telemetry disable/override behavior. Current app source contains
the API telemetry middleware and self-hosted telemetry runtime; this corrects
the narrower earlier statement that the application lacked instrumentation.

The suite uses a fake PostHog client and contract-local fixtures. It does not
prove an actual external telemetry delivery, host-level egress denial, sink
retention, or D2 runtime qualification. The existing D2 records therefore
retain their `failed`/`blocked` dispositions, while this current-head result
upgrades the application-side telemetry evidence from harness-not-run to
`partial_mechanical_only`. No runtime edge was promoted.

## Actual telemetry client localhost-sink smoke

On 2026-07-19, the current telemetry client was exercised with its real
PostHog SDK pointed at a temporary localhost-only HTTP sink. One queued
`oss_instance_heartbeat` event produced one `/batch/` request and one captured
event. The captured property keys contained the allowed `app_version` and
`api_healthy` values plus SDK-safe fields; `private_prompt`, `document_id`,
and nested non-scalar data were absent. The sink received no external
destination, and the temporary server was stopped after the observation.

This is stronger application-side delivery and sanitization evidence than the
fake-client contract alone, but it does not prove host-level default-deny
egress, real PostHog retention, production network policy, or the remaining D2
controls. The disposition remains `partial_mechanical_only`; no runtime edge
or qualification status changed.

## Canonical contract frozen-revision ancestry revalidation

On 2026-07-19, the two cross-repository compatibility profiles were checked
against the current pinned worktree histories without changing either
repository. The MinerU profile's canonical revision
`7048473f0c51c2062e98e700c56286c94e8ea90a` and the Knowhere profile's
canonical revision `71ff7fc1128743a9135f65b110d49504768c08b3` were present as
ancestors of the current pinned heads. The schema bytes at the frozen
revisions matched the current producer schema bytes exactly: MinerU
`8d649b58e6748ae7d1fbd021d76b3c154d544044a37fd357b3e6bcdf03f25def` and
Knowhere `54307e0c42ebf737af897b691badda18fd6c673f64aef3cf7eb961dab0123c4a`.

This closes only the specific frozen-revision ancestry and schema-byte
identity check. It does not establish active consumption of
`document-extraction-manifest-v1`, active emission of
`knowledge-retrieval-result-v1`, native-source verification, source
sufficiency, deletion completeness, or RA acceptance authorization. The
profiles remain `source_owner_frozen` / `pending_source_owner`, both edges
remain `declared_not_runtime`, and the qualification disposition remains
`deferred`. No implementation change was made.

## Current-head worker and API contract recheck with process-local PostgreSQL

On 2026-07-19, the current pinned Knowhere worktree at `b2df5d9b` was
rechecked using the existing Python 3.11 worker environment and the project
API environment. The worker-side MinerU provider/runtime/artifact, parse,
page-memory, canonical retrieval-result serializer, stale-job, and local
provider integration scope completed with `85 passed, 2 skipped` in 30.64
seconds. The API retrieval and page-memory/parse-track contract scope
completed with `33 passed` in 100.70 seconds and 13 warnings (12 existing
retrieval deprecation warnings and one duplicate OpenAPI operation-ID warning).

The worker tests require `pg_config`/`pg_ctl` for their local
`pytest-postgresql` fixtures. The Codex process had not inherited the user PATH
entry added for the existing portable PostgreSQL installation, so an initial
invocation stopped at setup with 12 environment errors. A process-local PATH
prepend resolved `pg_config` and `pg_ctl` to that existing installation; one
failing parse-task test then passed, followed by the complete worker scope
above. No repository, database, service, or test configuration was changed.

This is current-head mechanical contract and environment-reproducibility
evidence only. It does not add canonical MinerU manifest consumption,
source-version or extraction-run lineage, active canonical result emission,
native/human semantic gold, source sufficiency, hard deletion, or RA
acceptance authorization. WP-03/WP-04/WP-05/WP-06 qualification and runtime
edge promotion remain deferred, and no implementation change was made.

## Critical identifier and negation gold-preparation mechanical recheck

On 2026-07-19, a new synthetic-only DOCX was generated under the private
`.qa` boundary from the existing public fixture generator, then extended with
explicit identifier, lot, numeric/unit, negative-condition, no-fallback, and
table/image-locator categories. The input SHA-256 was
`09c8740b7a1e42d5bbeae97f23ce1adfd9c9c560da6277e1f4b9c123d07aedb1`.

The existing offline/local export path completed with manifest status
`completed`; the manifest source hash matched the host input hash. It emitted
18 blocks, 3 tables, 1 image block, 24 inventoried artifacts, and 2
mechanical findings. All 9/9 critical category tokens were present in the
derivative/raw/structured package, and all matching blocks had explicit
producer source locators and provenance metadata. The Office parser locators
were logical page locators; normalized-PDF mapping remained `unmapped`.

Thirteen memory-only projections were then built from the producer blocks
through the existing opt-in `knowledge-retrieval-result-v1` serializer. All
13 passed the canonical JSON Schema, retained an explicit extraction block
locator, emitted no RA authority/readiness fields, and preserved
`native_source_verification_status: unverified` plus
`not_source_sufficiency_decision: true`. No Knowhere API, worker task,
database, vector store, active retrieval route, or provider was used.

This is critical-category mechanical gold preparation only. It does not
constitute human/native adjudication, physical pagination verification,
semantic meaning preservation, retrieval top-N evidence, source sufficiency,
deletion qualification, or producer/edge qualification. The package was
requested offline but recorded `offline_verified: false`; that remains an
environment attestation limitation. No implementation change was made.

## Native physical-pagination cross-check for critical gold preparation

On 2026-07-19, the exact private native `source.docx` from the critical
synthetic package was converted with the installed LibreOffice 26.2.4.2 into
a two-page letter-size PDF under the ignored `.qa` boundary. The rendered PDF
SHA-256 was
`59ca027d88587c884d75bd5edabd18ef1553e8b2628d5837bc594667e588251e`.
The existing exporter-normalized PDF was also two pages with the same page
size, but its byte hash differed because it was a separate generated artifact.

A read-only text crosswalk found the run identifier, device identifier, lot
identifier, negative-condition wording, table-cell guard, and image-locator
guard on physical page 2. Their corresponding MinerU blocks still carried
`office_logical_page` locators with `page_number: 1` and
`normalized_pdf_mapping_status: unmapped`. The repeated current/temperature
unit categories appeared on both physical pages; the no-fallback phrase was
line-wrapped in PDF text extraction, while its `fallback` term was present on
page 2. This is a native-pagination/locator discrepancy, not a source-content
loss determination.

The result is a negative locator observation: physical page citation and
native locator qualification remain open. No locator was corrected, no
implementation change was made, and no runtime edge or qualification status
was promoted. The private rendered PDF and source package remain outside Git.

The same two-page PDF was also rendered at 150 DPI with the existing Poppler
`pdftoppm` tool and visually inspected under `.qa`. Page 1 ends with the
overview metrics and embedded image; page 2 visibly contains the results table,
conclusion, critical identifiers, negative rule, and identifier table. This
confirms that the physical-page discrepancy is not an artifact of text
extraction. The rendered page images remain private and no locator correction or
qualification claim was made.

## Telemetry disabled-path localhost negative control

On 2026-07-19, the existing `start_self_hosted_telemetry` runtime path was
exercised with `TELEMETRY_ENABLED=false`, a synthetic project key, and a
temporary localhost-only HTTP sink. The installed PostHog package was
importable, but the disabled branch returned `None` before installation
identity resolution or client construction; the sink received zero POST
requests during the bounded observation window.

This is application-side negative-control evidence that the explicit telemetry
disable flag suppresses the self-hosted telemetry startup path. It does not
prove host-level default-deny egress, production configuration precedence,
telemetry exhaustiveness, retention behavior, or any remaining D2 control. The
telemetry evidence remains `partial_mechanical_only`, D2 remains `blocked`, and
no runtime edge or qualification status changed. No implementation change was
made.

## Telemetry configuration default/override audit

On 2026-07-19, a read-only `BaseConfig` probe with the project `.env` source
excluded and only synthetic required storage settings supplied resolved the
application defaults as `TELEMETRY_ENABLED=True` and
`TELEMETRY_POSTHOG_HOST=https://us.i.posthog.com`. Supplying the explicit
constructor override `TELEMETRY_ENABLED=False` resolved the flag to `False`
while leaving the host value unchanged. No telemetry client was started and
no network request was made by this configuration probe.

This confirms that the current application default is opt-out rather than
default-off, and that the public PostHog host remains the configured default;
an operator deployment must therefore demonstrate an explicit disable or
approved egress policy before runtime qualification. The probe does not verify
deployed environment precedence, container network enforcement, telemetry
exhaustiveness, or D2. D2 remains `blocked`, and no implementation, runtime
edge, or qualification status changed.

## Current-head isolated contract regression recheck

On 2026-07-19, the current pinned Knowhere head
`67a18d4bc32cae7ab3bb55da39a411dc1afb5e9a` was rechecked with the existing
project-local environments and a process-local PostgreSQL PATH prepend. The
isolated worker selection covering MinerU provider/artifact/runtime
preflight, local-process boundaries, parse tasks, page-memory retrieval,
canonical retrieval-result serialization, stale-job lifecycle, and the local
MinerU integration marker completed with `80 passed, 2 skipped` in 30.98
seconds. The isolated API selection covering retrieval, documents, and
page-memory/parse-track contracts completed with `50 passed` in 176.54
seconds and 13 existing warnings.

An initial attempt launched both selections concurrently and produced one
failure in the worker concurrent-parse billing test while the API suite was
running. The failure showed shared test object-storage cleanup removing a
temporary result/source path; the same test passed in three consecutive
isolated reruns, and the complete worker selection then passed when run alone.
The bounded validation rule is therefore sequential suite execution, not a
product failure claim. This is current-head mechanical contract and test
environment-boundary evidence only; native/human semantic gold, source
sufficiency, hard deletion, canonical active-edge consumption/emission, RA
acceptance, and qualification remain deferred. No implementation change or
runtime-edge promotion was made.

## Source-owner/native adjudication handoff packet

The existing private synthetic package
`.qa/wp03-critical-gold-run-20260719-01` is now bounded as a handoff packet for
source-owner and RA/native review. It is not a gold decision and does not
change the qualification status. The packet identity is:

* run ID: `EXT-WP03-20260719-CRITICAL-NEGATION-001`;
* native source: `package/native/source.docx`, SHA-256
  `09c8740b7a1e42d5bbeae97f23ce1adfd9c9c560da6277e1f4b9c123d07aedb1`;
* parser: MinerU `3.4.4`, pinned revision
  `cebf5078a3ed2990260caa03110b0bab82a16b64`, effective `office` backend;
* producer logical page count: `1`; `offline_verified: false` remains an
  environment-attestation limitation;
* native LibreOffice render: two physical pages, with `source.pdf` SHA-256
  `59ca027d88587c884d75bd5edabd18ef1553e8b2628d5837bc594667e588251e`.

The nine critical categories are mechanically present in the producer
package and mapped below for a human/native decision. The producer locator is
logical page 1 for these blocks; the native crosswalk places the critical text
on physical page 2, so the mapping remains unresolved.

| Critical category | Producer block(s) | Native observation | Required owner disposition |
|---|---|---|---|
| Run identifier | `blk_b3ee4ef8cbf69c9ca189` | Text observed on physical page 2 | Confirm exact native text and citation |
| Device identifier | `blk_a635b9bc012591f84f67` | Text observed on physical page 2 | Confirm identity and citation |
| Lot identifier | `blk_a635b9bc012591f84f67` | Text observed on physical page 2 | Confirm identity and citation |
| Measured current | `blk_a635b9bc012591f84f67`, `blk_2388158ac28fc3e2ba69` | Paragraph/table value observed on physical page 2 | Confirm value, unit, and native table cell |
| Temperature | `blk_a635b9bc012591f84f67`, `blk_2388158ac28fc3e2ba69` | Paragraph/table value observed on physical page 2 | Confirm value, unit, and native table cell |
| Acceptance threshold / negative rule | `blk_0a7cdd339e6ff33eeac1` | Text observed on physical page 2 | Confirm wording and decision meaning |
| No-fallback rule | `blk_0a7cdd339e6ff33eeac1`, `blk_2388158ac28fc3e2ba69` | Text was line-wrapped in extracted PDF; `fallback` is present on physical page 2 | Confirm complete native wording and zero-fallback value |
| No dropped table cell | `blk_afd01ab66dca63d82f43`, `blk_2388158ac28fc3e2ba69` | Guard text and identifier table observed on physical page 2 | Confirm each decision-relevant cell against native table |
| Missing image locator fails closed | `blk_afd01ab66dca63d82f43`, `blk_c3930e0a052a7b5fffad` | Guard text is on physical page 2; embedded image is on physical page 1 | Confirm image identity, locator, and fail-closed interpretation |

The table is a review index only. It does not assert that any category is
accepted, source-sufficient, semantically preserved, or citation-qualified.
The packet remains `pending_human_adjudication`; native verification remains
`unverified`; top-N retrieval remains `not_run_active_route_disabled`; and the
qualification disposition remains `deferred`. No database, active route,
provider, private-data workflow, implementation change, or runtime-edge
promotion was used.

## Archived citation-source negative-path recheck

On 2026-07-19, the existing API document contract was re-run with the focused
selection `-k "archive or archived_page_citation"`. The canonical and legacy
archive-route tests passed, and the archived-document page-citation-source
test returned HTTP 404 even when a citation source object had been staged.
The focused selection completed with `3 passed, 14 deselected`.

This is bounded archive-state and citation-source negative-path evidence only.
It does not prove hard deletion from object storage, vectors, memory, or
derived retrieval results; it does not establish stale-version non-retrieval,
source sufficiency, native/human gold, RA acceptance, or qualification. The
qualification disposition remains `deferred`, and no implementation, edge,
private-data, provider, or runtime status changed.

## Archived retrieval runtime probe

On 2026-07-19, a temporary synthetic API probe seeded one document containing
the marker `archived retrieval probe sentinel`, changed only that document's
status to `archived`, and queried the existing `/api/v1/retrieval/query`
route. The route returned HTTP 200 with `result_count: 0`; the archived
document ID and marker were absent from the result set. The probe also
confirmed the current query path's `Document.status == 'active'` and
`current_job_result_id` join boundary through observed zero-row behavior.

This is runtime evidence for active-status exclusion only. It does not prove
hard deletion of object-storage/vector/memory artifacts, stale-version
non-retrieval across every route, canonical producer-result emission, native
or human semantic gold, source sufficiency, RA acceptance, or qualification.
The qualification disposition remains `deferred`; the temporary probe file
was removed and no implementation or edge status changed.

## Current-revision runtime probe

On 2026-07-19, a temporary synthetic API probe seeded an older and a newer
job result for the same document, advanced the document's
`current_job_result_id` to the newer result, and queried the existing
`/api/v1/retrieval/query` route for both revision markers. Both responses
returned HTTP 200 and `result_count: 1`; the older marker was absent while the
newer marker was present (`old_marker_present: False`,
`new_marker_present: True`).

This is observed stale-content exclusion through the current-result join for
the exercised route. It does not prove every retrieval route, hard deletion
from object storage/vector/memory artifacts, canonical producer-result
emission, native or human semantic gold, source sufficiency, RA acceptance,
or qualification. The qualification disposition remains `deferred`; the
temporary probe file was removed and no implementation or edge status
changed.

## Worker process, artifact, and webhook safety contract recheck

On 2026-07-19, the existing worker contract selection
`test_local_mineru_process_contract.py`, `test_mineru_artifact_contract.py`,
and `test_webhook_recovery_contract.py` completed with `20 passed, 1 skipped`
in 20.52 seconds. The selection mechanically covered argv construction
without a shell, secret redaction, timeout/process-tree termination, bounded
stdout/stderr persistence, project-path validation, artifact manifest/schema
validation, path traversal, hash/source-identity checks, required-artifact
parsing, orphaned/completed/stale webhook recovery, and duplicate-Beat
suppression.

The artifact symlink-escape test was skipped because this Windows host could
not create a symlink (`WinError 1314`, required privilege not held). The
symlink guard is therefore not locally executed evidence. This recheck is
mechanical process/artifact/recovery safety evidence only; it does not prove
runtime no-cloud-fallback behavior, egress control, deletion completeness,
canonical manifest consumption, source sufficiency, native/human semantic
gold, RA acceptance, or qualification. The qualification disposition remains
`deferred`; no implementation or edge status changed.

## Native locator and page-render contract recheck

On 2026-07-19, the existing worker contracts
`test_codex_block_normalizer_contract.py` and
`test_codex_page_render_contract.py` completed with `33 passed` in 2.41
seconds. The selection covered deterministic block IDs and content hashes,
page and section structure, table/image provenance, unknown-block handling,
logical-versus-normalized DOCX page locators, JSONL round-tripping, supported
MinerU block types, standalone rendering, explicit normalized-page selection,
invalid page/DPI rejection, argv construction without a shell, and standard
LibreOffice resolution.

This is mechanical locator/render contract evidence only. It does not verify
the critical private native source against producer blocks, resolve physical
versus logical pagination, establish source sufficiency or semantic gold, or
qualify citation locators. The existing handoff packet's physical-page 2
versus producer logical-page 1 mapping remains `unmapped`; no locator was
corrected, and the qualification disposition remains `deferred`. No
implementation or edge status changed.
