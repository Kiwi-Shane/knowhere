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
| Backup/restore | Synthetic PostgreSQL 15.18 custom-format dump/restore smokes matched both a generic fixture and an Alembic-migrated application-schema fixture; LocalStack S3 service and existing Knowhere S3 adapter round-trips also matched; production backup, retention, and recovery controls remain untested. | `partial_mechanical_only` |
| External telemetry and LLM/VLM egress | Local/offline contract tests cover application flags and provider boundaries; a read-only host firewall audit showed profiles enabled but default outbound `Allow`, so host-level default-deny network isolation remains unverified. | `partial_mechanical_only` |
| Result provenance and native locator | The opt-in serializer requires source/version, explicit block IDs, page range, native citation, and emits the fixed `unverified` native-source status; no active retrieval route or gold result set is wired. | `partial_mechanical_only` |
| RA acceptance fields in producer result | Canonical fixture has no `evidence_status`, `readiness_status`, or `regulatory_conclusion`. | `mechanical_pass` |
| Critical gold evidence in top-N and meaning preservation | A temporary synthetic four-question active-route probe found all expected chunks and exact extractive content in `classic_topk` top-three results; native-source and human adjudication remain open. | `partial_mechanical_only` |

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

## Current local launcher boundary recheck (2026-07-19)

Knowhere revision `1763610b73a6f1ae92d5eaef2d5bcaf14f1a9b0a` updates the
existing `deploy/local-dev/start-dev.sh` summary so its documented API start
command uses `127.0.0.1` rather than `0.0.0.0`, and it no longer prints the
development PostgreSQL credential. The launcher contract now passes alongside
the Compose boundary checks. The script was not executed against the running
local stack, and no container was restarted or stopped.

This is guidance/configuration hardening only; it does not establish runtime
network state, host firewall policy, secret rotation, or production
qualification. D2 remains `blocked`, with no provider, private-data,
active-edge, source-sufficiency, or RA status change.

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

## Offline-verifier safety contract recheck

On 2026-07-19, the existing
`test_codex_offline_verification_contract.py` selection completed with
`5 passed` in 0.26 seconds. The contract covered non-administrator
fail-closed behavior before rule creation, outbound blocking rules for both
the `uv` and MinerU Python executables, `shell=False` command execution,
offline environment variables, verified/unverified attestation output, rule
cleanup after validator failure, and failure to attest when cleanup fails.

The selection used a recorded command double for `netsh`; it did not install
or exercise host firewall rules and does not prove deployed default-deny
egress, external telemetry suppression, production configuration precedence,
or runtime qualification. D2 and the qualification disposition remain
`blocked`/`deferred` at their existing boundaries; no implementation or edge
status changed.

## Current-revision multi-router runtime probe

On 2026-07-19, a temporary synthetic API probe seeded older and newer results
for one document in isolated contract databases and exercised the active
`/api/v1/retrieval/query` route through both router selections. The
`small_corpus_all` old/new queries each returned HTTP 200 with
`result_count: 1`; the old marker was absent from the result/evidence/
reference payload while the new marker was present. The `classic_topk`
old/new queries showed the same boundary: HTTP 200, `result_count: 1`, old
marker absent, and new marker present.

This strengthens observed current-result/stale-content exclusion across two
active router paths only. It does not prove agentic-path behavior across all
variants, hard deletion from object storage/vector/memory artifacts, canonical
manifest consumption, source sufficiency, native or human semantic gold, RA
acceptance, or qualification. The temporary probe file was removed; the
existing Windows cp950 emoji logging warnings remain an environment output
boundary. No implementation or edge status changed.

## Current-revision agentic runtime probe

On 2026-07-19, a temporary synthetic API probe enabled the existing
`LLM_MOCK_ENABLED` boundary and exercised `/api/v1/retrieval/query` with
`use_agentic: true` after advancing one document from an older to a newer
result. Both old and new queries returned HTTP 200 through
`workflow_single_step` with `result_count: 1`; the old marker was absent from
the result/evidence/reference payload while the new marker was present.

This is bounded stale-content exclusion evidence for the exercised mocked
agentic route. It does not prove external LLM/VLM behavior, production
agentic planning, hard deletion, canonical manifest consumption, source
sufficiency, native or human semantic gold, RA acceptance, or qualification.
The temporary probe file was removed; cp950 emoji logging warnings remain an
environment output boundary. No implementation or edge status changed.

## Synthetic PostgreSQL backup/restore smoke

On 2026-07-19, an isolated synthetic PostgreSQL 15.18 source database was
populated with two fixture rows, exported with `pg_dump` custom format, and
restored into a separate temporary database with `pg_restore`. The dump was
1,864 bytes; the source and restored row-count/content fingerprints both
matched `2:277039fca06d4cfdc5b5f313c4feb2d8`. The temporary databases and
container dump were removed after the comparison.

This is storage-layer synthetic backup/restore evidence only. It does not
cover the production Knowhere database, object-storage/vector/memory
artifacts, backup encryption or immutability, retention policy, scheduled
backup delivery, restore authorization, RTO/RPO, application consistency, or
qualification. The matrix disposition is therefore
`partial_mechanical_only`; no implementation or edge status changed.

### Application-schema backup/restore extension

On 2026-07-19, the existing Alembic migrations were applied to an isolated
synthetic PostgreSQL 15.18 source database through both current heads. The
source was populated with one linked user/job/job-result/document/document-
chunk fixture, then exported as a container-local custom-format dump of
95,475 bytes (SHA-256
`55d0a865eca3fc967964938c8955f8c9542149f96328ee8dfb27ee33d2306d4a`) and
restored into a separate temporary database with `pg_restore --exit-on-error`.
The source and restored databases each contained 33 public tables with the
same schema fingerprint
`33:f0b1c1eafb1356470e3235f114362018`; the five core fixture table counts
were `1:1:1:1:1` and the linked-data fingerprint matched at
`cb73baaa78084a55f7b20dff9045528f`. Both temporary databases and the
container dump were removed after comparison.

This strengthens application-schema mechanical recovery evidence only. It
does not cover production backup scheduling, object-storage/vector/memory
artifacts, encryption or immutability, retention, restore authorization,
RTO/RPO, application-consistency coordination, deletion recovery, native or
human gold, source sufficiency, or qualification. The matrix disposition
remains `partial_mechanical_only`; no implementation or edge status changed.

### Synthetic object-storage round-trip control

On 2026-07-19, the existing LocalStack S3 service (`3.8.1`) was used with
two uniquely named temporary buckets and a 68-byte synthetic JSON fixture.
The fixture was written to the source bucket, read back, written to the
restore bucket, and read back again. Source and restored content matched at
SHA-256
`d70d0f08461f8304479c4deb008b2826c58cdebee370d9f35893b56a072c43d1` and
content length `68`. The temporary object and both buckets were removed, and
the post-run bucket check found no `qa-app-bk-obj-*` buckets remaining.

This is an object-storage service/control round-trip only. It does not prove
production backup scheduling or restore orchestration, object versioning,
encryption or immutability, retention, vector/memory artifact coverage,
authorization, RTO/RPO, or qualification. The matrix disposition remains
`partial_mechanical_only`; no implementation or edge status changed.

### Knowhere application S3-adapter round-trip control

On 2026-07-19, the existing `S3StorageAdapter` and `JobFileStorage` path was
exercised against a uniquely named temporary LocalStack bucket with a
62-byte synthetic JSON fixture. The path performed upload, existence/size
verification, download-to-temp, content comparison, deletion, and
post-deletion existence verification. Source and restored content matched at
SHA-256
`940df415b6e9fc0e4928a261a0524af097fbccd9fa082486ccbc317a74421b8f`, and
the temporary object and bucket were removed after the run.

This is application storage CRUD and cleanup evidence only. It does not prove
backup scheduling or restore orchestration, versioning, encryption or
immutability, retention, vector/memory artifact coverage, authorization,
RTO/RPO, or qualification. The matrix disposition remains
`partial_mechanical_only`; no implementation or edge status changed.

## Active synthetic extractive gold-question probe

On 2026-07-19, a temporary active API probe seeded four synthetic question
categories in one namespace and queried the existing route with
`use_agentic: false` and `top_k: 3`. All four queries returned HTTP 200 through
`classic_topk` with three results; the expected document/chunk was present in
the top three for every category, and the expected extractive content matched
exactly (`4/4`).

This is active-route synthetic top-N and extractive-content evidence only. It
does not establish a native-source gold set, human semantic adjudication,
meaning preservation for MinerU derivatives, source sufficiency, vector
retrieval, canonical manifest lineage, RA acceptance, or qualification. The
temporary probe file was removed; no implementation or edge status changed.

## Host firewall outbound-policy observation

On 2026-07-19, a read-only Windows Firewall audit showed Domain, Private, and
Public profiles enabled with the active policy `BlockInbound,AllowOutbound`.
The PowerShell ActiveStore view reported `DefaultOutboundAction=Allow` and
seven enabled outbound block rules. No firewall rule or profile setting was
created, changed, or removed.

This confirms that host-level default-deny egress was not demonstrated on the
qualification host; it is not a D2 pass. Application telemetry-disable and
offline-verifier contract results remain application-side evidence only, D2
remains `blocked`, and no implementation, edge, or qualification status
changed.

## Source-owner/native packet integrity audit

On 2026-07-19, a read-only integrity audit rechecked the existing private
synthetic handoff packet `EXT-WP03-20260719-CRITICAL-NEGATION-001` without
changing its files. The package and MinerU manifests both reported
`completed`; the native DOCX SHA-256 matched the manifest and the recorded
source hash. All 24 inventoried package artifacts matched their recorded
size and SHA-256 values. The structured block file contained 18 parseable
lines with 18 unique block IDs, and all six unique producer block IDs used by
the nine-category review index were present. Their locators were consistently
`office_logical_page`, logical page 1, with normalized-PDF mapping
`unmapped`.

The audit also found two portability boundaries that must remain visible to
the owner/native review. The image block preserves the producer reference
`images/c0fe4015d52e08dcc84cb5e0bad1feb22564800020e0e5fdd53e489644d04888.jpg`,
but that exact package-root path is absent; the copied file is present under
`assets/` and `raw/mineru/images/`. The package manifest reports zero selected
render pages, so the two private native render PNGs used for the physical-page
observation are adjacent to the package rather than self-contained under a
package `pages/` directory. The package normalized PDF and the adjacent
render PDF both have two pages and the same extracted-text SHA-256
`fae8d758b58c482e82045f0614293ece5f2e3a181283d5e097b1431b860ce4e6`, while
their file hashes differ (`9b590098300ebd966c2e24f24fa82869e3acadfdaff06d1dd402d18127d92a08`
versus
`59ca027d88587c884d75bd5edabd18ef1553e8b2628d5837bc594667e588251e`), so no
PDF byte identity is inferred.

The existing review-package contract suite passed `8` tests in `4.81`
seconds. It verifies manifest inventory hashes and package safety, but does
not verify that every structured block asset reference resolves from the
package root or that native render pages are included when the packet claims
physical-page observations. This audit therefore records a packet
portability/locator gap for owner disposition; it does not correct a locator,
accept a category, establish source sufficiency, or change
`pending_human_adjudication`, `unverified`,
`not_run_active_route_disabled`, or `deferred`. No implementation, database,
active route, private-data workflow, provider, or runtime-edge promotion was
used.

## Review-package/client-artifact seam audit

On 2026-07-19, a read-only seam probe compared the existing critical packet's
image block reference with the existing client-artifact contract. The block
reference is `images/c0fe4015d52e08dcc84cb5e0bad1feb22564800020e0e5fdd53e489644d04888.jpg`;
the exact package-root path does not exist, while equivalent copies exist
under `assets/` and `raw/mineru/images/`. The existing storage normalizer
accepts the `images/...` reference and the existing ingestion collector emits
it for an image chunk, but rejects both `assets/...` and
`raw/mineru/images/...` as client artifact references. The focused review-
package and page-memory contract selection passed `20` tests.

This narrows the finding to a portability seam between the Codex review
package's copied asset layout and the client-visible artifact-root contract;
it is not evidence of an active runtime-edge failure because no active edge or
private workflow was exercised. No path was corrected and no package, storage,
schema, or runtime implementation was changed. Native verification, source
sufficiency, RA acceptance, and qualification remain deferred.

## Current-head review-package and page-memory contract recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`5b2a067c` reran the existing review-package and page-memory retrieval
contract selection with the project-local Python 3.11 environment. The
selection passed `20` tests in `5.72` seconds. This reconfirms current-head
mechanical package, locator, and retrieval-hydration behavior only; it does
not resolve the recorded package-root asset portability gap, establish native
verification, semantic gold, source sufficiency, RA acceptance, or active-edge
qualification. No path, package, storage, schema, or runtime implementation
was changed.

## Current-head WP-05 lifecycle recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`155f5cdf` reran `test_parse_task_contract.py` and
`test_stale_job_sweeper_contract.py` with the project-local Python 3.11
environment and portable PostgreSQL runtime. The selection passed `15` tests
in `41.75` seconds. This reconfirms existing publication idempotency,
terminal-job, cleanup, stale-expiry, and duplicate-sweeper controls only.
The active worker still does not consume the source-owned
`document-extraction-manifest-v1` or carry `source_version_id`,
`extraction_run_id`, and canonical manifest-hash lineage; partial canonical
manifest replay and source-owner recovery remain unqualified. No database,
active edge, private data, provider, or implementation status was changed.

## Current-head page-memory qualification recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`46cff4b6` reran the existing page-memory retrieval, page-tagger,
node-assembler, and navigation contract selection with the project-local
Python 3.11 environment and portable PostgreSQL runtime. The selection passed
`31` tests in `4.26` seconds. This reconfirms mechanical page-memory,
locator/hydration, navigation, and node-assembly behavior only. It does not
establish canonical MinerU manifest consumption, source/version or
extraction-run lineage, native-source or semantic gold, source sufficiency,
hard deletion, RA acceptance, or runtime-edge qualification. No database,
active edge, private data, provider, or implementation status was changed.

## Current-head hierarchy and citation contract recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`d5c12c70` reran a focused synthetic contract selection covering
`test_codex_document_tree_contract.py`,
`test_codex_block_normalizer_contract.py`,
`test_knowledge_retrieval_result_v1_contract.py`, and
`test_codex_review_package_contract.py`. All `36` tests passed in `3.84`
seconds with the project-local Python 3.11 environment.

The selection reconfirms document hierarchy and nearest-section paths, block
normalization, table/image provenance references, canonical retrieval-result
field boundaries, and review-package contract behavior. It is mechanical
current-head evidence only; it does not establish cross-document semantic
graph correctness, native-source or human gold, source sufficiency, active
canonical-manifest consumption, RA acceptance, or runtime-edge qualification.
No database, active edge, private data, provider, or implementation status was
changed.

## Cross-document graph coverage boundary audit

On 2026-07-19, a follow-up read-only current-tree search superseded the earlier
statement that no graph implementation existed. Current head `67d7fc0a` contains
`shared.services.retrieval.graph.service.DocumentGraphService`; the normal job
publication finalizer calls it for a non-duplicate document publication. The
writer creates document-level `GraphNode` records and keyword/entity-overlap
`GraphEdge` records, and `agentic.discovery.tools` reaches
`build_knowledge_map_overview`, which reads document graph-node summaries for
file selection. The source therefore has a real graph write path and a bounded
graph-state read consumer.

The current graph is not a canonical MinerU manifest or native-locator graph:
the writer stores document-level keywords/entities, summaries, counts, and
document references, with no producer extraction-block identity, source
version, native page locator, or table/image locator. `GraphQueryService` exists
as a read-side lexical helper but has no non-test caller in the inspected
application tree; agentic discovery reads `GraphNode` summaries rather than
traversing `GraphEdge` relations. Existing contract coverage found graph-row
cleanup/count assertions in the document archive test, but no focused semantic
link-quality, isolation, stale-version, or graph-deletion qualification suite.

The corrected disposition is therefore `partial_mechanical_only` for graph
implementation/wiring and `not_assessed` for cross-document semantic
correctness, isolation, stale/deletion behavior, and native-locator support.
This correction is source-traceability evidence only; no implementation,
database, active edge, private data, provider, or runtime status was changed.

## Current-head D5/D6 manifest-to-result route audit

The same current-head source audit traced the active parse-to-retrieval route.
`ParseOutput` carries only `output_dir` and `parsed_df`; the worker's
`build_parse_result_package` immediately converts that dataframe to chunks.
The local MinerU seam validates a `knowhere-mineru-artifacts/1.0`
`mineru_manifest.json`, but `parse_via_local` publishes only `full.md`, images,
and a sanitized log, then removes the temporary artifact root. The validated
manifest and producer block identity are not carried into `ParseOutput`, the
chunk package, or the normal retrieval response. The cloud MinerU polling path
also materializes the result ZIP into the same output boundary without a
source-owned canonical manifest consumer.

The opt-in `knowledge-retrieval-result-v1` serializer still requires explicit
source/version, memory/configuration, producer block, page, and native-reference
context; its module documentation confirms that normal retrieval routes do not
call it. The active public response projection instead exposes database
`document_id`/`chunk_id`/section fields and derivative asset URLs. This closes
only the route-level absence/ownership characterization: canonical manifest
consumption, source/version/extraction-run lineage, native locator mapping,
idempotency, stale/deletion behavior, RA acceptance, and D5/D6 promotion remain
deferred. No implementation, database, active edge, private data, provider, or
runtime status was changed.

## Current-head local-MinerU preflight, capacity, and provider boundary recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`0d25367e` reran the existing local-MinerU boundary selections
`test_mineru_runtime_preflight_contract.py`,
`test_mineru_local_capacity_contract.py`, and
`test_mineru_provider_contract.py` with the project-local Python 3.11 worker
environment. All `35` tests passed in `2.38` seconds.

The selection reconfirms cloud-mode bypass of local probes, content-free local
runtime preflight and stable failure codes, offline argv construction,
temporary-path cleanup checks, bounded local capacity admission and release,
local/cloud provider separation, partial-work cleanup, allowlisted provider
observations, and fail-closed local-provider behavior without cloud fallback.
The tests use synthetic temporary paths and stubbed commands; they do not
start MinerU, initialize a model, process a source document, contact a
provider, or exercise the active edge. This is mechanical safety and
configuration-boundary evidence only; local production parsing,
canonical-manifest lineage, native/semantic gold, no-egress enforcement,
source sufficiency, and WP-03/WP-05 qualification remain deferred. No
implementation, database, active edge, private data, provider, or runtime
status was changed.

## Current-head API retrieval isolation and runner-boundary recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`95f59f2e` reran the existing API retrieval contract suite
`apps/api/tests/contract/test_retrieval_contract.py` with the repository-root
locked `uv` environment (`uv run --locked`), the portable PostgreSQL runtime,
and the test fixture's fake Redis boundary. All `15` tests passed in `110.06`
seconds; the run reported `12` existing deprecation warnings.

The selection reconfirms authenticated user and namespace isolation, default
namespace behavior, empty-query handling, classic top-k routing, agentic
root/discovery reference projection, table-artifact exclusion from VLM input,
out-of-scope reference rejection, same-chunk-id disambiguation across
documents and sections, request validation, and document/section exclusion
filters.

An earlier invocation with the worker-only `.qa` Python environment failed
before application startup because that environment does not include the API
package dependency `stripe==13.0.1`. The repository-root `uv` workspace
environment already contains the declared dependency; rerunning with the
canonical project command passed. This is an environment-runner boundary,
not a retrieval regression or a source dependency change. The evidence is
mechanical and synthetic only; canonical MinerU manifest publication,
source/version lineage, ranked production top-N sufficiency, semantic/native
gold, RA locators, and WP-04/WP-06 qualification remain deferred. No
implementation, database, active edge, private data, provider, or runtime
status was changed.

## Current-head table export and fidelity-boundary recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`5d2b14cf` reran the existing `test_codex_table_export_contract.py` selection
with the project-local Python 3.11 worker environment. All `9` tests passed in
`0.81` seconds.

The selection reconfirms deterministic HTML/CSV export for simple, nested,
multiple, rowspan, and colspan tables; invalid-HTML preservation; caption,
footnote, and fidelity metadata; deterministic CSV paths; formula/Unicode
retention; and copying/linking of an existing MinerU table image. Complex
rowspan/colspan or nested layouts remain explicitly marked lossy and are not
treated as lossless semantic table evidence. This is a mechanical artifact
contract only; it does not establish native-source or human semantic gold,
critical-cell meaning, canonical manifest lineage, source sufficiency, RA
acceptance, or WP-06 qualification. No implementation, database, active edge,
private data, provider, or runtime status was changed.

## Windows PostgreSQL test-preflight discovery boundary

On 2026-07-19, the repository's official API test-environment preflight was
run with the locked root `uv` environment. All four required Python modules
were importable, but the preflight exited with six missing PostgreSQL checks
(`initdb`, `pg_ctl`, `postgres`, `pg_config`, `uuid-ossp`, and `pg_trgm`). A
direct filesystem check confirmed that PostgreSQL 15.18 and both extension
control files exist under the installed portable runtime. The shared
`find_executable()` helper resolves `pg_ctl.exe`, `postgres.exe`, and
`pg_config.exe`, but returns no result for the extensionless names used by
the preflight on Windows.

This is an existing Windows executable-suffix discovery limitation, not a
missing installation: the API retrieval and worker contract selections used
the verified portable PostgreSQL executable and passed. No executable shim,
source change, database change, or runtime status change was made; the
preflight compatibility gap remains recorded for a separately authorized
implementation slice.

## Current-head review CLI, batch-validation, and evidence-renderer recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`0aec7ae7` reran the existing review/batch boundary selection consisting of
`test_codex_batch_validation_contract.py`,
`test_codex_review_cli_contract.py`, and
`test_agentic_evidence_renderer_contract.py`. The selection passed `18` tests
in `1.36` seconds and recorded `1` skip because Windows symlink creation
requires a privilege not held by the test process.

The selection reconfirms safe relative validation-corpus resolution,
rejection of unsafe/missing records and tamper, ordered private report output,
offline sequential CLI defaults, traceback-free local-MinerU failure
reporting, and page/table evidence rendering through summaries and asset URLs
without inlining table HTML. The symlink-escape branch remains unexecuted on
this host; it is not treated as a pass. This is synthetic offline contract
evidence only and does not establish provider execution, private-source
handling, native/semantic gold, source sufficiency, RA acceptance, or
qualification. No implementation, database, active edge, private data,
provider, or runtime status was changed.

## Current-head D2 telemetry and offline-verifier contract recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`80abaad2` reran the API self-hosted telemetry contract suite and the worker
offline-verifier contract suite. The telemetry selection passed `23` tests in
`0.91` seconds; the offline-verifier selection passed `5` tests in `1.11`
seconds.

The telemetry contracts reconfirm installation identity handling,
allowlisting/removal of unknown, non-scalar, and sensitive properties,
startup/shutdown/heartbeat events, aggregate/request metrics, batching,
flushing, and explicit disable/override behavior. The offline-verifier
contracts reconfirm non-administrator fail-closed behavior, both executable
rule requests, offline environment/attestation output, and cleanup/failure
handling using a recorded `netsh` double. These are application-side and
synthetic contract observations only; no host firewall rule was installed,
no external telemetry destination was contacted, and D2 host-level egress,
retention, credential, and runtime controls remain `blocked`. No
implementation, database, active edge, private data, provider, or runtime
status was changed.

## Current-source-head API retrieval isolation recheck

On 2026-07-19, the current qualification branch head `b8de6e26` was checked
against its runtime/source head `67d7fc0a`; the only intervening change is the
qualification record itself. The existing
`apps/api/tests/contract/test_retrieval_contract.py` selection was rerun with
the project `.venv` and the verified portable PostgreSQL runtime. All `15`
tests passed in `118.56` seconds, with `12` existing deprecation warnings.

The selection reconfirms authenticated user and namespace isolation,
namespace defaults, empty-query and top-k routing, agentic reference
projection, table-artifact exclusion, out-of-scope reference rejection,
same-chunk-id disambiguation, request validation, and document/section
filters. This is direct current-source mechanical evidence only; it does not
establish canonical MinerU manifest lineage, production ranking sufficiency,
native or semantic gold, source sufficiency, hard deletion, RA acceptance, or
WP-04/WP-06 qualification. No provider, private data, active edge, or runtime
promotion was used.

## Current-source document lifecycle and graph-row recheck

On 2026-07-19, the current qualification branch head `a8d7eccb` was checked
against runtime/source head `67d7fc0a`; the only intervening change remains the
qualification record. The existing
`apps/api/tests/contract/test_documents_contract.py` selection was rerun with
the project `.venv` and portable PostgreSQL runtime. All `17` tests passed in
`137.19` seconds.

The selection reconfirms document namespace/list behavior, revision and page
citation projections, table/image asset boundaries, archived-document
handling, and the canonical archive route's bounded graph-node/edge cleanup
and peer-node preservation assertions. These are synthetic API and database
contract observations, not graph semantic link-quality, all-route isolation,
stale-version, deletion-completeness, native-locator, source-sufficiency, or
RA acceptance qualification. No provider, private data, active edge, or
runtime promotion was used.

## Current-source review and offline-verifier recheck

On 2026-07-19, the current qualification branch head `444a5c52` was checked
against runtime/source head `67d7fc0a`; the only intervening change remains
qualification documentation. The existing review/batch/evidence-renderer and
offline-verifier selections passed together with `23` tests and `1` skip in
`1.39` seconds. The skip is the Windows symlink-privilege branch and is not
counted as a pass.

The selections reconfirm safe relative validation-corpus resolution, tamper
and missing-record rejection, ordered private-report output, offline CLI
defaults, traceback-free local-MinerU failure reporting, evidence rendering,
and fail-closed offline-verifier behavior with bounded environment/attestation
output. This is synthetic offline contract evidence only; no host firewall
rule, external telemetry destination, provider, private data, active edge,
native/gold decision, or runtime promotion was used.

## Current-source canonical retrieval-result serializer recheck

On 2026-07-19, the current qualification branch head `0e841e38` was checked
against runtime/source head `67d7fc0a`; the intervening changes remain
qualification documentation only. The existing shared serializer and worker
`knowledge-retrieval-result-v1` contract selections passed `7/7` tests in
`0.10` seconds.

The selection reconfirms explicit source/version, producer-block, page, native
reference, table/image linkage, score, and fail-closed field-boundary rules.
This is opt-in serializer evidence only: the normal retrieval route still does
not invoke it, no canonical result was accepted by RA, and no provider,
private data, active edge, or runtime promotion was used.

## Current-source ancillary API contract recheck

On 2026-07-19, the current qualification branch head `7c3ae6cd` was checked
against runtime/source head `67d7fc0a`; the intervening changes remain
qualification documentation only. Using the repository-root locked `uv`
environment (`uv run --locked`) and the existing portable PostgreSQL test
runtime, the ancillary API contract selections passed as follows:

| Selection | Result |
|---|---:|
| Agentic discovery selection, page-memory/parse-track, chunk/document-path, and legacy evidence renderer | `49 passed` in `5.24` seconds; `1` existing duplicate OpenAPI operation-ID warning |
| Job creation contract | `24 passed` in `147.83` seconds |

The selections reconfirm discovery-action/rejection precedence, parse-track and
public-route boundaries, legacy path compatibility, evidence rendering, v2
job/document/retrieval creation, authorization and namespace checks, archived
document rejection, URL/private-network rejection, and retryable upload
transitions. The worker-only `.qa` environment was not used for API imports
because it intentionally omits the API-only `stripe==13.0.1` dependency; the
canonical project environment contains the declared dependency. These are
synthetic API contract observations using disposable test resources only; no
provider, private data, active edge, canonical MinerU manifest consumption,
native/semantic gold, source sufficiency, RA acceptance, or runtime promotion
was performed, and the qualification disposition remains `deferred`.

## Current-source job, health, demo, and telemetry contract recheck

On 2026-07-19, the current qualification branch head `4d698ad8` was checked
against runtime/source head `67d7fc0a`; the intervening changes remain
qualification documentation only. Using the repository-root locked `uv`
environment (`uv run --locked`) and the existing disposable PostgreSQL test
runtime, the existing job-read, health, demo-document, and self-hosted
telemetry contract selections passed `37` tests in `95.59` seconds, with `2`
existing demo-route deprecation warnings.

The selections reconfirm job listing/detail ownership and date filtering,
health bootstrap, demo catalog citation/materialization and no-credit/no-parse
behavior, telemetry installation identity, allowlists, sensitive-property
removal, batching, flush/stop behavior, and explicit disable/override paths.
Telemetry delivery assertions use contract doubles/local boundaries; no
external telemetry destination was contacted. This is synthetic API and
application-side contract evidence only; it does not establish host-level
egress denial, telemetry retention/exhaustiveness, canonical MinerU manifest
lineage, native/semantic gold, source sufficiency, deletion, RA acceptance,
provider execution, active-edge promotion, or qualification, and the
disposition remains `deferred`.

## Current-source worker MinerU boundary and package integration recheck

On 2026-07-19, the current qualification worktree at Knowhere revision
`2b1cf3fa` was checked with the repository-root locked offline `uv` environment.
The existing worker artifact/provider/local-capacity/local-process contract
selections and the static PDF/DOCX package integration selections completed
with `46 passed, 2 skipped` in `4.21` seconds.

The passing selection reconfirms artifact JSON/schema, relative-path and
symlink-escape handling where the host permits symlink creation, hash and
source-identity validation, local-provider configuration and no-cloud-fallback
behavior, capacity leasing, process argument/timeout/log bounds, and static
PDF/DOCX package construction and reproducibility. One skip was the Windows
symlink branch because the test account lacks the privilege required to create
the link; the other was the explicitly opt-in model-backed local MinerU E2E
(`RUN_LOCAL_MINERU_E2E=1`), which was not enabled. No model-backed run,
provider, private source, external network, active edge, database mutation, or
runtime promotion was used. This is mechanical worker and synthetic local
package evidence only; it does not qualify real local MinerU execution,
producer-to-Knowhere canonical manifest consumption, semantic/native gold,
source sufficiency, deletion completeness, RA acceptance, or D3/D4
qualification, and the disposition remains `deferred`.

## Opt-in local MinerU synthetic E2E seam recheck

On 2026-07-19, the previously disabled model-backed local seam was exercised
with public/synthetic inputs only. The outer Knowhere command used the locked
project environment with `--frozen --offline`; the child MinerU runner used the
same local `uv` executable with `UV_OFFLINE=1`, `UV_FROZEN=1`, the MinerU
repository path, and the test's `--offline` application flag. The selection
was:

```text
apps/worker/tests/integration/test_local_mineru_provider_integration.py
apps/worker/tests/integration/test_codex_pdf_package_integration.py
```

The result was `3 passed` in `54.83` seconds. The run used the existing public
MinerU `tests/unittest/pdfs/test.pdf` fixture and a generated synthetic PDF.
The provider-seam test confirmed that the local provider reached the standard
PDF path, produced `full.md` and a bounded log, and made no cloud-parser call.
The package test confirmed an offline-requested manifest with no `server_url`
and a non-empty block result. Pytest temporary outputs were outside the
repository; no provider, browser, or private source was used, and external
network interaction was outside the test scope. Host-level egress remains
unverified.

This is model-backed local execution and application/offline-runner evidence
only. The offline flags do not prove host-level egress denial, and the result
does not qualify model identity/legal provenance, semantic/native gold,
critical-token meaning, source sufficiency, canonical MinerU manifest lineage,
active edge use, RA acceptance, or D2/D3/D4 qualification. The qualification
disposition remains `deferred`; no implementation, database, active edge,
private-data, provider, or runtime promotion occurred.

## Current source provider and telemetry boundary audit

On 2026-07-19, a read-only source/configuration audit was performed against
the current Knowhere qualification worktree revision
`43b8d788694056444f907fc9ce1965e298feb8b5`. The repository carries Apache 2.0
`LICENSE` (SHA-256
`1eb85fc97224598dad1852b5d6483bbcf0aa8608790dcc657a5a2a761ae9c8c6`) and a
`NOTICE` file (SHA-256
`b2c977015e2346a143dc69839905d0d30d884c0513e8639575c7d4522b897f03`).

The source README and environment examples identify external dependency
surfaces: DeepSeek, Qwen-VL, OpenAI, DashScope, Zhipu, and Volcengine provider
keys/URLs; `MINERU_API_KEYS` and a vision-capable provider for image/OCR paths;
S3-compatible storage; and QStash/webhook endpoints. The API environment
example sets `TELEMETRY_ENABLED=true` by default and documents a PostHog host,
project key, installation ID, and aggregate/heartbeat telemetry settings. The
README describes the telemetry as anonymous and allowlisted, but source
configuration facts are not host-level egress or retention evidence.

This audit did not load credentials, contact a provider, send telemetry, read
private source data, or change configuration/runtime state. It identifies the
outbound and model-provider surfaces that must remain explicitly controlled for
a private-local profile; D2 host-level egress and telemetry qualification,
provider authorization, private shadow-pilot acceptance, native/semantic gold,
source sufficiency, RA acceptance, and D4/D5/D6 promotion remain deferred.

## Current Docker and host-boundary recheck

On 2026-07-19, a read-only check of the local qualification runtime confirmed
Docker Engine client/server `29.6.1` and healthy containers for the MinerU API,
PostgreSQL, Redis, and LocalStack services. Host-wide published bindings remain
present for the service ports, and both active Compose networks remain
non-internal bridge networks. The inspected containers retain writable roots,
unbounded memory/CPU/pids settings, and LocalStack retains a read-write Docker
socket mount.

All enabled Windows firewall profiles still report `NotConfigured` default
inbound and outbound actions. This is host/runtime-boundary evidence only; no
firewall, Docker, source, provider, telemetry, private-data, or database state
was changed. D2 remains `blocked`, and the qualification disposition remains
`deferred`; no runtime promotion, active edge, provider execution, or RA
acceptance is inferred.

## Current-head parser-adjacent contract recheck

On 2026-07-19, the existing offline Knowhere contract selections for
cross-page table merging, table caption/footnote export, block normalization,
and DOCX duplicate-image summary handling passed `45` tests in `3.93` seconds.
These tests provide mechanical coverage for preserving explicit caption,
footnote, table-continuation, and duplicate-asset metadata at the application
boundary. They do not prove MinerU parser meaning, native-source fidelity,
critical-cell gold, retrieval top-N meaning, source sufficiency, host egress,
deletion, or RA acceptance. The qualification disposition remains `deferred`;
no implementation, database, active edge, provider, or private-data status
changed.

## Fixture-batch reproducibility boundary

On 2026-07-19, a read-only search of the tracked Knowhere/worker test and
fixture tree found the recorded `EXT-WP03` batch identifiers only in
qualification prose. No checked-in complete batch command manifest, runner, or
fixture/hash bundle was found for independently reproducing the 12-input
fixture-family handoff; temporary generated outputs from that run had already
been removed. Existing individual synthetic fixture generators remain useful
inputs, but they do not prove exact-batch reproducibility.

This is a traceability/reproducibility gap, not permission to add new shared
machinery during the implementation pause. The prior batch remains bounded
historical mechanical evidence; native/semantic gold, active retrieval,
source sufficiency, and qualification remain deferred. No implementation,
database, provider, private-data, active-edge, or runtime status changed.

## Current-state source-owner packet portability recheck (2026-07-19)

An independent read-only recomputation of the private synthetic handoff packet
confirmed `24/24` declared artifacts present with matching size and SHA-256.
The only package file outside the artifact list was the self-describing
`metadata/manifest.json`. The native source hash still matched the manifest.

The structured block file contained `18` parseable lines. All `9` table
references resolved from the package root, but the single image reference
`images/c0fe4015d52e08dcc84cb5e0bad1feb22564800020e0e5fdd53e489644d04888.jpg`
did not; the copied image remains only under the previously recorded alternate
asset/raw paths. The package contains `0` render pages while the adjacent
native render directory contains `2` pages. `offline_verified` remains
`false`, normalized-PDF mapping remains `unmapped`, and no owner category was
adjudicated. The packet remains `pending_human_adjudication` /
`unverified` with qualification `deferred`; no locator, artifact, database,
provider, private-data, implementation, or runtime-edge state changed.

## Current canonical schema SHA recheck

The current `schemas/knowledge-retrieval-result-v1.schema.json` is
byte-identical to the RA compatibility profile's frozen SHA-256
`54307e0c42ebf737af897b691badda18fd6c673f64aef3cf7eb961dab0123c4a` at
`71ff7fc1128743a9135f65b110d49504768c08b3`, and that commit is an ancestor of
the current qualification head. This confirms contract-byte continuity only;
the source-owner qualification, runtime/edge promotion, native/semantic gold,
RA acceptance, and release provenance gates remain open. No schema, source,
runtime, provider, private-data, or qualification status changed.

## Current qualification-head continuity recheck (2026-07-19)

The previously recorded runtime/source head
`67d7fc0a1fd7893aa18c679d2b59c832874b6ac8` remains an ancestor of the current
qualification head `546da1aad5b570f431463eae0a5fa89e62a8893e`. The tracked diff
between those heads contains only this qualification record
(`334` lines changed); the intervening descendants are documentation-only
qualification updates. The branch remains `0` commits ahead/behind its tracked
remote, with the existing untracked `.qa/` directory preserved and untouched.

The locally available upstream comparison object and fork baseline remain
unchanged; no fetch, sync, merge, rebase, cherry-pick, provider operation, or
private-data processing was performed. The source-owner, native/semantic gold,
runtime-edge, RA acceptance, and release-provenance gates remain deferred.

## Current post-change package portability recheck (2026-07-19)

After the package exporter portability fix at Knowhere revision
`99d8ca4b53666674776917782d9d9a3d0fdf7ed5`, the original synthetic handoff
packet was left untouched and a new local/private verification output was
generated from the same native source. The new packet contains `2` rendered
pages and `18` structured blocks. Its single image asset now uses the
package-root locator
`assets/c0fe4015d52e08dcc84cb5e0bad1feb22564800020e0e5fdd53e489644d04888.jpg`
while preserving the producer path under `source_relative_path` as
`images/c0fe4015d52e08dcc84cb5e0bad1feb22564800020e0e5fdd53e489644d04888.jpg`.

All `26/26` manifest-declared artifacts were present with matching size and
SHA-256. This confirms the exporter now produces a portable package-root image
locator for the tested synthetic packet; it does not establish parser meaning,
native/semantic gold, source sufficiency, owner adjudication, retrieval
quality, host egress control, or RA acceptance. Offline verification remains
`false`, normalized-PDF mapping remains `unmapped`, and the qualification
disposition remains `deferred`; no active edge, provider, private-data,
database, or release-promotion status changed.

## Current local-private telemetry configuration hardening (2026-07-19)

Knowhere revision `4feb9c61b2e6b8f7163f23b69f9b82c7f1a3fd31` changes the existing
`apps/api/.env.example` local-copy sample to declare
`TELEMETRY_ENABLED=false` explicitly. A new contract assertion fixes that
sample boundary, and the existing self-hosted telemetry contract suite passed
`24` tests. The application `BaseConfig` fallback and ADR-0004 telemetry
schema/default-on policy were not changed; this is a local configuration
hardening measure, not proof that every deployment loads the sample file.

The change reduces accidental outbound telemetry when a private/local operator
starts from the repository's API example, but it does not prove host-level
egress denial, firewall policy, external sink retention, or full D2 runtime
qualification. The D2 evidence disposition remains
`blocked`/`partial_mechanical_only`, and no provider, private-data, active-edge,
source-sufficiency, or RA status changed.

## Current local Compose boundary hardening (2026-07-19)

Knowhere revision `f96c874d6f9f74e8a5df2f8d0e41bd0f9b4d16f3` updates the existing
local-development Compose file so PostgreSQL, Redis, and LocalStack published
ports bind to loopback only. The same three services now declare explicit
CPU, memory, and PID ceilings. Two new Compose contract tests passed, and
`docker compose config --quiet` parsed the file successfully.

This is deployment-configuration hardening only. The local bridge network,
development PostgreSQL credential handling, LocalStack Docker-socket mount,
host-level egress policy, and production deployment controls remain open and
were not represented as passed. D2 remains `blocked`; no runtime promotion,
provider execution, private-data processing, source-sufficiency conclusion, or
RA acceptance changed.

## Current local Compose internal-network hardening (2026-07-19)

Knowhere revision `c9311c24c4d680125b4ea9e89ddc03dd3dd6f805` extends the
existing local-development Compose contract by marking `knowhere_network` as
`internal: true`. The boundary contract now passes for loopback-only published
ports, the declared resource ceilings, and the internal-network flag; the
Compose configuration parser also passes.

This declaration has not been applied to the already-running containers in
the local Docker Engine, which were intentionally left untouched. It is
therefore configuration evidence only, not host-level egress proof. The
development credential, LocalStack Docker-socket, current runtime network,
firewall, and production deployment controls remain open; D2 stays `blocked`
and no runtime edge, provider, private-data, source-sufficiency, or RA status
changed.

## Current Docker deployment-application boundary (2026-07-19)

A read-only Docker inspect found the running `knowhere_postgres`,
`knowhere_redis`, and `knowhere_localstack` containers owned by the separate
`ra-d2-knowhere-20260718` Compose project. Their named data volumes were
present, but the running containers still exposed `5432`, `6379`, and `4566`
on `0.0.0.0`/IPv6, and reported zero memory, CPU, and PID limits. The
configuration hardening above was not applied to them because their Compose
project identity does not match the current local-dev file; no stop, remove,
recreate, or volume operation was issued.

This confirms the distinction between tracked deployment configuration and
runtime state. D2 host/runtime hardening remains unqualified; no data,
provider, active edge, source-sufficiency, or RA status changed.

## Current local Compose host-access correction (2026-07-19)

The `internal: true` default-dev experiment was reproduced and then corrected
forward at Knowhere revision `ae7645a9a909c40e2b7a5f01e4420fa6c99b7a6e`.
Docker Desktop kept the containers healthy and retained the resource limits,
but refused host connections to all three published ports while the network
was internal; container-local PostgreSQL and Redis probes still passed. The
default local-dev network therefore no longer declares `internal: true`, and
the contract now protects host accessibility for the host-run API/worker.

The same `ra-d2-knowhere-20260718` project was reconciled with the corrected
configuration without removing its named volumes. Fresh runtime checks showed
all three services healthy, loopback connectivity on ports `5432`, `6379`, and
`4566`, LocalStack HTTP `200`, PostgreSQL/Redis service probes passing,
`network_internal=false`, and the declared memory/CPU/PID limits active. This
does not establish host-level egress denial; an internal network remains an
isolated D2-harness control rather than a default host-integrated dev setting.
D2 remains `blocked`, with no provider, private-data, active-edge,
source-sufficiency, or RA status change.

## Bounded canonical-manifest consumer seam (2026-07-19)

Knowhere revision `8364d7a7` adds an opt-in consumer seam for the existing
MinerU source-owned `document-extraction-manifest-v1` output. The local
review-package runner now passes explicit source, source-version, and
extraction-run identifiers to the paired MinerU CLI, fails closed when the
canonical output is absent or mismatched, verifies the input SHA-256 and every
declared output artifact hash, and preserves the canonical manifest plus its
lineage identifiers in the review package.

The bounded contract tests passed `32` tests with `1` expected skip; the
relevant Ruff check passed; and a real public synthetic manifest from the
MinerU `.qa` smoke output was consumed read-only with the legacy artifact
contract, `7` canonical outputs, matching source SHA-256, and both producer
boundary flags set to `true`. This is mechanical cross-edge evidence only. It
does not add canonical consumption to the standard `parse_task` path, and it
does not establish source-owner review, native or semantic gold, source
sufficiency, retrieval quality, host egress denial, runtime-edge qualification,
provider approval, or RA acceptance. D5/source-owner qualification remains
deferred; the default exporter path remains unchanged.

## Current paired local MinerU seam recheck (2026-07-19)

At Knowhere revision `73acff28893ca9135a5cf1d7045ca037156b4d94`, the bounded
local MinerU runtime, capacity, provider, artifact, process, and integration
selection passed `54` tests with `2` expected skips. The skips were the Windows
symlink-creation privilege check and the opt-in real seam when it was excluded
from the contract selection. The paired MinerU producer revision was
`de329b20325a801c7771f9a142748502402312e6`; its manifest and Knowhere adapter
contract selection passed `18` tests.

The explicit public-fixture local seam then passed `1` test in `37.41` seconds.
It exercised the standard PDF provider boundary, produced `full.md` and the
sanitized log, made zero cloud-sentinel calls, and left no local temporary-run
directory. The run used the existing local/offline configuration and did not
transmit private data or start an external provider.

This expands current paired mechanical/runtime-seam evidence only. It does not
qualify the MinerU parser profiles, establish native or semantic gold, prove
host-level egress denial, promote the runtime edge, authorize provider or
private-data execution, establish source sufficiency, or change RA disposition.
D5/source-owner qualification and D2 runtime-edge qualification remain
deferred/blocked as previously recorded; the default ingestion path remains
unchanged.

## Current-head retrieval/document contract recheck (2026-07-20)

At the current qualification checkout revision
`02f8a0cc85a0fba0d893f2958cff9fe03520dc08`, the offline contract selection
`apps/api/tests/contract/test_retrieval_contract.py` and
`apps/api/tests/contract/test_documents_contract.py` passed `32` tests
(`15` retrieval and `17` document tests) in `152.96` seconds. The run
used the local locked environment and `TELEMETRY_ENABLED=false`; the only
reported findings were `12` existing deprecation warnings in the retrieval
route.

This is current-head synthetic contract evidence for API/storage/retrieval
mechanics only. It does not establish native or semantic gold, top-N
qualification, hard deletion, host-level egress denial, source sufficiency,
runtime-edge promotion, provider approval, private-data processing, or RA
acceptance. The retrieval qualification disposition remains `deferred`.

## Current public synthetic local MinerU E2E recheck (2026-07-20)

At Knowhere revision `087154660d37f83ac33399306d1a60fc4c7c8e13`, paired with
MinerU revision `9bd964e03e638ebdd533b9c8fdc24325552b4251`, the explicit
offline local MinerU selection passed `3` tests in `55.76` seconds. It covered
the standard PDF provider seam and the Codex PDF review-package export using
the public synthetic fixture/generated PDF; the provider test observed no
cloud fallback calls, and the package assertions preserved offline execution
and omitted a server URL. The targeted Knowhere and MinerU Ruff checks also
passed.

This is current public synthetic mechanical/runtime-seam evidence only. It does
not qualify MinerU parser profiles, native or semantic gold, source-owner
review, host-level egress denial, D2/runtime edge promotion, source sufficiency,
provider approval, private-data execution, or RA acceptance. The standard
Knowhere ingestion path and the qualification gates remain unchanged.

## Current-head D2 runtime-control contract recheck (2026-07-20)

At the current qualification checkout revision
`30e67c5af5f68b4d9d1dab86b3ecc7b2cd741eda`, the existing local-development
Compose and self-hosted telemetry contract selection passed `28` tests in
`0.48` seconds. The selection covered loopback-only published ports, declared
memory/CPU/PID ceilings, the intentional non-internal host-integrated bridge,
the loopback/secret-free launcher boundary, telemetry sanitization, identity,
startup/shutdown, disable/override behavior, and the local `.env.example`
opt-out declaration.

Static current-head inspection confirms that the local Compose file still binds
PostgreSQL, Redis, and LocalStack to loopback and declares resource limits, but
the default network remains a non-internal bridge so the host-run API/worker can
reach its dependencies. `BaseConfig` still falls back to telemetry enabled when
the environment does not explicitly set `TELEMETRY_ENABLED`; the existing
startup path returns before identity/client construction when the flag is false.

This is application/configuration contract evidence only. No Docker project was
reconciled, no external sink or host firewall was contacted, and no telemetry
delivery, default-deny egress, secret isolation, runtime enforcement, or
production deployment control was proven. D2 remains `blocked`; no provider,
private-data, active-edge, source-sufficiency, qualification, or RA acceptance
status changed.

## Current-head page-memory retrieval contract recheck (2026-07-20)

At the current qualification checkout revision
`dd09cc5c36f47c022b43c9c97cd09c04fb0f34b4`, the existing
`apps/worker/tests/contract/test_page_memory_retrieval_contract.py` selection
passed `12` tests in `1.93` seconds under locked offline execution with
`TELEMETRY_ENABLED=false`. The selection covered page-node search text,
summary-based page and table result assembly, page-number URL generation,
page-citation asset precedence over lazy PDF cropping, safe artifact-reference
allowlisting, referenced-artifact upload filtering, cache reuse, missing-source
handling, and referenced-chunk page asset hydration. The targeted Ruff check
also passed.

This is current-head worker retrieval/hydration contract evidence only. It does
not establish producer-owned canonical-result emission, native or semantic
gold, ranked top-N meaning preservation, source sufficiency, hard deletion,
host-level egress denial, runtime-edge promotion, provider approval,
private-data processing, or RA acceptance. The retrieval qualification
disposition remains `deferred`; no edge or runtime status changed.

## Current-head page-memory parse-track/navigation contract recheck (2026-07-20)

At Knowhere revision `bd4fabd831254c588dc0257dd3dd5ef9ee59a7e3`, the existing
page-memory parse-track and navigation contract selections passed `20` tests
(`18` parse-track and `2` navigation) under locked offline execution with
`TELEMETRY_ENABLED=false`. The selections covered v1/v2 parse-track routing,
fail-closed public selectors and unknown fields, route/OpenAPI registration,
guest route policy, system-rule precedence, path-based leaf summaries, page
counts, and chunk-path navigation. The targeted Ruff check passed. One
existing FastAPI duplicate-operation-ID warning was reported during the
OpenAPI test.

This remains worker/API contract evidence only. It does not establish
producer-owned canonical-result emission, native or semantic gold, ranked
top-N meaning preservation, source sufficiency, deletion, D2 egress control,
runtime-edge promotion, provider/private-data authorization, or RA
acceptance. Retrieval qualification remains `deferred` and no edge status
changed.
