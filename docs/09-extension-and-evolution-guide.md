# Heartweb extension and evolution guide

**Author:** Raphael Rechberger
**Status:** Current extension authority
**Updated:** 2026-08-22

## 1. Goal

Heartweb is designed to evolve without losing old results, customer separation or workflow integrity. Extensions are versioned and activated deliberately. Existing accepted runs remain bound to the versions that produced them.

## 2. Freedom and constraints

LLMs retain freedom for:

- strategic interpretation
- topic and cluster development
- information-gap analysis
- page structure and comparison concepts
- briefing language and recommendations
- evidence-grounded prioritization

LLMs do not control:

- customer or project identity
- workflow state
- revisions and hashes
- Human Gates
- provider market binding
- missing metrics
- unsupported claims
- releases and publication status

Contracts are guardrails and acceptance filters. They do not replace prompt quality, real data or human judgment.

## 3. Change a prompt

A semantic prompt change follows this sequence:

1. create a new prompt version
2. document the intended output difference
3. compare against the preserved baseline requirement matrix
4. update the expected output schema if meaning or structure changes
5. update validator and renderer
6. update Quality Gate rules
7. add positive and negative fixtures
8. update Context Package and tool policy
9. run behavioral comparison against representative fixtures
10. activate only for new runs or an explicit migration

Never replace accepted prompt bytes silently.

## 4. Change an output contract

Contract changes use a new schema version when they alter required fields, meaning, allowed values or validation behavior.

A contract migration must define:

- old version
- new version
- compatible read behavior
- activation rule
- whether old artifacts remain valid
- whether a rerun is required
- negative cases that must fail

Do not add optional fields that silently become required in downstream code.

## 5. Add or replace a provider

Use a provider adapter behind Provider Gateway.

The adapter must define:

- capability
- request schema
- required market, location and language fields
- asynchronous or synchronous execution behavior
- normalized result schema
- raw-response Evidence and hash
- timeout, quota and error mapping
- retry policy
- unsupported capability behavior

Provider failure must not produce estimated values or an automatic fallback with different semantics.

## 6. Add a tool

Classify the tool as:

- deterministic validator or solver
- external data provider
- renderer
- file transformer
- deployment adapter

Define exact inputs, outputs, errors, side effects and Evidence. Add the tool to a step Tool Policy only after contract and failure tests pass.

## 7. Add a workflow step

A new step requires:

1. stable step ID
2. workflow-graph transition
3. predecessor and successor rules
4. prompt or deterministic executor
5. Context Package rule
6. output contract
7. renderer
8. machine Quality Gate
9. Human Gate decision
10. artifact and revision behavior
11. Operator API command and read model
12. Console action and state
13. Delivery mapping
14. tests and real acceptance evidence

A new step must not duplicate behavior that belongs inside an existing step or Notion implementation work.

## 8. Customer-specific customization

Prefer typed Project V2 configuration over prompt forks.

Customer-specific inputs include:

- sector and services
- target audience
- countries, regions and service areas
- language and tone
- business objectives
- design tokens
- claims and Evidence
- risk and compliance profile
- content types
- provider availability

If a new customer archetype requires reusable behavior, add a client-neutral optional module with an explicit activation condition. Do not embed the first customer's content into shared logic.

## 9. Quality preservation

Every extension is checked against:

- original approved quality requirements
- current schema and validator behavior
- representative positive and negative fixtures
- customer-neutral archetypes
- real output usefulness
- no regression in tenant, revision, Evidence or transition safety

A structurally valid but professionally thin result is not accepted.

## 10. Reruns and migrations

A rerun creates a new artifact revision. It uses:

- exact active prompt version
- released predecessor artifacts
- Project V2
- current permitted Evidence
- rejected artifact and findings when applicable
- immutable field policy
- expected schema version

Do not rewrite an accepted artifact in place.

## 11. Documentation update contract

A semantic change must update:

- `00_admin/PROJECT_STATE.md`
- active or superseded entry in `00_admin/DECISIONS.md`
- relevant active plan
- AGENTS and CLAUDE only when a global agent rule changes
- README when user-visible architecture or capability changes
- current architecture or integration documents
- authority overrides and generated registry

Then run:

```text
python scripts/build_repository_index.py
python scripts/build_repository_index.py --check
python -m unittest tests.test_repository_index -v
```

## 12. Retrieval and RAG integration

A future retriever consumes `DOCUMENT_REGISTRY.jsonl`.

Required order:

1. filter by lifecycle
2. filter by workflow step, audience and task area
3. prefer authority level and retrieval priority
4. apply semantic ranking
5. include historical Evidence only for explicit historical or audit requests

Never let embedding similarity override Project State, Decisions, schema versions or supersession metadata.

## 13. Release gate

An extension is ready only when:

- implementation and contracts match
- generated clients show no drift
- affected tests pass
- negative behavior is proven
- documentation and registry are current
- no open P0/P1 remains
- a real or representative output demonstrates the intended value
- Raphael explicitly approves commit, merge or deployment where required
