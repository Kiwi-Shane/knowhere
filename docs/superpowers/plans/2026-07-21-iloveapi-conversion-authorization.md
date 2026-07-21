# iLoveAPI Conversion Authorization Plan

## Completed implementation

- [x] Add optional trusted job metadata to the low-level PPTX conversion call.
- [x] Require the existing `iloveapi` provider authorization before quota or
      outbound request work.
- [x] Propagate metadata through the legacy PPTX API path and page-memory
      normalization path.
- [x] Add synthetic negative, positive, and propagation contract tests.
- [x] Preserve the existing default-off operator gate, endpoint allowlist,
      explicit timeouts, and redirect blocking.

## Verification

- New conversion authorization contract: 4 passed.
- Affected iLoveAPI/provider/parser selection: 26 passed.
- Ruff check: passed; the two touched legacy files retain pre-existing
  formatter-only differences, while the new test is formatter-clean.
- Compileall: passed.
- Changed-runtime Pyright: 0 errors, 0 warnings, 0 informations.
