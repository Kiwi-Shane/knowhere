# Plan: Remote Parser Input Authorization

## Goal

Close the metadata propagation gap between worker parser orchestration and the
already guarded source-URL download boundary.

## Task 1: Add failing contract coverage

- Assert `load_file_bytes()` forwards a synthetic job authorization record to
  `JobFileStorage.download_file_from_url()`.
- Assert text, image, Markdown, HTML, PPTX, DOCX, and XLSX adapter paths carry
  the same job metadata object.
- Update the existing remote-input storage double for the additive keyword.

## Task 2: Implement the bounded propagation

- Add optional `job_metadata` parameters to the shared worker file loader and
  parser entry points.
- Thread metadata through format adapters, the XLSX wrapper/request, HTML and
  Markdown delegation, and page-memory PPTX normalization.
- Keep the source-URL gate and its failure semantics in the shared boundary;
  parser layers only forward context.

## Task 3: Verify and hand off bounded evidence

- Run focused remote-input, source-storage, URL-upload, parser, HTML, document
  profile, and MinerU URL-storage contracts.
- Run the worker suite, Ruff, changed-runtime Pyright, compile, and diff
  checks; distinguish unrelated order/environment failures from this change.
- Keep live URL/provider/storage calls, private data, deployment, and upstream
  synchronization out of scope.
