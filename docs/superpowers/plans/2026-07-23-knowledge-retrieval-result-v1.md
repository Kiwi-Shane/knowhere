# Knowhere `knowledge-retrieval-result-v1`

## Goal

Publish the source-owned retrieval-result schema, synthetic contract fixture,
and contract test on the Knowhere feature branch based directly on the live
fork default branch.

## Scope

- Add `schemas/knowledge-retrieval-result-v1.schema.json`.
- Add `examples/contracts/knowledge-retrieval-result-v1/example.json`.
- Add `apps/worker/tests/contract/test_knowledge_retrieval_result_v1_contract.py`.
- Add a concise qualification/ownership note if needed, without claiming
  runtime qualification.
- Do not activate a retrieval route, private corpus, telemetry path, or
  runtime qualification in D1.

## Verification

Run the contract test from the Knowhere worktree, run JSON parsing/schema
structural checks, inspect the diff for private artifacts, then commit and
push only the feature branch. Record the final commit and artifact hashes for
the RA consumer packet.
