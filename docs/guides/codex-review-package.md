# Build and inspect a local Codex review package

This standalone workflow converts one local PDF or DOCX into a portable review
directory. It runs MinerU as a local child process and does not require the
Knowhere API, worker, Celery, PostgreSQL, Redis, S3, or LocalStack services. It
does not replace Knowhere's production PDF or DOCX ingestion paths.

The source-owned canonical retrieval-result contract is
`schemas/knowledge-retrieval-result-v1.schema.json`. The review package
manifest described by this guide remains a separate derivative-package
baseline; it is not treated as a qualified retrieval-result payload. See
`docs/qualification/knowledge-retrieval-result-v1.md` for the current gate
status. Knowhere also exposes an opt-in pure serializer for an already-ranked
retrieval row, but it requires explicit source-version and native-locator
context and is not called by this review-package builder or the active public
retrieval routes.

## Prerequisites

1. Check out and install the paired MinerU project, including the
   `mineru-knowhere-export` adapter.
2. Pre-download the model files required by the selected backend before a
   strict offline run. The supported MVP PDF backend is `pipeline`; DOCX uses
   MinerU's effective `office` backend. Other non-HTTP backends are not
   qualified here.
3. Install LibreOffice only if DOCX pages must be rendered. Structured DOCX
   export can complete without it when no pages are requested.
4. Ensure sufficient local disk, RAM, and, if used, GPU memory. Requirements
   vary with the selected models, page count, resolution, and document
   complexity. CPU execution can be slower; GPU execution needs compatible
   drivers and runtime. No performance or capacity guarantee is implied.

Application offline flags ask known model libraries not to download and reject
MinerU HTTP-client backends and server URLs. They are not equivalent to a host
firewall or an independently verified network-denial control. Use host or
container network controls when that assurance is required; the manifest keeps
`offline.requested` and `offline.verified` separate.

## Run without Knowhere services

From `knowhere/apps/worker`, run:

```bash
uv run python scripts/export_codex_review_package.py \
  --input /absolute/path/to/source.pdf \
  --output ../../.codex-review/source-pdf \
  --mineru-project /absolute/path/to/MinerU \
  --backend pipeline \
  --method auto \
  --lang en \
  --pages 1,2 \
  --include-table-pages \
  --dpi 200 \
  --offline
```

Paths are passed as an argument list, not a shell command. The output must not
already exist unless `--force` is supplied. On failure, the unfinished package
is removed unless `--keep-work-dir` was requested. Do not place confidential
fixtures or completed review packages in the repository; `.codex-review/` and
`review-package/` are ignored.

For DOCX, `--pages` means pages in the LibreOffice-normalized PDF. MinerU Office
logical pages remain distinct and unmapped. Pagination can change with fonts,
LibreOffice version, operating system, and printer settings.

## Package map

- `native/source.pdf` or `native/source.docx`: authoritative source copy.
- `metadata/manifest.json`: source hash, tool provenance, options, counts,
  limitations, and a hash inventory of package artifacts.
- `structured/blocks.jsonl`: deterministic parser-derived blocks and locators.
- `structured/document_tree.json`: deterministic, navigation-only hierarchy.
- `structured/extraction_findings.jsonl`: extraction and fidelity warnings.
- `derivatives/document.md`: MinerU Markdown derivative.
- `raw/mineru/`: validated MinerU artifacts and original manifest.
- `tables/`: preserved HTML, metadata, source image when available, and
  best-effort CSV derivatives.
- `assets/`: package-root copies of image and chart assets referenced by
  `structured/blocks.jsonl`; these portable references use `assets/...`, while
  `source_relative_path` preserves the producer's original `images/...` path.
- `pages/`: selected lossless PNG page renders.
- `CODEX_REVIEW_INSTRUCTIONS.md`: evidence boundaries for the reviewer.

Image and chart references are rebound to `assets/...` only when the copied
source and package asset both resolve safely inside the package. Absolute,
traversal, or missing asset paths remain unbound and must be treated as an
export warning rather than silently rewritten.

Table HTML is the preserved structural derivative. CSV is explicitly
best-effort: merged cells, row/column spans, nesting, multiple tables, or parser
failures can make it lossy or unavailable. Verify decision-relevant values on
the native source page.

## Provenance and evidence classes

- `parser_extracted` / `source_derivative`: MinerU-extracted text and structure;
  useful for search and navigation, but not a substitute for the source.
- `native_verification_required`: table derivatives and other content whose
  decision-relevant values must be checked against the native document.
- `machine_generated_visual_description` / `navigation_only`: image or chart
  descriptions used to locate content, never as source evidence.
- Normalized PDFs and page PNGs: rendering derivatives. PDF pages retain native
  page numbers; DOCX PNGs use normalized-PDF page numbers.
- The document tree is `navigation_only`; it does not imply approval, status,
  compliance, equivalence, disposition, or a Pass/Fail result.

## Inspect with Codex

Open the completed package directory in Codex and ask it to read
`CODEX_REVIEW_INSTRUCTIONS.md` first. Then inspect
`metadata/manifest.json` for identity and limitations,
`structured/document_tree.json` for navigation, and
`structured/blocks.jsonl` for extracted content. Use table metadata and page
renders to locate evidence, then verify material claims against `native/`.
Check `structured/extraction_findings.jsonl` before relying on any derivative.

## Validate the repository test corpus

The batch validator accepts only named repository roots and corpus-relative PDF
or DOCX paths. It rejects absolute paths, traversal, symlink escapes, duplicate
IDs, unsupported extensions, and missing files. From the Knowhere repository
root on Windows:

```powershell
$env:MINERU_LOCAL_UV_EXECUTABLE = "C:\path\to\uv.exe"
python -m uv run python apps/worker/scripts/validate_codex_export_corpus.py `
  --corpus apps/worker/tests/fixtures/codex_export/validation-corpus.json `
  --output .codex-review/batch-validation `
  --mineru-project C:\path\to\MinerU `
  --repeat 1 --backend pipeline --method auto --dpi 144 --offline --force
```

The two outputs are `validation-report.json` and `validation-report.html`.
They contain source filenames, IDs, tags, hashes, sizes, timings, peak RSS,
package counts, fidelity/finding counters, expected/actual status, and bounded
sanitized errors. They never contain extracted text, table cell values,
absolute paths, environment dumps, credentials, or package contents. Package
artifact hashes are rechecked before a run is counted as completed.

## Externally verify offline execution on Windows

Application offline flags do not prove network denial. The external verifier
requires an elevated Windows token and temporarily installs outbound block
rules for the exact `uv.exe` and MinerU virtual-environment `python.exe`. It
verifies both rules, runs the batch, deletes only its uniquely named rules in a
`finally` path, and then writes a separate attestation:

```powershell
python -m uv run python apps/worker/scripts/verify_codex_export_offline.py `
  --corpus apps/worker/tests/fixtures/codex_export/validation-corpus.json `
  --output .codex-review/offline-validation `
  --mineru-project C:\path\to\MinerU `
  --uv-executable C:\path\to\uv.exe `
  --mineru-python C:\path\to\MinerU\.venv\Scripts\python.exe `
  --attestation .codex-review/offline-attestation.json --force
```

Without elevation it exits before creating rules or an attestation with
`Administrator privileges are required`. A successful external attestation
does not change any package manifest: package-level `offline.verified` remains
false because the enforcement evidence has its own lifecycle and schema.

## Opt in to the production local PDF provider

Production PDF parsing remains cloud-backed by default. Roll out local parsing
explicitly with the paired MinerU checkout and local models already installed:

```dotenv
MINERU_PROVIDER=local
MINERU_LOCAL_PROJECT_PATH=C:\path\to\MinerU
MINERU_LOCAL_UV_EXECUTABLE=C:\path\to\uv.exe
MINERU_LOCAL_SHARD_CONCURRENCY=1
MINERU_LOCAL_MAX_CONCURRENT_JOBS=1
MINERU_LOCAL_ADMISSION_TIMEOUT_SECONDS=30
```

Local mode accepts only a local PDF path, publishes the validated Markdown as
`full.md`, confines copied images, retains the sanitized MinerU log, and removes
raw temporary artifacts. It does not use S3, API keys, or HTTP requests and it
never falls back to cloud after a local failure. DOCX production routing is
unchanged. Keep local shard concurrency at one until capacity testing supports
a higher value; cloud mode continues to use `MINERU_SHARD_CONCURRENCY`.

Before enabling a dedicated local worker, follow the complete
[Local MinerU production canary](local-mineru-production-canary.md). It defines
the content-free preflight, repeat-three acceptance gates, 24-hour observation,
and explicit rollback procedure. External firewall isolation remains the
operator-run BL-001 backlog item and is not implied by application offline mode.

## Opt in to source-owned canonical lineage

The local review-package exporter can optionally request and consume the
source-owned `document-extraction-manifest-v1` emitted by the paired MinerU
checkout. The caller must provide explicit `source_id`, `source_version_id`, and
`extraction_run_id`; Knowhere passes those values to the existing MinerU CLI,
fails closed if the returned manifest is absent or mismatched, and verifies the
input SHA-256 plus every declared output artifact hash before package creation.

```powershell
python apps/worker/scripts/export_codex_review_package.py `
  --input C:\path\to\source.pdf `
  --output C:\path\to\package `
  --mineru-project C:\path\to\MinerU `
  --lang en --offline --canonical-manifest `
  --source-id SRC-EXAMPLE-001 `
  --source-version-id SRC-EXAMPLE-001-V001 `
  --extraction-run-id EXT-EXAMPLE-001
```

When enabled, the canonical manifest is preserved at
`raw/mineru/document-extraction-manifest-v1.json` and its lineage identifiers
are recorded in `metadata/manifest.json`. The producer-owned schema remains the
contract authority; this consumer performs only the cross-edge identity,
boundary, path, and hash checks needed to avoid silently binding the wrong
source run. The default exporter path and the standard `parse_task` ingestion
path remain unchanged.

This option establishes a bounded mechanical consumer seam only. It does not
establish source-owner review, native or semantic gold, source sufficiency,
retrieval quality, offline host denial, runtime-edge qualification, provider
approval, or RA acceptance.

## Security and licensing notes

The adapter validates relative artifact paths, resolves symlinks, verifies
SHA-256 hashes, uses `shell=False`, bounds logs, and redacts common secret
forms. It does not require `MINERU_API_KEYS` or start a MinerU HTTP server.

Knowhere's `LICENSE` and `NOTICE` remain in force. MinerU remains under its own
license and additional terms; no MinerU source is copied into Knowhere. If the
combined result is offered as an online service, evaluate MinerU attribution
and other deployment-specific obligations. This guide is not a legal
conclusion, and deployment-specific legal review may be required.
