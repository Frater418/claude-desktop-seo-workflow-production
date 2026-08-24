# Repository Authority and RAG Index Implementation Plan

> **Lifecycle: active isolated documentation plan.** Vor Integration aus dem finalen stabilen Feature-Commit aktualisieren, neu generieren und vollstaendig verifizieren.

> **For implementation:** This plan executes only in the isolated worktree and branch `docs/repository-authority-index-2026-08-22`. It must not write to the active Sisyphus worktree. No commit, push, merge or branch consolidation is authorized by this plan.

**Author:** Raphael Rechberger
**Date:** 2026-08-22
**Status:** Parallel build complete and in verification. Final volatile-state refresh remains mandatory at the stable Production integration gate.

**Goal:** Give humans and new LLM sessions current, complete and correctly classified project documentation plus one deterministic, machine-readable and task-oriented map of authorities, supporting sources, historical evidence and superseded material without introducing a second Source of Truth or a semantic-search service.

**Architecture:** A curated source policy and authority override file classify repository documents. A deterministic Python generator emits a canonical JSON registry, RAG-ready JSONL, session bootstrap and compact Markdown indexes. Generated indexes point to existing authorities and never replace Project State, Decisions, standards, artifacts or evidence.

**Tech Stack:** Python standard library, JSON Schema Draft 2020-12, Markdown, JSON, JSONL and existing pytest infrastructure.

---

## 1. Safety and Integration Boundary

1. Work only inside the isolated worktree.
2. Base implementation on WIP commit `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`.
3. Treat the active Sisyphus tree as a later integration source, not a writable dependency.
4. Reconcile entry and current architecture documents only in this isolated branch. Do not write them into the active Sisyphus tree.
5. Before integration, update the branch from the final stable Feature commit, re-read current Project State and Decisions, refresh volatile completion facts, rerun the generator and review all lifecycle classifications.
6. Historical audits and checkpoints remain immutable.
7. Generated indexes may be replaced deterministically. Source documents may not.
8. No vector database, embedding server, crawler daemon or external telemetry is in scope.

## 2. Authority Model

The registry uses this order:

1. latest explicit Raphael instruction, represented in current project state and decisions;
2. `00_admin/PROJECT_STATE.md`;
3. active records in `00_admin/DECISIONS.md`;
4. active plans identified by the classification overrides;
5. machine-readable standards and contracts;
6. current runtime, UI and tests;
7. current integration documents;
8. supporting research;
9. audits, checkpoints, historical plans and superseded documents as evidence only.

A semantic retriever may rank content by similarity later, but it must filter and order results using registry lifecycle and authority metadata.

## 3. Registry Record

Every indexed record contains:

- stable `document_id`;
- normalized repository-relative path;
- title and short summary;
- document type and repository area;
- lifecycle state;
- authority level and retrieval priority;
- default-retrieval flag;
- audience, tags and workflow steps;
- supersession and related-document links;
- content SHA-256 and byte size;
- format and generated-source marker.

Allowed lifecycle states:

- `current_authority`
- `current_strategy`
- `active_plan`
- `deferred_plan`
- `needs_reconciliation`
- `historical`
- `superseded`
- `evidence`
- `generated_view`

Superseded, historical and evidence records are excluded from default retrieval unless requested explicitly.

## 4. Source Policy

Index these areas:

- root entry and governance documents;
- top-level `00_admin` state, decisions, backlog and meeting records;
- `.hermes/plans` documents and images;
- `docs` documents;
- prompts and documentation-oriented standards;
- compact research sources;
- audit and checkpoint evidence with low retrieval priority;
- selected test evidence documents.

Exclude runtime caches, dependencies, source code without documentation purpose, generated registry outputs, credentials and customer workspaces.

## 5. Generated Artifacts

Create:

- `standards/documentation/document-registry.schema.json`
- `00_admin/repository-index/source-policy.json`
- `00_admin/repository-index/authority-overrides.json`
- `00_admin/repository-index/DOCUMENT_REGISTRY.json`
- `00_admin/repository-index/DOCUMENT_REGISTRY.jsonl`
- `00_admin/REPOSITORY_INDEX.md`
- `00_admin/SESSION_BOOTSTRAP.md`
- `docs/INDEX.md`
- `.hermes/plans/INDEX.md`
- `00_admin/audits/INDEX.md`
- `03_research/INDEX.md`
- `scripts/build_repository_index.py`
- `tests/test_repository_index.py`

## 5.1 Reconciled Source Documents

Update in the isolated branch:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `00_admin/POST_RELEASE_BACKLOG.md`
- `docs/00-current-production-architecture.md`
- `docs/09-extension-and-evolution-guide.md`
- `docs/integrations/notion-operating-model.md`
- `docs/integrations/n8n-orchestration-model.md`
- `docs/copywriter-handoff-guidelines.md`

Add explicit lifecycle banners to every historical or superseded Markdown document under `docs/` and `.hermes/plans/`. The banner links to the current registry and names the current replacement where one exists. Historical body content remains unchanged.

## 6. Session Bootstrap Contract

A new LLM session reads in this order:

1. `00_admin/SESSION_BOOTSTRAP.md`
2. `00_admin/PROJECT_STATE.md`
3. active decisions linked from `00_admin/DECISIONS.md`
4. `00_admin/REPOSITORY_INDEX.md`
5. the active plan for the requested task
6. exact standards, services and tests linked by the registry
7. historical evidence only when needed for reconstruction

The bootstrap must warn when entry documents remain `needs_reconciliation`.

## 7. RAG-ready JSONL

The JSONL output contains one stable JSON object per record. It is suitable for later chunking or embedding, but contains no embeddings. Every record carries authority and lifecycle fields so a future retriever can filter stale material before semantic ranking.

Recommended retrieval behavior:

1. filter by lifecycle and task area;
2. prefer current authority and active plans;
3. apply workflow-step and audience filters;
4. rank remaining records semantically;
5. include historical or evidence records only when the query requests origin, audit, rollback or prior decisions.

## 8. Tests and Gates

Tests must prove:

1. generation is byte-identical for unchanged source;
2. `--check` detects drift;
3. every indexed path exists and stays within the repository;
4. every registry entry has required fields and a valid hash;
5. critical entry, state, decision, plan and integration documents are classified;
6. superseded or historical documents are not in default retrieval;
7. supersession and related-document paths resolve;
8. generated views are excluded from recursive source scanning;
9. no credential-like file or customer workspace is indexed;
10. generated Markdown contains no Em Dash or En Dash characters;
11. session bootstrap contains the binding read order;
12. root, docs, plans, audits and research indexes match the registry.

## 9. Final Reconciliation Gate

This isolated branch is not integration-ready until the active Production branch reaches a stable checkpoint. At that gate:

1. update the branch from the final Feature commit;
2. import DEC-0024, DEC-0025, DIB-005, DIB-006 and current Sprint-5E facts;
3. reclassify all new Delivery, diagnostic and prompt-restoration documents;
4. reconcile AGENTS, CLAUDE and README under DIB-002;
5. classify the complete docs corpus under DIB-003;
6. rerun the generator and all registry tests;
7. inspect the generated indexes manually;
8. request Raphael approval before commit, push or merge.

## 10. Definition of Done for the Parallel Build

The parallel build is complete when:

- the isolated worktree contains all planned source and generated artifacts;
- generator and tests pass locally in that worktree;
- registry output is deterministic;
- critical documents are classified with explicit lifecycle and authority;
- audit evidence remains discoverable but excluded from default retrieval;
- active Sisyphus files, branch, index and processes remain unchanged;
- the integration checklist clearly states which volatile files must be refreshed later.
- AGENTS, CLAUDE, README and current architecture documents accurately describe the V2 Core, Operator Console, Delivery, Notion boundary, future n8n role, Step-3B cycle, prompt evolution and Production-first sequence.
- historical and superseded documents carry visible lifecycle banners and are excluded from default retrieval.
