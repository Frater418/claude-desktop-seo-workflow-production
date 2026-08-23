# Project State: Heartweb SEO and GEO Production Workflow

**Author:** Raphael Rechberger
**Status:** active
**Updated:** 2026-08-22
**Canonical file:** `00_admin/PROJECT_STATE.md`

## Current goal

Reach the first controlled local Production output as quickly as possible without sacrificing data integrity, professional output quality or deterministic Delivery.

The first output must turn a real customer briefing into an approved customer concept, role-specific handoffs, secure ZIP package and manual Notion implementation project.

## Product definition

Heartweb is a client-neutral local Core with a German Single-Admin Console.

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Human Copywriters write final editorial content. After Delivery, Notion owns human implementation tasks. The only planned post-handoff Core loop is Step 3B at day 30, 60 and 90.

## Implemented and verified foundation

- V2 domain and workflow contracts
- Transition Service as canonical state authority
- Context Packages and LLM Run Records
- Provider Gateway and Evidence boundaries
- immutable artifacts and revisions
- Quality Gates, approvals and releases
- recovery, replay and structured fail-fast errors
- Local Operator API
- German Single-Admin Console
- real browser-tested core actions
- Notion and n8n simulators with no live claim
- isolated prompt-quality baseline and parity audit

## Current execution state

As of the morning snapshot on 2026-08-22:

- release-critical Browser QA is complete
- Sprint-5E Delivery Tasks 1 through 5 are independently accepted
- Delivery API Task 6 is in bounded remediation after independent review found real integrity issues despite a green full suite
- Delivery Center Task 7 is pending
- neutral Delivery E2E Task 8 is pending
- no live Notion, n8n or deployment work is release-blocking

Volatile test totals and Task-6 completion status must be refreshed from current evidence before integration or external reporting.

## Pre-release sequence

1. Finish Delivery API remediation and independent verification.
2. Build German Delivery Center.
3. Prove neutral local Delivery E2E.
4. Implement minimal shared diagnostic trace from DIB-005.
5. Complete bounded PQ-0, PQ-1, PQ-2 and PQ-4 output restoration.
6. Run targeted local Production Release audit.
7. Run first real customer Golden Path until explicit Human Gates require Raphael.

## Active decisions

- DEC-0012: Notion remains the central operative company workspace.
- DEC-0015: local Notion and n8n behavior is simulated only.
- DEC-0019: stateful project, replaceable worker.
- DEC-0022: branch consolidation only after the final gate.
- DEC-0024: Production-first cut-line.
- DEC-0025: one complete Notion project handoff, no daily staff-task callbacks, Step 3B only at day 30, 60 and 90.

Full rationale is in `00_admin/DECISIONS.md`.

## Current authorities

- `00_admin/DECISIONS.md`
- `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
- `00_admin/POST_RELEASE_BACKLOG.md`
- `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
- `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md` after final branch refresh
- `docs/00-current-production-architecture.md`
- `docs/09-extension-and-evolution-guide.md`

## Active risks

1. Real Step 2 requires verified market-correct provider access. No substitute metrics.
2. Step-2-to-Step-3 typed metrics and solver projection require release-critical restoration.
3. Step 1B/1C and Step 4A/4B must regain approved professional output depth.
4. Delivery API remediation must pass full verification after the latest changes.
5. AHD real input, provider access and Human Gates may block the first Golden Path.
6. Documentation branch facts must receive one final refresh from the stable Feature commit before integration.

## Post-release

- live one-way Notion project creation
- live n8n orchestration
- complete Step 3B before first day-30 checkpoint
- public deployment adapters
- broad international and archetype expansion
- additional mobile polish
- repository cleanup and presentation expansion

See `00_admin/POST_RELEASE_BACKLOG.md`.

## Parallel documentation branch

Repository authority and RAG indexing is built in the isolated branch:

`docs/repository-authority-index-2026-08-22`

The branch uses stable WIP commit `7c844ba1` as its initial base. Before integration it must be updated from the final stable Feature commit, refreshed against current Project State and Decisions, regenerated and reverified.

## Working rules

- Raphael Rechberger is sole author.
- No Em Dash or En Dash characters.
- No silent fallback or estimated provider values.
- No commit, push, merge or deployment without explicit approval.
- Active Sisyphus worktree remains untouched by parallel documentation work.
- Historical evidence remains immutable and opt-in for retrieval.
