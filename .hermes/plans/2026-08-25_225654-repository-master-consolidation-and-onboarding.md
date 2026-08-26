---
title: "Heartweb Repository Authority, Master Consolidation and Fresh Clone"
summary: "Architecture and execution plan for repository-wide documentation, prompt, agent and information reconciliation, safe master integration, verified branch retirement, a deterministic one-file onboarding reference and a fresh continuation clone."
created_at: "2026-08-25T22:56:54-04:00"
status: "proposed"
author: "Raphael Rechberger"
---

# Heartweb Repository Authority, Master Consolidation and Fresh Clone Implementation Plan

> **For implementation:** Use only the execution path authorized by Raphael and the project rules. If OpenCode OMO is used, Hermes briefs only root Sisyphus and independently verifies results. Native `delegate_task` is not authorized. Git integration, push, branch deletion and clone replacement remain explicit controller gates.

**Goal:** Reconcile the complete Heartweb repository without deleting historical context, publish the truthful integrated state to `master`, retire every proven-reconciled non-master branch, replace the current workspace with a verified fresh clone and continue the paused real workflow from a new feature branch.

**Architecture:** Canonical sources remain separate and authoritative. A deterministic generated onboarding compendium provides one complete entry surface without replacing those sources. Documentation and runtime status are reconciled append-only through Project State, Decisions, lifecycle metadata and versioned prompt and agent contracts. Git branches are retired only after their tips are provably reachable from the final `master` graph.

**Tech Stack:** Git and GitHub CLI, Python 3.11, deterministic repository-index generator, JSON Schema, Markdown, FastAPI contracts, React and TypeScript Operator Console, Hermes `heartweb-runtime` Gateway.

---

## 1. Binding outcome

The operation ends with all of the following true:

1. Every current repository authority reflects the actually implemented state as of the consolidation.
2. Historical, superseded, audit and evidence files remain present or are explicitly preserved outside Git when they are local-only. Nothing is silently deleted because it appears stale.
3. Prompt changes obey semantic versioning. Previously accepted prompt versions remain immutable.
4. Every active Step Agent, Worker Profile and Tool Policy is mapped to its exact prompt, model policy, output contract and hash.
5. `00_admin/ONBOARDING_REFERENCE.md` provides one generated onboarding surface with complete source traceability.
6. The final `master` includes all accepted implementation and documentation changes.
7. Every retired branch tip is reachable from final `master` before deletion.
8. A clean clone at the canonical path matches the remote `master` SHA byte-for-byte at the Git tree boundary.
9. A new branch named `feature/production-workflow-continuation` starts from that exact `master` SHA.
10. The existing external CL project and its canonical workflow state survive the repository replacement.
11. Merging to `master` is not described as Production acceptance. The real Step-1 result and later Golden Path cells remain honestly open until executed and reviewed.

## 2. Measured baseline

Read-only inventory captured on 2026-08-25 at 22:56 AST:

| Area | Current fact |
|---|---|
| Repository | `Frater418/claude-desktop-seo-workflow-production` |
| GitHub default branch | `master` |
| Current `master` | `3f980520f049725e8c5a531c6925512ca79c023d` |
| Active local branch | `feature/e2e-operator-workflow-system` at the same commit as `master` |
| Working tree | 112 tracked change entries and 84 untracked files |
| Registry | 327 entries, no missing path and no duplicate path |
| Registry lifecycle | 127 current authority, 8 current strategy, 6 active plans, 173 evidence, 7 historical, 6 superseded |
| Default retrieval | 23 documents |
| Prompt files | 14 |
| Official workflow prompts | 9, including post-publication Step 3B |
| Active initial-route Step Agents | 8 for `0`, `1`, `1b`, `1c`, `2`, `3`, `4a`, `4b` |
| Worker Profiles | 8 |
| Tool Policies | 8 |
| GitHub branch protection | `master` is currently not protected |
| Open PRs | none |
| Merged PRs | PR 1 and PR 2 |
| Real workflow | Step 0 approved and released; Step 1 Run `run-next-7f7e2b778f4521b9` is paused in `in_progress`; no Step-1 provider execution was submitted |

## 3. Authority and supersession architecture

### 3.1 Authority order

The existing order remains binding:

1. latest explicit Raphael instruction
2. `00_admin/PROJECT_STATE.md`
3. active and superseding records in `00_admin/DECISIONS.md`
4. active plans
5. standards and contracts
6. current runtime and tests
7. current integration documents
8. supporting research
9. historical and audit evidence

### 3.2 New decisions required

Append, do not rewrite history:

- `DEC-0031`: Consolidate the truthful current repository state into `master` now. This supersedes only the timing restriction in DEC-0022. It does not declare M10, PT-03, PT-11 or Production acceptance complete.
- `DEC-0032`: Provide a deterministic one-file onboarding compendium while preserving all canonical source files and lifecycle history.

Patch DEC-0022 to `superseded` with `Superseded by: DEC-0031`. Preserve its original context, rationale and evidence.

### 3.3 No false release claim

The consolidated `master` is the integrated development and operational baseline. Documentation must state explicitly:

- implemented behavior
- verified behavior and exact evidence boundary
- currently running or paused behavior
- unverified behavior
- deferred behavior
- absent behavior

The merge must not convert a real Step-1 run without a result into a completed Golden Path claim.

## 4. Known inconsistencies to resolve

| ID | Current source | Conflict | Planned resolution |
|---|---|---|---|
| C-01 | `00_admin/PROJECT_STATE.md` | Says GATE-0 is closed and no Approval or Release exists | Update to the verified Step-0 release and Step-1 `in_progress` state |
| C-02 | DEC-0022 | Prohibits master integration before Final-Gate | Supersede timing through DEC-0031, while preserving open Production gates |
| C-03 | `README.md` | Still lists Delivery, diagnostics and output restoration as incomplete | Reconcile against current implementation and latest verified boundaries |
| C-04 | generated `SESSION_BOOTSTRAP.md` | Describes a parallel WIP index and stable Feature integration that has already occurred | Replace branch-specific prose with neutral source-snapshot and onboarding rules |
| C-05 | Prompt inventory | 14 files, 9 official workflow entries and 8 initial-route agents are easy to misread as inconsistent counts | Classify aliases, historical versions, active intake, active workflow prompts and deferred Step 3B explicitly |
| C-06 | `INTEGRATION_CHECKLIST.md` | Refers to the now-merged documentation branch and old WIP base | Mark superseded and point to this plan and DEC-0031 without deletion |
| C-07 | Repository index snapshot | Generated outputs use current `HEAD`, while source edits may still be uncommitted | Use a two-stage commit: authored sources first, generated views second |
| C-08 | Local-only untracked files | `apps/operator-console/.env.production` and `00_admin/session-recovery/` are not safely classified for Git | Preserve in the external snapshot, exclude from staging and add explicit ignore rules without reading secret values |
| C-09 | Central project registries | Still describe Delivery and the real run as open at an older checkpoint | Refresh status pointers after the new clone is verified |
| C-10 | GitHub master | Default branch is unprotected | Decide after consolidation whether to enable protection; do not change it silently |

Any newly discovered conflict with two plausible current meanings becomes a blocking question for Raphael. Historical material is never silently rewritten into the new meaning.

## 5. One-file onboarding architecture

### 5.1 Generated target

Create:

- `00_admin/ONBOARDING_REFERENCE.md`

Generate it through:

- `scripts/build_repository_index.py`

Add it to `GENERATED_PATHS`, so it is not recursively indexed as its own source.

### 5.2 Content contract

The file contains, in this order:

1. snapshot identity and generator version
2. authority order and conflict rule
3. product purpose and hard boundaries
4. truthful current status and next gate
5. workflow `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery`
6. separate Step-3B day-30, day-60 and day-90 boundary
7. Core, Console, Provider Gateway, Hermes Gateway, Delivery, Notion and n8n architecture
8. implemented, verified, unverified, planned, deferred and absent capability tables
9. Git, authorship, safety, customer-separation and testing rules
10. verbatim source sections for all current onboarding-critical Default-Retrieval authorities, each headed by source path, lifecycle, authority level and SHA-256
11. complete prompt catalog for all 14 prompt files, with active, alias, historical or deferred classification
12. full active workflow prompt registry map for all 9 registered steps
13. full active Step-Agent map for all 8 initial-route agents
14. Worker Profile and Tool Policy versions, paths and hashes
15. schema, validator, renderer, gate and fixture evolution rules
16. exact local startup, health, verification and recovery entry points without credentials
17. complete inventory row for every registry entry, including path, lifecycle, authority, type, summary and hash
18. branch and fresh-clone continuation point

Every registry entry appears in the final inventory. Raw bodies of the 173 audit and evidence records remain at their canonical paths instead of being duplicated into the onboarding file. This keeps the file usable while omitting no source from discovery.

### 5.3 Source-of-truth warning

The generated file begins with:

- it is a generated onboarding view
- it never overrides Project State, active Decisions or source contracts
- source blocks are identified and hashed
- any drift makes `build_repository_index.py --check` fail

### 5.4 Generator and test files

Modify:

- `scripts/build_repository_index.py`
- `tests/test_repository_index.py`
- `00_admin/repository-index/source-policy.json`
- `00_admin/repository-index/authority-overrides.json`
- `standards/documentation/document-registry.schema.json` only if an additive field is genuinely required

Regenerate:

- `00_admin/ONBOARDING_REFERENCE.md`
- `00_admin/REPOSITORY_INDEX.md`
- `00_admin/SESSION_BOOTSTRAP.md`
- `00_admin/repository-index/DOCUMENT_REGISTRY.json`
- `00_admin/repository-index/DOCUMENT_REGISTRY.jsonl`
- `docs/INDEX.md`
- `.hermes/plans/INDEX.md`
- `00_admin/audits/INDEX.md`
- `03_research/INDEX.md`

## 6. Complete repository reconciliation scope

### 6.1 Governance and entry documents

Update from verified facts:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `CHANGELOG.md`
- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `00_admin/MASTER_TASK_MATRIX.md`
- `00_admin/MASTER_TASK_MATRIX.json`
- `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
- `00_admin/POST_RELEASE_BACKLOG.md`
- `00_admin/repository-index/INTEGRATION_CHECKLIST.md`

DIB-002 and DIB-003 move to completed only after their acceptance criteria are verified. DIB-004 remains partially open unless every cleanup candidate is separately proven safe. No broad cleanup is inferred from this consolidation.

### 6.2 Documentation corpus

Reconcile all 18 indexed `docs` records:

- update current authorities and current strategy documents
- add visible lifecycle banners to historical and superseded Markdown
- preserve old facts as historical facts
- keep PDFs as evidence unless their source and intended current status are proven
- never regenerate or replace a PDF merely because its prose is old
- verify all relative links and source relationships

Primary current documents include:

- `docs/00-current-production-architecture.md`
- `docs/09-extension-and-evolution-guide.md`
- `docs/07-geo-architecture-specification.md`
- `docs/copywriter-handoff-guidelines.md`
- `docs/integrations/notion-operating-model.md`
- `docs/integrations/n8n-orchestration-model.md`

### 6.3 Prompts

Audit all 14 files under `prompts/`.

Rules:

1. Never silently overwrite a prompt whose meaning was used by an accepted run.
2. Alias files may point to the current active version only when their role is explicit.
3. Historical versions such as Step-0 v1.9.0 and Intake v1.2.0 remain present and inactive.
4. Active Step-0 v1.10.0 and Intake v1.3.0 retain exact version identity.
5. A semantic change requires a new prompt version plus coordinated schema, validator, renderer, Quality Gate, fixtures, Context Package and activation review.
6. Documentation-only corrections inside executable prompts still require hash and registry review.
7. Step 3B remains a registered post-publication prompt but is not presented as an active initial-route Step Agent.

Likely synchronized files:

- `standards/runtime/official-prompt-registry.json`
- `tests/contracts/test_llm_runtime_contracts.py`
- `tests/contracts/test_output_contracts_v2.py`
- direct step contract and renderer tests named by the affected prompt

### 6.4 Agents

Audit every entry and referenced file:

- `standards/runtime/step-agent-registry.json`
- `standards/runtime/step-agent-registry.schema.json`
- `standards/runtime/worker-profiles/step-0-agent.json` through `step-4b-agent.json`
- `standards/runtime/tool-policies/step-0-agent.json` through `step-4b-agent.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/agent-tool-policy.schema.json`
- `standards/runtime/step-agent-output-envelope.schema.json`

For each of the eight agents, verify:

- unique Step ID
- active prompt ID, path, version and hash
- Worker Profile ID, version and hash
- Tool Policy ID, version and hash
- model and reasoning policy
- allowed tool and provider operations
- confirmation and cost boundary
- output contract set
- max interaction rounds
- fail-fast behavior
- Evidence and revision binding

Any semantic agent change creates a new version. Do not rewrite accepted contract meaning in place.

### 6.5 Information, standards and tests

Use the 327-entry registry as the exhaustive inventory. Reclassify every new or changed item. Do not use filesystem similarity as authority. Update standards only when implementation and tests prove the new meaning.

The consolidation must also classify all 112 tracked changes and 84 untracked files into:

- accepted implementation
- accepted authored documentation
- deterministic generated output
- immutable evidence
- local-only runtime or session material
- sensitive or environment-specific material
- unresolved item requiring Raphael

No `git add -A` or blind whole-tree staging is permitted.

## 7. Branch reconciliation design

### 7.1 Current branch table

| Branch or ref | Tip | Unique relative to current master | Required disposition |
|---|---|---:|---|
| `master` | `3f98052` | target | Advance to final consolidation commit |
| `feature/e2e-operator-workflow-system` | `3f98052` plus dirty worktree | 0 committed | Commit accepted current work, then fast-forward master |
| `docs/repository-authority-index-2026-08-22` | `47ffdf9` | 0 | Remove clean worktree and delete local branch after final verification |
| `feature/geo-enhancement-v1.4` | `18cdd66` | 0 | Already merged through PR 2, delete local branch |
| `origin/fix/schritt-2-und-doku-1.3.0` | `aa11097` | 0 | Already merged through PR 1, delete remote branch |
| `origin/wip/sprint5-operator-console-2026-08-21-0809` | `7c844ba` | 0 | Already reachable, delete remote branch |
| `wip/m08-output-quality-2026-08-23` | `568bb49` | 1 | Semantic reconciliation required before graph merge and deletion |

### 7.2 M08 unique-commit rule

Create evidence:

- `00_admin/audits/2026-08-25-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`

For commit `568bb497e57af4f7ec6dc8a13438681bbf423a55`, classify every changed path as:

- present identically
- present in a newer implementation
- intentionally superseded with authority link
- still uniquely valuable and must be integrated
- unresolved

If any uniquely valuable current behavior is missing, integrate it explicitly and verify its affected closure. If all value is present or superseded, record that proof and use a documented no-tree-change merge such as `git merge --no-ff -s ours wip/m08-output-quality-2026-08-23`. This makes the branch tip reachable without reintroducing its older tree. If meaning remains ambiguous, stop and ask Raphael before the merge.

### 7.3 Deletion rule

Before every deletion:

```bash
git merge-base --is-ancestor <branch-tip> master
```

Expected: exit code 0.

Use normal deletion, not force deletion:

```bash
git branch -d <local-branch>
git push origin --delete <remote-branch>
```

If `git branch -d` refuses, stop. Do not substitute `-D` without a new exact proof and explicit Raphael decision.

## 8. Execution plan

### Task 1: Freeze mutable runtime and capture a recovery snapshot

**Objective:** Prevent repository writes during consolidation and preserve a rollback source.

**Actions:**

1. Read canonical CL run, artifact, approval and release state.
2. Stop Operator Console and `heartweb-runtime` gracefully after readback.
3. Verify no repository-writing process remains.
4. Create a dated external snapshot under `C:/Users/offic/Documents/Projekte/Hermes/90_archive/project-snapshots/Heartweb-Claude-Desktop-SEO-Workflow/`.
5. Preserve the full dirty repository, local-only files and Git metadata without publishing secrets.
6. Verify snapshot file count and a manifest of safe hashes.

**Hard stop:** Snapshot verification failure.

### Task 2: Classify the complete dirty tree

**Objective:** Decide explicitly what enters Git.

**Actions:**

1. Export exact tracked and untracked path lists.
2. Review each top-level package against implementation, tests and registry authority.
3. Exclude `apps/operator-console/.env.production` without reading or printing values.
4. Exclude raw `00_admin/session-recovery/` exports from Git while preserving them in the external snapshot.
5. Add precise `.gitignore` rules for environment and raw recovery material.
6. Create an explicit staging allowlist.
7. Ask Raphael about any path whose intent remains ambiguous.

### Task 3: Reconcile the M08 unique commit

**Objective:** Preserve every unique branch contribution without restoring stale tree state.

**Actions:**

1. Compare the M08 commit against final current sources path by path.
2. Write the branch reconciliation report.
3. Integrate any missing current value with focused verification.
4. Record supersession evidence for older alternatives.
5. Stop for unresolved meaning.
6. Only then create the graph merge that makes the M08 tip reachable.

### Task 4: Reconcile Project State, Decisions and release truth

**Objective:** Establish one truthful current authority before editing lower-level docs.

**Files:**

- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `00_admin/MASTER_TASK_MATRIX.md`
- `00_admin/MASTER_TASK_MATRIX.json`
- `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
- `00_admin/POST_RELEASE_BACKLOG.md`

**Actions:**

1. Append DEC-0031 and DEC-0032.
2. Supersede DEC-0022 timing without deleting it.
3. Record Step-0 release and paused Step-1 state.
4. Separate repository integration from Production acceptance.
5. Reconcile DIB-002 and DIB-003 only when their acceptance criteria are met.
6. Preserve DIB-004 cleanup candidates unless individually proven.

### Task 5: Reconcile every entry document and docs record

**Objective:** Make public, operator and agent documentation agree with current authority.

**Actions:**

1. Update `AGENTS.md`, `CLAUDE.md`, `README.md` and `CHANGELOG.md`.
2. Update all current docs authorities and strategies.
3. Add or correct visible lifecycle banners on historical and superseded docs.
4. Preserve old details as historical, not current.
5. Verify every docs file has a registry classification.
6. Preserve PDFs unless a separate source-linked regeneration is proven necessary.

### Task 6: Reconcile all prompts

**Objective:** Align executable instructions and prompt metadata without breaking reproducibility.

**Actions:**

1. Build a 14-file prompt lifecycle matrix.
2. Verify all 9 official registry entries and hashes.
3. Verify Intake v1.3.0 and its historical v1.2.0 predecessor.
4. Verify Step-0 v1.10.0 and historical v1.9.0.
5. Make aliases explicit.
6. For every semantic mismatch, create a new version instead of overwriting.
7. Update immediate contracts, validators, renderers, gates and fixtures only when semantics change.
8. Run the directly affected prompt dependency closure.

### Task 7: Reconcile all Step Agents

**Objective:** Make each active agent contract reproducible and documented.

**Actions:**

1. Validate registry, Worker Profiles and Tool Policies against schemas.
2. Recompute and verify record hashes.
3. Verify prompt and output-contract cross-bindings.
4. Verify Tool Policy operations against MCP and Provider Gateway implementations.
5. Verify Step 3B is clearly post-publication and outside the initial eight-agent route.
6. Version any semantic correction.
7. Run agent registry, tool identity, scope, failure envelope, Evidence and deterministic hash tests.

### Task 8: Implement the deterministic onboarding compendium

**Objective:** Provide one reliable new-session file without creating a competing authority.

**Actions:**

1. Add `00_admin/ONBOARDING_REFERENCE.md` to generated outputs.
2. Add a deterministic onboarding renderer to `scripts/build_repository_index.py`.
3. Update bootstrap and repository index navigation.
4. Add tests for source order, source hashes, complete inventory, no recursion, no forbidden dashes, no sensitive paths and link resolution.
5. Generate twice and require byte-identical output.

### Task 9: Refresh external project pointers

**Objective:** Keep the central Hermes and Agency Workbench routers accurate without duplicating repo content.

**Files outside this Git repository:**

- `C:/Users/offic/Documents/Projekte/Hermes/04_projects/PROJECT_REGISTRY.md`
- `C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Agency-Workbench/00_admin/PROJECT_REGISTRY.md`

Only update status and canonical pointer. Do not copy repository history into the Workbench.

### Task 10: Focused verification under the binding test policy

**Objective:** Verify the changed dependency closures and release metadata without an unauthorized complete-suite restart.

**Required commands or equivalents:**

```bash
python -m unittest -v tests.test_repository_index
python scripts/build_repository_index.py --check
python -m unittest -v tests.contracts.test_llm_runtime_contracts
python -m unittest -v tests.test_mcp_tool_identity tests.test_agent_tool_call_scope
python -m unittest -v tests.test_step_agent_deterministic_hashes tests.test_step_agent_failure_envelope tests.test_step1_agent_evidence_bundle
npm run build
hermes verify --json
git diff --check
```

Run prompt-specific validator and renderer tests only for prompt semantics that changed. Run the exact affected Operator Console component tests for UI changes already present. Retain earlier green baselines for unrelated areas. Do not run `python tests/run_full_suite.py` without separate explicit authorization.

Additional release checks:

- staged secret and credential scan
- no customer workspace path in Git
- no `.env` file staged
- no raw session export staged
- no Em Dash or En Dash
- generated index drift zero
- all Default-Retrieval links resolve
- all prompt, agent and contract hashes match bytes
- open P0 and P1 list explicit

### Task 11: Commit authored sources, then generated views

**Objective:** Keep the index source commit exact and auditable.

**Sequence:**

1. Verify Git author is Raphael Rechberger.
2. Stage only explicit accepted paths.
3. Commit implementation and authored source changes in focused, reviewable commits.
4. Include the branch reconciliation report and this plan.
5. Run the repository index generator from the final authored-source commit.
6. Commit only generated registry, index, bootstrap and onboarding views in the final metadata commit.
7. Verify generated `source_commit` equals the authored-source parent commit and all source hashes match.

Do not use `git add -A`.

### Task 12: Integrate and push master

**Objective:** Publish the verified truthful baseline.

**Sequence:**

```bash
git switch master
git merge --ff-only feature/e2e-operator-workflow-system
git push origin master
```

If fast-forward fails, stop and inspect. Do not force push or rewrite history.

Verify externally:

```bash
git ls-remote origin refs/heads/master
gh repo view --json defaultBranchRef,url
gh api repos/Frater418/claude-desktop-seo-workflow-production/commits/master
```

The local and remote SHA must match exactly.

### Task 13: Retire all reconciled non-master branches

**Objective:** Leave only verified master before creating the new continuation branch.

**Sequence:**

1. Re-run ancestor proof for every local and remote branch tip.
2. Remove the clean documentation worktree.
3. Delete merged local branches with `git branch -d`.
4. Delete remote branches:
   - `fix/schritt-2-und-doku-1.3.0`
   - `wip/m08-output-quality-2026-08-23`
   - `wip/sprint5-operator-console-2026-08-21-0809`
5. Verify `git ls-remote --heads origin` lists only `refs/heads/master`.
6. Verify no second worktree remains.

### Task 14: Create and verify the fresh clone

**Objective:** Continue from a clean repository while preserving the old dirty source as a rollback artifact.

**Recommended path strategy:**

1. Clone remote master into a temporary sibling folder.
2. Verify clone HEAD equals the remote master SHA.
3. Run `git fsck --full`, `git status --short` and repository-index check.
4. Move the old repository to the dated external snapshot location.
5. Move the verified fresh clone into the unchanged canonical path:
   - `C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow`
6. Restore only required local runtime configuration without staging it.
7. Create and push:

```bash
git switch -c feature/production-workflow-continuation
git push -u origin feature/production-workflow-continuation
```

8. Verify the new branch starts exactly at consolidated master.
9. Verify remote now contains exactly `master` and the new continuation branch.

### Task 15: Reattach runtime and resume the real workflow

**Objective:** Continue the existing CL workflow from the fresh codebase without creating a new project or losing canonical state.

**Actions:**

1. Start Operator Console and `heartweb-runtime` from the new clone.
2. Verify health endpoints from current profile configuration rather than hardcoded ports.
3. Read back the external CL project state.
4. Verify Step-0 release still exists.
5. Verify Step-1 Run `run-next-7f7e2b778f4521b9` remains `in_progress` unless canonical state proves otherwise.
6. Verify no provider call was created during consolidation.
7. Resume Step-1 production only after the normal production and tool approval gate.

## 9. Verification and acceptance matrix

The consolidation is accepted only when:

- [ ] Every tracked and untracked path has a disposition.
- [ ] No secret, `.env`, raw session export or customer workspace is staged.
- [ ] DEC-0031 and DEC-0032 exist and old decisions remain traceable.
- [ ] Current Project State reflects released Step 0 and paused Step 1.
- [ ] All 18 docs records have correct lifecycle and current claims.
- [ ] All 14 prompt files are classified.
- [ ] All 9 workflow prompt registry entries validate and hash-match.
- [ ] All 8 Step Agents, Worker Profiles and Tool Policies validate and hash-match.
- [ ] Step 3B is clearly post-publication and not falsely presented as an initial-route agent.
- [ ] `ONBOARDING_REFERENCE.md` is deterministic and complete by its content contract.
- [ ] Every registry entry appears in the onboarding inventory.
- [ ] No historical or evidence record enters Default Retrieval.
- [ ] Repository index generation and check both pass.
- [ ] Focused tests, Console build and `hermes verify --json` pass or a concrete blocker is reported.
- [ ] M08 unique commit is integrated or explicitly blocked for Raphael.
- [ ] Final master contains every retired branch tip.
- [ ] Remote master SHA equals local master SHA.
- [ ] All old non-master branches are gone locally and remotely.
- [ ] The old workspace exists in a verified external snapshot.
- [ ] The fresh clone is clean and at the canonical path.
- [ ] The new continuation branch starts at exact consolidated master.
- [ ] The external CL project and Step-1 state remain readable.
- [ ] No statement claims Production acceptance before the real route proves it.

## 10. Rollback

Before push:

- reset only by switching back to the preserved pre-consolidation branch or external snapshot
- never rewrite shared remote history

After master push but before branch deletion:

- all prior tips remain available as branches and through the master graph

After branch deletion:

- all deleted tips must already be reachable from master
- the external full workspace snapshot remains the filesystem rollback source
- GitHub master remains the remote source of truth

After fresh clone replacement:

- restore the archived old workspace only if clone verification or runtime reattachment fails
- do not delete the archive during this operation

## 11. Explicitly out of scope

- completing the real Step-1 production result before repository consolidation
- claiming PT-03 or PT-11 complete
- live Notion or live n8n implementation
- deployment
- broad code cleanup unrelated to safe consolidation
- deleting historical docs, audits, plans, PDFs or recovery sources
- force-pushing or rewriting Git history
- running the complete repository suite without separate authorization
- changing customer facts or customer workspace records during documentation reconciliation

## 12. Execution gate

No implementation, commit, merge, push, branch deletion, clone swap or runtime resume begins until Raphael accepts:

1. the generated onboarding scope
2. the canonical-path fresh-clone strategy
3. the semantic M08 reconciliation rule
4. the truthful-master rule that does not claim Production acceptance
