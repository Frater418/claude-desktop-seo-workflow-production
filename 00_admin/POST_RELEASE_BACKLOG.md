# Post-Release Backlog

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Created:** 2026-08-21
**Status:** Active non-blocking post-release queue
**Purpose:** Keep valuable work without delaying the first locally production-capable workflow and real customer output.

## Authority Boundary

This file is a scheduling projection, not a second Source of Truth. Detailed requirements remain in the linked Decision, DIB, plan, schema, or audit. If this file conflicts with those sources, the higher-authority source wins.

## First Production Release Definition

The first local Production Release exists when:

1. Desktop and core Operator actions pass targeted browser and functional QA.
2. No open P0 or P1 data-integrity, workflow, security, output-quality, or Delivery defect remains.
3. Sprint 5E produces deterministic checkpoint and handoff packages.
4. DIB-005 provides the minimal shared timestamped diagnostic trace.
5. The output-critical pre-release part of DIB-006 is verified for Step 1B/1C, Step 2/3, and Step 4A/4B.
6. One targeted production smoke test passes with the local Core and manual file handoff.
7. Live Notion, live n8n, public deployment, and perfect mobile polish are not required.

## Post-Release Queue

| ID | Work | Source authority | Activation | Why it does not block first Production Release |
|---|---|---|---|---|
| PR-001 | Full Step-3B performance semantics | DIB-006 PQ-3, original Step-3B prompt | Before the first real day-30 checkpoint | Initial production route marks Step 3B `not_due`; no real performance data exists yet. |
| PR-002 | Full real-output parity and PQ-5 acceptance | DIB-006 PQ-5 | Immediately after the first real AHD output chain | Requires real outputs and therefore cannot logically precede the first production run. |
| PR-003 | Live one-way Notion project creation for customer concept, tasks, people, priorities and deadlines | DEC-0025, current Notion operating model | After local production output is stable and target databases are confirmed | Manual Delivery and Notion import pack provide the first release handoff. Daily task callbacks to the Core are out of scope. |
| PR-004 | Live n8n orchestration for concept production, Notion handoff and scheduled Step-3B performance re-entry | DEC-0025, current n8n operating model | After local production and command/event contracts are stable | The local Core already executes without n8n. n8n does not monitor staff-task completion for Core progression. |
| PR-005 | Additional mobile polish and exhaustive mobile-only regression rounds | Operator Experience spec and QA evidence | After first release unless a mobile issue corrupts state or blocks a required review action | Desktop is the production surface. Mobile is review/status convenience only. |
| PR-006 | Full docs-corpus classification and historical PDF regeneration | DIB-002, DIB-003 and DEC-0031 | Docs classification and generated onboarding completed on 2026-08-26; historical PDF regeneration remains post-release where source parity is unproven | Current onboarding is verified; historical presentation PDFs do not block M10. |
| PR-007 | Repository hygiene, dead demo code removal, image deduplication and readability cleanup | DIB-004 | After first release at a stable checkpoint | Important maintenance, but not required to generate correct customer outputs. |
| PR-008 | Broad multi-archetype, international and portability expansion | Master plan Sprint 11 and domain fixture matrix | After the first real local Golden Path | The first release needs one proven real Golden Path, not every future archetype. |
| PR-009 | Jesse presentation expansion and complete presentation matrix | Master plan Sprint 10 | After real outputs exist | Presentation must use real production evidence rather than delaying that evidence. |
| PR-010 | CMS, WordPress, Elementor and public deployment adapters | Fundamental audit section 5.5 | Separate explicitly approved deployment phase | First release produces professional Developer files and staging-ready outputs, not a live deployment. |
| PR-011 | General LLM backend platform, direct Multi-Provider adapters, separate execution-record store, delegation contracts and model benchmark framework | DEC-0028 and Hermes Gateway LLM adapter plan | After M10 and only if real runs prove a concrete need | The first release needs one thin validated Hermes Runs adapter, not a speculative provider platform. |

## Blocking Rule

A post-release item returns to the release-blocking queue only if it causes one of the following:

- data corruption or false canonical success;
- illegal workflow transition or stale approval;
- tenant, secret, path or security breach;
- missing or materially weak customer output;
- unusable Desktop operator action;
- nondeterministic or unsafe Delivery package;
- a deadline-specific dependency such as Step 3B before day 30.

Cosmetic mobile behavior, documentation polish, repository tidiness, live integrations, broad archetype coverage, and presentation enhancements remain post-release by default.

## Review Rule

Raphael may promote any item before implementation. Otherwise the queue is reviewed after the first real AHD output package and again before the first day-30 performance checkpoint.

Live-integration implementation must preserve the DEC-0025 boundary: one complete project handoff to Notion, Notion-owned human execution, and Core re-entry only for the scheduled Step-3B performance cycle.
