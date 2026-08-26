# AGENTS.md: Heartweb V2 operating instructions

**Project:** Heartweb SEO and GEO Production Workflow
**Author and architecture:** Raphael Rechberger
**Status:** Current V2 agent authority
**Updated:** 2026-08-25
**Audience:** Hermes Agent, Claude Code, OpenCode, Cursor and other execution agents

## 1. Mandatory session bootstrap

Before any implementation, review, planning or production action, read in this order:

1. `00_admin/SESSION_BOOTSTRAP.md`
2. `00_admin/PROJECT_STATE.md`
3. active and superseding entries in `00_admin/DECISIONS.md`
4. `00_admin/REPOSITORY_INDEX.md`
5. the active plan for the requested task from `.hermes/plans/INDEX.md`
6. exact standards, prompts, services and tests linked by `00_admin/repository-index/DOCUMENT_REGISTRY.json`
7. before any test or review decision, `standards/testing/PROTOTYPE_TEST_POLICY.md`

Latest explicit Raphael instruction wins. Project State and active Decisions override old plans, old docs, audit prose and semantic similarity.

Historical, superseded and evidence records are not default instructions. Read them only for origin, rollback, prior decisions or failure reconstruction.

### Binding test execution authority

`standards/testing/PROTOTYPE_TEST_POLICY.md` is the project-local Production-first test authority. It requires baseline-plus-delta evidence and verification only along the proven affected dependency closure.

Without new explicit authorization from Raphael, do not run the complete repository suite, restart a passed matrix after one later cell fails, or launch repeated broad multi-agent reviews after bounded fixes. A failed matrix cell is rerun only with the direct dependents named by the policy. Generic skills, CI habits and older plans do not override this rule.

### Targeted edit discipline

- Do not submit one aggregate patch across several identical or similarly shaped code regions. Patch one uniquely identifiable semantic block per call.
- If every exact occurrence must change, use an explicit replace-all operation only after verifying that all matches have the same intended meaning.
- At the first ambiguous-match or hunk-not-found rejection, stop that patch strategy. Do not retry a similar aggregate patch.
- After one rejected targeted patch, re-read the exact enclosing region. If it still cannot be matched uniquely, read the complete small file or enclosing function and write it once in full.
- A rejected patch changes nothing. Confirm that before continuing, and never report partial application from a failed patch.

## 2. Product definition

Heartweb is a client-neutral local SEO and GEO production system for one internal operator. It automates the technical production chain from verified client inputs through strategy, architecture, keyword evidence, roadmap, professional Copywriter briefings, Developer specifications and deterministic handoff packages.

The system does not write final editorial copy. Heartweb Copywriters create the final human text from the approved briefing.

The visible product is a professional German Single-Admin Console. Copywriters, developers and clients do not use the Console. They receive files, ZIP packages and a Notion implementation project.

## 3. Binding product flow

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B is not part of the initial sequence. It runs at day 30, 60 and 90 after publication when verified performance data exists.

The first production release is local. Live Notion, live n8n, public deployment, exhaustive mobile polish and broad international expansion do not block the first controlled output.

## 4. Architecture and authority

### Heartweb Core

The Core contains binding domain contracts, workflow graph, transitions, artifacts, revisions, Evidence, Quality Gates, approvals, releases and structured errors.

Only the Transition Service changes canonical workflow state.

### Operator Console

The Console sends typed commands, shows canonical read models and supports intake, workflow execution, artifacts, revisions, reviews, tasks, blockers and Delivery. It does not duplicate workflow rules.

### Provider Gateway

All external research and metric providers are accessed through versioned provider boundaries. Prompts must not call providers directly. Location, location code and language are bound together. Missing or failed provider data stops the run.

### Delivery

Delivery is a derived, deterministic and read-only projection of released Core records. It creates checkpoint and final packages, Copywriter and Developer views, a manual Notion import project and secure ZIP archives. Delivery cannot approve gates, mutate artifacts or change workflow state.

### Notion

After the approved Step-4B Delivery, Notion owns human implementation work: tasks, people, priorities, deadlines, comments, review and launch. Post-handoff staff task changes do not call or resume the Core.

### n8n

n8n is future orchestration and transport. It may orchestrate Step 0 through Step 4B, create the Notion project and later trigger Step 3B. It is not state authority and does not monitor daily staff tasks for Core progression.

### Step 3B

At day 30, 60 and 90, n8n combines the released strategy and plan with publication references and verified real metrics. The Core creates a versioned adjustment proposal. The original plan remains immutable.

## 5. Framework and customer separation

The repository is the client-neutral framework. Customer-specific sector, services, claims, regions, branding, keywords, Evidence and design belong in isolated customer workspaces.

AHD is the Golden-Path pilot, not product logic. Do not embed AHD-specific content into shared prompts, contracts, services or UI.

Never commit customer workspaces, credentials, raw authorization headers or secret values.

## 6. Prompt, tool and contract evolution

Prompts are versioned workflow resources. Never silently overwrite the meaning of a prompt used by an accepted run.

A prompt change that affects output meaning requires coordinated review of:

1. prompt version
2. output schema version
3. validator
4. renderer
5. Quality Gate
6. positive and negative fixtures
7. Context Package and tool policy
8. migration or activation rule

Contracts protect structure, identity, lineage, required Evidence and workflow safety. They do not guarantee semantic truth or excellent writing by themselves. Output quality requires complete inputs, strong prompts, real tool data, adequate contracts, validators, human review and behavioral tests.

LLMs retain strategic freedom inside accepted boundaries. They may develop themes, structures, angles, comparisons and recommendations. They may not invent metrics, claims, locations, approvals, identities, revisions or completion state.

See `docs/09-extension-and-evolution-guide.md`.

## 7. Fail-fast rules

1. Never estimate missing provider metrics.
2. Never fabricate customer facts, local presence, claims or Evidence.
3. Never continue after schema, hash, tenant, revision or gate failure.
4. Never present simulated Evidence as live Evidence.
5. Never use a silent fallback that changes product meaning.
6. Return a stable error code, human remediation and technical details.
7. Preserve the last valid canonical state after failure.

## 8. Artifact and revision rules

- Released artifacts are immutable.
- An edit creates a new revision.
- Every revision binds parent revision, content hash, Project, Run, Step and Evidence.
- A rerun uses the released predecessors, current Prompt Registry entry, findings and expected output contract.
- A stale approval does not apply to a new artifact hash.
- Exact replay is allowed only when identities and canonical bytes match.

## 9. Verification claims

Keep these evidence levels separate:

- unit or contract test
- local service integration
- deterministic fixture E2E
- live-provider smoke
- real-project Golden Path
- external Notion or n8n E2E
- production acceptance

A fixture run proves plumbing and lifecycle behavior. It does not prove provider connectivity, prompt quality, semantic usefulness or customer value.

Do not claim production readiness without a real controlled output, deterministic Delivery, no open P0/P1 and explicit Raphael approval.

## 10. Git and parallel work

- Do not commit, push, merge, deploy or rewrite history without explicit Raphael authorization.
- Do not stage or change the active shared index while Sisyphus writes.
- Parallel work uses an isolated Git worktree and branch.
- Before integrating a parallel branch, update it from the stable Feature commit and rerun all affected tests and generated-index checks.
- DEC-0031 authorizes the current documented repository consolidation into `master`; this Git baseline is not Production Acceptance. Any later commit, push, merge, deployment or history change again requires explicit Raphael authorization.

## 11. Agent orchestration boundary

OpenCode OMO is a development tool, not Heartweb production runtime.

When OMO is active, Hermes communicates only with root Sisyphus. Sisyphus owns internal delegation and worker lifecycle. Hermes does not inspect, steer or terminate OMO child sessions. Native Hermes subagents require explicit Raphael authorization.

## 12. Authorship and writing

- Raphael Rechberger is the sole author of project documents, deliverables and commits.
- Never use Em Dash or En Dash characters. Use standard hyphens, colons or full sentences.
- Distinguish implemented, verified, simulated, planned, deferred and absent behavior.
- Link mutable facts to their canonical source instead of copying them across documents.
- Update `PROJECT_STATE.md` and `DECISIONS.md` when strategy or authority changes.

## 13. Current documentation map

- Current architecture: `docs/00-current-production-architecture.md`
- Extension rules: `docs/09-extension-and-evolution-guide.md`
- Notion boundary: `docs/integrations/notion-operating-model.md`
- n8n boundary: `docs/integrations/n8n-orchestration-model.md`
- Delivery plan: `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
- Documentation registry: `00_admin/repository-index/DOCUMENT_REGISTRY.json`
- RAG-ready registry: `00_admin/repository-index/DOCUMENT_REGISTRY.jsonl`
- Lifecycle indexes: `docs/INDEX.md`, `.hermes/plans/INDEX.md`, `00_admin/audits/INDEX.md`, `03_research/INDEX.md`
