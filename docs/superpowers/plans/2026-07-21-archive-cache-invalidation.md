# Archive Cache Invalidation Plan

1. Add a contract test for an idempotent archive request and observe the
   current missing invalidation behavior.
2. Move cache invalidation after the archive transition branch so both active
   and already-archived requests attempt the post-commit invalidation.
3. Run the focused test, the full document contract module, retrieval-cache
   unit tests, and relevant lifecycle/publication contract tests.
4. Run Ruff, Pyright, compile checks, inspect the diff, then record the result
   as a bounded stale-cache boundary without changing canonical qualification.
