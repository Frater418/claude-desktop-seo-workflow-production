# Prompt Quality Preservation and V2 Contract Restoration Plan

> **For implementation:** Use only the execution path authorized by the user and project rules. In Raphael's OpenCode OMO workflow, Hermes briefs only root Sisyphus and independently verifies results. Native `delegate_task` requires explicit authorization.

**Author:** Raphael Rechberger
**Date:** 2026-08-21
**Status:** Approved production-first sequencing contract. Pre-release scope executes after Sprint 5E and DIB-005. PQ-3 and PQ-5 are post-release.

**Goal:** Restore every output-critical requirement from the original Heartweb Promptworkflow and repository version 1.4 prompts into the current V2 schemas, validators, renderers, Quality Gates, fixtures, and Admin review surfaces without reverting or duplicating the current architecture.

**Architecture:** Keep Project V2, Provider Gateway, Transition Service, Context Packages, immutable artifacts and revisions, Quality Gates, Local Operator API, event boundaries, and the single-admin Console. Prompts remain bounded candidate generators. Quality requirements become closed typed fields and machine or human gates rather than returning to prompt-only prose.

**Tech Stack:** Existing Python 3.11/3.12 services, JSON Schema Draft 2020-12, current renderer and preflight modules, React/TypeScript Operator Console, current test suites, real Chrome QA, and deterministic tools.

---

## Binding Sources

1. `C:\Users\offic\Desktop\Heartweb\Promptworkflow`
2. Git prompt baselines at `a10093b`, `c818ffc`, and `5e78679`
3. `00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md`
4. `00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md`
5. `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
6. `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`
7. `00_admin/DECISIONS.md`, DEC-0020, DEC-0021, and the new sequencing decision
8. `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`, DIB-001, DIB-005, and DIB-006

## Global Constraints

1. Do not interrupt the active Browser-QA package or Sprint 5E.
2. Do not run restoration against an unstable shared worktree.
3. Create a stable controller-verified Sprint-5E checkpoint before restoration.
4. Do not overwrite, delete, or normalize original Desktop prompts or old Git prompt versions.
5. Do not restore complete old prompts into runtime. Transfer requirements to current seams.
6. No direct provider calls from prompts.
7. No prompt may mutate canonical status, create Human Approval, or start a successor step.
8. Heartweb remains client-neutral. AHD is only the real acceptance case.
9. Every requirement must map to one authority and one verification route. Do not create a second Source of Truth.
10. No commit, push, master merge, deployment, or live external integration without Raphael's explicit gate.
11. Hermes communicates only with root Sisyphus. Sisyphus owns internal decomposition.
12. Complete one package and its independent review before starting the next package.
13. Desktop and core actions are release-blocking. Mobile is advisory unless it corrupts state, hides a required review action, or makes a required action unreachable.

## Execution Chain

```text
Current Browser QA
-> Sprint 5E Delivery
-> controller verification and stable checkpoint
-> DIB-005 shared diagnostic trace
-> PQ-0 bounded output-critical requirement matrix
-> PQ-1 Step 1b and 1c output fidelity
-> PQ-2 Step 2 and Step 3 real data and solver chain
-> PQ-4 Step 4a and 4b GEO, Copywriter, and Developer quality
-> targeted Production Release audit
-> first local Production Release and real AHD output chain
-> PQ-5 real-output parity audit
-> PQ-3 before the first day-30 checkpoint
-> Post-Release Backlog
```

The existing final-audit Todo becomes the targeted Production Release audit. It is deferred only until DIB-005 and the pre-release packages PQ-0, PQ-1, PQ-2, and PQ-4 are verified. It does not wait for real day-30 data, live Notion, live n8n, exhaustive mobile polish, full docs cleanup, or the post-release real-output audit.

## Package PQ-0: Baseline Requirement Matrix

**Objective:** Convert every original output-critical instruction into a traceable migration row before any production contract changes.

**Evidence inputs:** Desktop originals, Git master prompts, current V2 prompts, schemas, preflights, renderers, gates, UI, and tests.

**Required matrix fields:** Requirement ID, original source and exact line, affected step, user-facing outcome, current V2 target, state `preserved | strengthened | missing | deferred | not_applicable`, schema field, validator, renderer, gate, UI view, positive fixture, negative fixture, and acceptance evidence.

**Acceptance criteria:**

1. Every output-critical original requirement needed for the first production route has exactly one classified row.
2. No missing row is silently classified as architectural refactoring.
3. Missing requirements are grouped only into PQ-1, PQ-2, or PQ-4 for pre-release work, with Step 3B and real-output parity routed post-release.
4. No product code is changed during PQ-0.

## Package PQ-1: Step 1B and Step 1C Output Fidelity

**Objective:** Preserve the safe Architecture and Design contracts while restoring professional customer and developer usefulness.

**Likely affected seams:**

- `standards/outputs/step-1b-architecture.schema.json`
- `services/step1b_preflight/validator.py`
- `services/step1b_preflight/render.py`
- `prompts/1b-seitenarchitektur.xml.md`
- `standards/outputs/step-1c-template.schema.json`
- `services/step1c_preflight/validator.py`
- `services/step1c_preflight/render.py`
- `prompts/1c-pillar-template.xml.md`
- Step-1B and Step-1C review surfaces and fixtures

**Must restore:**

- customer-presentable architecture tree, legend, page-type classification, decisions, and open confirmations;
- bestandscheck and update-versus-new behavior;
- Hero and CTA;
- Quick Facts;
- substantive editorial block;
- unique pillar-specific heartpiece;
- grouped cluster links;
- process section;
- Social Proof;
- visible FAQ answers;
- cross-pillar links;
- final CTA;
- brand-derived design consistency and no external runtime dependencies.

**Acceptance criteria:** Machine contracts reject missing mandatory structure, renderers produce professional self-contained outputs, and a representative human review confirms the outputs are usable. The real AHD review occurs post-release in PQ-5.

## Package PQ-2: Step 2 and Step 3 Real Data and Solver Chain

**Objective:** Make the real provider-evidence dataset sufficient for the actual deterministic solver while preserving provider neutrality and evidence integrity.

**Likely affected seams:**

- `standards/outputs/step-2-keyword-evidence.schema.json`
- `services/step2_preflight/validator.py`
- `services/step2_preflight/render.py`
- `prompts/2-cluster-recherche.xml.md`
- `services/step3_preflight/validator.py`
- `standards/outputs/step-3-plan.schema.json`
- `mcp/tools/capacity_matrix_solver.py`
- Provider Gateway normalization and Step-2/Step-3 fixtures

**Must restore:**

- broad 25 to 40 candidate research coverage across approved category families;
- typed target keyword, search volume, difficulty, CPC where available;
- category, content type, GEO type, engine target;
- information gain and entity-density inputs where used;
- business relevance and explicit mandatory-location policy;
- deterministic projection from released Step 2 into the real solver;
- existing effort weights, priority formula, mandatory Phase-1/2 placement, backlog, and link maps;
- no invented, zero-filled, or provider-default metrics.

**Acceptance criteria:** A real provider-backed Step-2 artifact drives the real solver without manual side data, all mandatory items are preserved, and both positive and missing-metric cases are proven.

## Post-Release Package PQ-3: Step 3B Performance Semantics

**Objective:** Keep immutable adjustment revisions while restoring the approved decision logic.

**Activation:** Complete before the first real day-30 checkpoint. It does not block the initial Step-0-to-Step-4B production route because Step 3B remains `not_due` until real post-publication data exists.

**Likely affected seams:** Step-3B schema, prompt, validator, renderer, measurement records, Quality Gate, and Operator review.

**Must restore:**

- minimum publication age;
- performer, stagnant, and underperformer classification;
- local-location-page special evaluation;
- cause categories for links, intent, depth, and keyword targeting;
- performer expansion, refresh, replacement, and mandatory-location priority rules;
- unchanged weekly capacity boundary;
- explicit original-versus-proposed change markers.

**Acceptance criteria:** A typed performance fixture cannot produce an adjustment without the required observation window, classification, cause, evidence, and capacity-safe proposal.

## Package PQ-4: Step 4A and Step 4B Quality Restoration

**Objective:** Execute DIB-001 fully through existing V2 seams.

**Authority:** `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`.

**Must restore:** Complete Copywriter briefing, Hero Direct Answer, Semantic Triples, Evidence Containers, evidence-bearing data, definitive language, enhanced entity bindings, semantic sections, visible GEO components, section-to-JSON-LD correspondence, safe Local SEO, conversion structure, and professional Developer output.

**Acceptance criteria:** All machine-checkable DIB-001 criteria plus representative Copywriter and Developer review pass. Real AHD output review follows in post-release PQ-5.

## Post-Release Package PQ-5: Real Output Parity and Acceptance

**Objective:** After the first real AHD output chain, prove technical safety and customer-facing quality together and convert any real-output findings into bounded corrections.

**Required evidence:**

1. completed baseline requirement matrix;
2. schema and prompt diffs;
3. validator and renderer positive and negative tests;
4. real Step-2-to-Step-3 solver trace;
5. real 1b, 1c, 4a, and 4b outputs;
6. DIB-005 timestamped diagnostics;
7. task-based Admin browser QA;
8. independent specification review;
9. independent code and contract quality review;
10. human output-quality review against the original Promptworkflow.

**Gate:** No simulated evidence is presented as real. Real AHD findings are corrected before broad rollout, public deployment, or final product-maturity claims. This package does not block creating the first controlled local production output.

## Final Audit Sequencing

The existing Sisyphus Todo `Sprint 5 completion: Run independent final audit` becomes a targeted Production Release audit and executes after:

1. Sprint 5E verified;
2. stable checkpoint created;
3. DIB-005 verified;
4. PQ-0, PQ-1, PQ-2, and PQ-4 verified.

If a pre-release package fails, the Production Release audit remains blocked and reports the exact open package instead of issuing a partial GO. PQ-3, PQ-5, live integrations, exhaustive mobile polish, docs-corpus cleanup, repository hygiene, and presentation expansion remain in `00_admin/POST_RELEASE_BACKLOG.md`.
