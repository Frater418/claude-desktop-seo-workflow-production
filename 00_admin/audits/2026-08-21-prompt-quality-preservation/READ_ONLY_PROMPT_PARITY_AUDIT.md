# Read-only Prompt Quality Preservation Audit

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Date:** 2026-08-21
**Mode:** Read-only comparison. No prompt, schema, service, test, branch, or runtime was changed by this audit.

## Executive Verdict

The V2 migration is architecturally necessary and materially improves state integrity, evidence, provider safety, tenant binding, revision safety, human approval, and reproducibility. It is not a failed architecture and must not be rolled back wholesale.

The migration is not yet quality-complete. Several output-quality requirements from the original Desktop Promptworkflow and the version 1.4 repository prompts were not mapped to enforceable V2 schema, validator, renderer, gate, and UI requirements. The final product must not claim complete prompt parity or production output quality until those gaps are restored through the existing V2 seams.

## Compared Sources

1. Original workflow files under `C:\Users\offic\Desktop\Heartweb\Promptworkflow`.
2. Repository prompts at master commit `5e786790d84af3c6fba57c3b3f3c1834b74a9a61`.
3. Current Feature and WIP prompts at `3ed76b1` and `7c844ba1`.
4. V2 output schemas under `standards/outputs/`.
5. Preflight validators and renderers under `services/step*_preflight/`.
6. Capacity solver, Provider Gateway, Quality Gate Registry, master audit, master E2E plan, DIB-001, and DEC-0020.

## Git Baseline

- `origin/master`: `5e786790d84af3c6fba57c3b3f3c1834b74a9a61`
- Feature prompt commit: `a3b8ea1f50fd222bc5d024569e0d5776bd1b640a`
- Current Feature HEAD: `3ed76b1a7962db168dc5b5325adcdc8220aa1de5`
- WIP checkpoint: `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`
- `master` is an ancestor of Feature. All old repository prompt versions remain reachable after a later fast-forward.
- Feature and WIP contain the same prompt versions. The current Working Tree has no additional prompt modifications.
- Master to Feature prompt diff: 301 insertions and 597 deletions across all nine prompts.

## Why the Migration Happened

The fundamental audit identified production blockers in prompt-controlled state, direct provider access, geo defaults, unsupported claims, Local SEO assertions, stale approvals, missing lineage, prose-only output contracts, and non-enforceable Human Gates. The binding architectural decision was to make prompts bounded candidate generators while schemas, services, gates, evidence, and transitions enforce correctness.

This direction is stated in `00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md`: the largest problem was that quality rules existed only as prose, and the required transition was from nine large prompts to versioned Domain and State Machine transforms.

The migration defect was specification incompleteness. The new migration task list covered state and safety comprehensively but did not map every original editorial, SEO, conversion, presentation, and handoff requirement to a required V2 target. Reviews correctly verified the new task plan, but the task plan itself did not contain full baseline quality parity.

## Per-Prompt Verdict

| Step | Verdict | Preserved or improved | Missing or incomplete |
|---|---|---|---|
| 0 | improved | intake, geo, semantic separation, schema, preflight, explicit Gate 0 | no material baseline quality loss found |
| 1 | improved | content inventory, pillars, gaps, cluster candidates, intent, information gain, conversational patterns, evidence | no material baseline quality loss found |
| 1b | core improved, delivery view reduced | exact content decision, URL, canonical, navigation, redirect, vertical and horizontal links | interactive customer-presentable menu tree, badges, legend, design quality, explicit open-decision presentation |
| 1c | incomplete | design tokens, accessibility, location safety, JSON-LD references, links | full pillar template structure: hero, CTA, quick facts, editorial depth, unique heartpiece, grouped clusters, process, social proof, FAQ, crosslinks, final CTA |
| 2 | production contract gap | Provider Gateway, raw hashes, geo, cost, job identity, 25 verified rows | research breadth, typed search volume, difficulty, CPC, category, content type, GEO type, information gain, entity density, business relevance, mandatory location flag |
| 3 | solver preserved, input bridge incomplete | effort weights, priority factors, GEO factors, mandatory placement, 17 weeks, backlog, link maps | released Step-2 projection does not provide the real solver's required metrics and classifications |
| 3b | revision safety improved, semantics incomplete | source plan immutability, new revision, hash, external gate | minimum age, performer/stagnant/underperformer classification, local-page special rule, cause diagnosis, capacity and mandatory-location adjustment rules |
| 4a | known mandatory restoration | Provider Gateway, SERP evidence, claims, reviewer policy, Claim Ledger, JSON-LD hash, Notion projection | complete Copywriter briefing, Hero Direct Answer, Semantic Triples, Evidence Containers, evidence data, definitive language, enhanced Wikidata binding |
| 4b | known mandatory restoration | Page Spec, hash, consent, tracking, service-area safety, staging evidence | enforceable semantic sections, visible GEO components, section-to-JSON-LD binding, complete conversion and Local SEO page structure |

## Critical Cross-Step Finding

`standards/outputs/step-2-keyword-evidence.schema.json` and `services/step3_preflight/validator.py::step2_solver_projection` do not provide search volume, difficulty, category, content type, or mandatory location values. `mcp/tools/capacity_matrix_solver.py` requires those fields. Neutral tests currently use a simulated Step-3 output, so they prove lifecycle plumbing but not the real Step-2-to-Step-3 production solver path.

This is a blocking production contract gap for a real AHD Step 2 and Step 3 run.

## Existing Known Restoration

DIB-001 and `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` already cover the confirmed Step-4a and Step-4b GEO and handoff gaps. This audit extends the required parity scope to Step 1b presentation, Step 1c template quality, Step 2 and Step 3 data compatibility, and Step 3b performance semantics.

## Preservation Evidence

All nine repository prompts exist at:

- initial rollout commit `a10093bd7503a2063c809293b8bafdca27d443f4`
- GEO 1.4 commit `c818ffc5487e17a9a5b7096ac48dd443aaa8eb89`
- master commit `5e786790d84af3c6fba57c3b3f3c1834b74a9a61`

The original Desktop workflow contains nine source files, including the overview and combined Step 4. A separate immutable archive and hash manifest are created outside the active repository before any restoration work.

## Required Outcome

Do not revert to the old prompt-controlled architecture. Extend the current V2 schemas, validators, renderers, gates, and Admin review surfaces so every approved original quality requirement has one enforceable target and one positive and negative proof.

The restoration is complete only when:

1. a baseline requirement matrix has no unexplained removed requirement;
2. the real Step-2-to-Step-3 data and solver path runs with real typed metrics;
3. 1b and 1c produce professional customer and developer artifacts;
4. 3b applies the approved performance decision rules;
5. 4a and 4b satisfy DIB-001;
6. neutral and real AHD outputs pass machine and human quality review;
7. the final audit distinguishes contract validity from customer-facing output quality.
