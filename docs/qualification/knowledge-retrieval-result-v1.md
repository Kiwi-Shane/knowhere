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
