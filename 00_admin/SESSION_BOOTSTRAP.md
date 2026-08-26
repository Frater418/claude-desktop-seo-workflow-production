# Session bootstrap

**Author:** Raphael Rechberger
**Indexed snapshot:** `da1d77c2dcda40707884e6412624577c953524e8`

## Mandatory read order

1. Read `00_admin/ONBOARDING_REFERENCE.md` for the generated complete snapshot.
2. Read `00_admin/PROJECT_STATE.md`.
3. Read active and superseding records in `00_admin/DECISIONS.md`.
4. Read `00_admin/REPOSITORY_INDEX.md`.
5. Select the active plan for the requested task from `.hermes/plans/INDEX.md`.
6. Before any test or review decision, read `standards/testing/PROTOTYPE_TEST_POLICY.md`.
7. Resolve exact standards, prompts and supporting Evidence through `00_admin/repository-index/DOCUMENT_REGISTRY.json`.
8. Read historical or audit material only when the task requires origin, rollback, prior decisions or failure reconstruction.

## Authority rule

Project State and active Decisions override entry documents, old plans, audit prose and semantic similarity. A search result is not an authority decision.

## Current snapshot warning

This generated view was built from source commit `da1d77c2dcda40707884e6412624577c953524e8`. Exact live branch and remote identity must be read from Git. Any record listed as `needs_reconciliation` in `00_admin/REPOSITORY_INDEX.md` is not current authority and blocks a clean integration.

## RAG rule

A future semantic retriever must first exclude `historical`, `superseded` and `evidence` records from default retrieval. It may include them only for explicit historical or audit queries.
