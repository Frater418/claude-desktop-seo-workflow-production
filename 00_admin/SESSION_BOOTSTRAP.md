# Session bootstrap

**Author:** Raphael Rechberger
**Indexed snapshot:** `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`

## Mandatory read order

1. Read `00_admin/PROJECT_STATE.md`.
2. Read active and superseding records in `00_admin/DECISIONS.md`.
3. Read `00_admin/REPOSITORY_INDEX.md`.
4. Select the active plan for the requested task from `.hermes/plans/INDEX.md`.
5. Before any test or review decision, read `standards/testing/PROTOTYPE_TEST_POLICY.md`.
6. Resolve exact standards, prompts and supporting evidence through `00_admin/repository-index/DOCUMENT_REGISTRY.json`.
7. Read historical or audit material only when the task requires origin, rollback, prior decisions or failure reconstruction.

## Authority rule

Project State and active Decisions override entry documents, old plans, audit prose and semantic similarity. A search result is not an authority decision.

## Current snapshot warning

This parallel index was generated from WIP commit `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`. Any records listed as `needs_reconciliation` in `00_admin/REPOSITORY_INDEX.md` must not be treated as current authority. All volatile completion facts require one final refresh from the stable Feature commit before integration.

## RAG rule

A future semantic retriever must first exclude `historical`, `superseded` and `evidence` records from default retrieval. It may include them only for explicit historical or audit queries.
