# Deferred GEO V2 Contract Restoration

**Author:** Raphael Rechberger
**Date:** 2026-08-20
**Status:** Mandatory deferred remediation
**Activation gate:** Start only after the current Sprint 5 and Sprint 5E implementation is stable, independently verified, and the existing local workflow passes its completion gate.

## Purpose

Restore the concrete SEO and GEO production-quality requirements approved in session `20260817_151731_bc9488` and ADR-011 to the executable V2 contracts. The architectural intent remains present, but several Step 4a and Step 4b requirements currently exist only in specifications, ADRs, research, CSS, and historical changelog entries.

This remediation is mandatory before claiming that the real AHD Golden Path produces the complete approved GEO-quality Copywriter and Developer deliverables.

## Architectural Boundary

This work extends existing seams. It must not replace or duplicate:

- workflow graph
- Transition Service
- Context Builder
- artifact and revision storage
- approval and release authority
- Provider Gateway
- Notion and n8n command/event boundaries
- single-admin Operator Console architecture

## Canonical Sources

- Session `20260817_151731_bc9488`
- `docs/07-geo-architecture-specification.md`
- `docs/04-entscheidungslog.md`, ADR-011
- `CHANGELOG.md`, release 1.4.0
- `03_research/exa_geo_research_raw.json`
- `docs/08-geo-sprint-plan-and-multi-agent-orchestration.md`

## Verified Drift

### Step 4a

The current V2 prompt and schema do not fully require or represent:

- Hero Direct Answer with 50 to 70 words
- 15 to 20 Semantic Triples
- Evidence Containers with a target of 130 to 160 words per H2 section
- at least one concrete evidence-bearing data point or structured table per container
- definitive-language guidance
- explicit `about` and `mentions` requirements with Wikidata binding in enhanced GEO mode
- a complete copywriter-facing briefing structure beyond metadata, SERP references, claims, JSON-LD, and Notion projection metadata

### Step 4b

The current V2 page contract and validator do not fully require or enforce:

- semantic section IDs bound to the content structure
- GEO-specific markup for definition and evidence containers
- Microdata or explicitly approved equivalent semantic annotations
- correspondence between visible page sections and JSON-LD graph nodes
- preservation of the approved GEO component classes in generated HTML

### Provider Evolution

The earlier AgentSEO-primary approach has been superseded by the current provider boundary:

- DataForSEO is primary
- AgentSEO is conditionally allowed
- both are accessed only through Provider Gateway

The restoration must preserve this current architecture while retaining geo, language, raw evidence, cost, job, and hash requirements.

## Required Implementation Package

1. Extend `standards/outputs/step-4a-briefing.schema.json` with closed, typed content structures for the Hero Direct Answer, Semantic Triples, Evidence Containers, section evidence, and copywriter instructions.
2. Extend `prompts/4a-content-briefing-und-schema.xml.md` to generate the complete approved briefing structure.
3. Extend Step-4a preflight validation and rendering so invalid word ranges, missing triples, empty evidence containers, unsupported claims, or invalid enhanced GEO entity bindings fail visibly.
4. Extend `standards/outputs/step-4b-page-spec.schema.json` with the required semantic section and GEO markup bindings.
5. Extend `prompts/4b-landingpage-html.xml.md`, Step-4b validation, and rendering to preserve semantic sections, GEO components, accessibility, JSON-LD correspondence, and safe HTML.
6. Extend the Quality Gate Registry with machine-checkable Step-4a and Step-4b GEO requirements.
7. Add positive fixtures that represent a professional copywriter briefing and developer page package.
8. Add negative fixtures for missing Hero Direct Answer, invalid word count, too few Semantic Triples, missing evidence data, invalid Wikidata `about`, broken section-to-graph correspondence, and missing GEO component markup.
9. Expose all new fields in the single-admin review UI at the appropriate Step 4a and Step 4b workspaces.
10. Prove the requirements with a real AHD output and human quality review, not only neutral fixtures.

## Acceptance Criteria

- The Step-4a schema cannot validate a briefing missing any mandatory GEO content block.
- The Step-4a renderer produces a professional, directly usable Copywriter briefing with Notion-compatible frontmatter.
- The Step-4b schema and validator reject pages missing the required semantic and GEO bindings.
- Strict JSON-LD validation passes with correct `@graph`, `about`, `mentions`, and Wikidata references where required.
- The Operator Console displays, edits, revises, validates, compares, and approves the extended Step-4a and Step-4b artifacts.
- Existing lineage, revision, approval, release, Provider Gateway, and transition invariants remain green.
- A real AHD run demonstrates that the resulting Copywriter and Developer deliverables meet the approved quality standard.

## Completion Evidence

Required before closing this deferred item:

- schema diffs
- prompt diffs
- validator and renderer tests
- positive and negative fixture evidence
- full-suite result
- task-based browser QA
- real AHD Step-4a and Step-4b artifacts
- independent specification review
- independent quality review
