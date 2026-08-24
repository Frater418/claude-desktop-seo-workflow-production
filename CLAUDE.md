# CLAUDE.md: Heartweb V2 quick operating contract

**Author:** Raphael Rechberger
**Status:** Current V2 agent authority
**Updated:** 2026-08-22

## Read first

1. `00_admin/SESSION_BOOTSTRAP.md`
2. `00_admin/PROJECT_STATE.md`
3. `00_admin/DECISIONS.md`
4. `00_admin/REPOSITORY_INDEX.md`
5. the active task plan from `.hermes/plans/INDEX.md`
6. before any test or review decision, `standards/testing/PROTOTYPE_TEST_POLICY.md`

Current Project State and active Decisions override old docs, old plans and audit prose. Historical, superseded and evidence records are opt-in context only.

`standards/testing/PROTOTYPE_TEST_POLICY.md` is the binding Production-first test authority. It preserves prior green baseline evidence and selects tests only for the proven affected dependency closure. Without new explicit Raphael authorization, do not run the complete repository suite, restart a passed matrix after a later-cell failure, or launch repeated broad multi-agent review rounds.

## Product

Heartweb is a client-neutral local SEO and GEO production Core with a German Single-Admin Console. It turns verified client inputs into strategy, architecture, keyword evidence, a 120-day roadmap, Copywriter briefings, Developer specifications and deterministic Delivery packages.

Human Copywriters write the final editorial copy. External team members work from files and Notion, not from the Admin Console.

## Workflow

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B runs separately at day 30, 60 and 90 using verified post-publication performance data.

## Authority

- Transition Service is the only canonical workflow state writer.
- Prompts create candidates and never approve or complete steps.
- Provider calls go through Provider Gateway with explicit market, code and language.
- Released artifacts are immutable. Changes create new revisions.
- Delivery is deterministic and read-only with respect to Core state.
- Notion owns staff execution after final handoff.
- Post-handoff Notion task changes do not call the Core.
- n8n later orchestrates the concept workflow, Notion handoff and Step-3B checkpoints. It never owns business state.

## Fail-fast

Never guess missing metrics, facts, claims, locations, Evidence, IDs, revisions or approvals. Stop with a stable error code and remediation. Preserve the last valid canonical state.

Never present simulated output as live or production Evidence.

## Extensibility

Prompt and tool changes are allowed through versioned resources. A semantic output change requires coordinated prompt, schema, validator, renderer, gate, fixtures, Context Package and activation review.

Contracts guarantee accepted structure, identity, lineage and persistence. They reduce and expose hallucination risk but cannot guarantee semantic truth or excellent output alone.

See `docs/09-extension-and-evolution-guide.md`.

## Project separation

Shared runtime and prompts remain client-neutral. Customer facts, claims, regions, branding, Evidence and design remain in isolated customer workspaces. AHD is a pilot fixture, not shared product logic.

## Git and agents

Do not commit, push, merge, deploy or rewrite history without explicit Raphael authorization. Parallel work uses an isolated worktree.

When OpenCode OMO is active, Hermes communicates only with root Sisyphus. Do not control child sessions. Native Hermes subagents require explicit Raphael authorization.

## Writing

Raphael Rechberger is the sole author. Never use Em Dash or En Dash characters. Clearly label implemented, verified, simulated, planned, deferred and absent behavior.
