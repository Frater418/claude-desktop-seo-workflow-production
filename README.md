# Heartweb SEO and GEO Production Workflow

**Author and architecture:** Raphael Rechberger
**Organization:** Heartweb
**Status:** Production-first V2 development
**Updated:** 2026-08-22

Heartweb turns a verified customer briefing into a structured, reviewable and deliverable SEO and GEO implementation project.

The system is designed to replace a manual chain of prompts, spreadsheets, file copying and task creation with one controlled workflow. It produces the strategic and technical foundation. Human Copywriters create the final editorial content, and developers implement the approved specifications.

## What Heartweb produces

A completed local workflow can produce:

- validated Project V2 customer context
- Pillar and cluster strategy
- page, menu and URL architecture
- reusable design tokens and Pillar templates
- verified keyword and provider Evidence
- deterministic 120-day roadmap
- internal-linking maps
- professional Copywriter briefings
- Developer page specifications and HTML
- implementation tasks, priorities, assignees and deadlines
- Copywriter, Developer and Project Management packages
- manual Notion import project
- deterministic ZIP archives with manifests and checksums

## Product flow

```text
Customer briefing
-> Heartweb Admin Console
-> Core workflow 0 to 4B
-> review, revision and Human Gates
-> Delivery packages
-> Notion implementation project
-> human execution by the Heartweb team
```

After handoff, Notion owns daily implementation work. Staff task changes do not resume or mutate the Core.

At day 30, 60 and 90, Step 3B compares the released strategy and plan with verified real performance data and proposes adjustments for future work.

## Architecture

```text
German Single-Admin Console
        |
        v
Operator API -> Heartweb Core -> Provider Gateway and deterministic tools
        |              |
        |              v
        |        artifacts, revisions, Evidence, gates and releases
        v
Delivery Service -> role packages, Notion import and secure ZIP

Future n8n:
UI and schedules -> typed Core commands -> Notion handoff -> Step-3B checkpoints
```

Only the Transition Service writes canonical workflow state. The Console, Notion and n8n never duplicate that logic.

Read the full architecture at [`docs/00-current-production-architecture.md`](docs/00-current-production-architecture.md).

## Current state

Implemented on the active Feature line:

- V2 domain, workflow and Transition Service
- Provider Gateway and Evidence boundaries
- immutable artifacts and revisions
- Quality Gates, approvals, releases and recovery
- Context Packages and reproducible LLM run records
- Local Operator API and append-only events
- German Single-Admin Console
- real browser-tested core actions
- Sprint-5E Delivery contracts and services under active completion

Still required before the first controlled local Production output:

- complete Delivery API, Delivery Center and Delivery E2E
- minimal shared diagnostic trace
- release-critical output restoration for Steps 1B/1C, 2/3 and 4A/4B
- targeted Production Release audit
- one real customer Golden Path

Post-release:

- live Notion adapter
- live n8n orchestration
- complete Step-3B implementation before the first day-30 checkpoint
- public deployment adapters
- broad international and multi-archetype expansion
- additional mobile polish and repository cleanup

Current mutable status is always in [`00_admin/PROJECT_STATE.md`](00_admin/PROJECT_STATE.md).

## Repository navigation

Start every new human or LLM session with:

1. [`00_admin/SESSION_BOOTSTRAP.md`](00_admin/SESSION_BOOTSTRAP.md)
2. [`00_admin/PROJECT_STATE.md`](00_admin/PROJECT_STATE.md)
3. [`00_admin/DECISIONS.md`](00_admin/DECISIONS.md)
4. [`00_admin/REPOSITORY_INDEX.md`](00_admin/REPOSITORY_INDEX.md)
5. [`.hermes/plans/INDEX.md`](.hermes/plans/INDEX.md)

Machine-readable retrieval sources:

- [`DOCUMENT_REGISTRY.json`](00_admin/repository-index/DOCUMENT_REGISTRY.json)
- [`DOCUMENT_REGISTRY.jsonl`](00_admin/repository-index/DOCUMENT_REGISTRY.jsonl)
- [`document-registry.schema.json`](standards/documentation/document-registry.schema.json)

Area indexes:

- [`docs/INDEX.md`](docs/INDEX.md)
- [`00_admin/audits/INDEX.md`](00_admin/audits/INDEX.md)
- [`03_research/INDEX.md`](03_research/INDEX.md)

## Workflow steps

| Step | Purpose | Main output |
|---|---|---|
| 0 | Intake and Project V2 | validated customer project |
| 1 | Pillar and topic inventory | strategic topic model |
| 1B | page and navigation architecture | architecture and menu view |
| 1C | design system and Pillar templates | reusable page structure |
| 2 | provider-backed keyword research | verified keyword Evidence |
| 3 | deterministic capacity plan | 120-day roadmap and links |
| 4A | Copywriter briefing | editorial implementation package |
| 4B | Developer page specification | HTML, schema and technical handoff |
| Delivery | deterministic handoff | ZIP, role packages and Notion import |
| 3B | later performance adaptation | versioned adjustment proposal |

## Extending the system

Prompts, providers, tools, schemas and workflow steps can be extended through versioned contracts. Old accepted runs remain bound to their original prompt, schema, model, tool policy, Evidence and artifact hashes.

See [`docs/09-extension-and-evolution-guide.md`](docs/09-extension-and-evolution-guide.md).

## Quality model

Contracts protect:

- required structure
- customer and project identity
- revision and hash integrity
- Evidence references
- workflow ordering
- deterministic persistence

Contracts do not guarantee semantic truth or excellent writing by themselves. Heartweb combines strong prompts, verified sources, tool results, validators, behavioral tests and human approval.

## Framework and customer data

This repository contains the client-neutral Core. Customer-specific facts, claims, services, regions, design and Evidence belong in isolated customer workspaces and must never be committed to the framework repository.

AHD is the Golden-Path pilot and must not become hardcoded shared behavior.

## Integrations

- Current first release: local Core, files, ZIP and manual Notion import
- Future Notion: one-way creation of the customer implementation project
- Future n8n: orchestration, provider waits, retries, Notion handoff and Step-3B schedules
- OpenCode OMO: development and QA only, never production runtime

## Development and release rules

- No silent fallback or estimated provider data
- No commit, push, merge or deployment without Raphael approval
- `master` remains protected until the Production Release gate
- Historical audits and checkpoints remain immutable
- Parallel work uses isolated Git worktrees
- Raphael Rechberger is the sole author
- Em Dash and En Dash characters are forbidden

## License

Proprietary. Intended for Heartweb production use.
