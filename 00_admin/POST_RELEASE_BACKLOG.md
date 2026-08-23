# Post-Release Backlog

**Author:** Raphael Rechberger
**Status:** Active non-blocking post-release queue
**Updated:** 2026-08-22

## Authority boundary

This file schedules non-blocking work. Detailed requirements remain in the linked Decision, DIB, plan, schema or audit. It is not a second Source of Truth.

## First local Production Release

The first release requires:

1. targeted Desktop and core-action QA
2. no open P0/P1 affecting data, workflow, security, output or Delivery
3. deterministic checkpoint and final packages
4. minimal shared diagnostic trace
5. release-critical output restoration for Steps 1B/1C, 2/3 and 4A/4B
6. one targeted local Production smoke
7. one real customer Golden Path

Live Notion, live n8n, public deployment and perfect mobile polish do not block it.

## Queue

| ID | Work | Activation | Reason for deferral |
|---|---|---|---|
| PR-001 | Complete Step-3B performance semantics | Before first real day-30 checkpoint | No real performance data exists during initial production. |
| PR-002 | Full real-output parity and PQ-5 acceptance | After first real customer output | Requires real output Evidence. |
| PR-003 | Live one-way Notion project creation | After local production and database mapping | Manual Notion import provides first handoff. Daily task callbacks are out of scope. |
| PR-004 | Live n8n concept orchestration and Step-3B scheduling | After local command and event stability | Local Core runs without n8n. |
| PR-005 | Additional mobile polish | After first release | Desktop is the production surface. |
| PR-006 | Final docs-corpus and PDF reconciliation | At stable integration gate | The parallel authority-index branch performs the base work without delaying output. |
| PR-007 | Repository hygiene and dead-code cleanup | Stable post-release checkpoint | Cleanup must not disturb active production work. |
| PR-008 | Broad international and archetype expansion | After first real Golden Path | One real customer route has priority. |
| PR-009 | Jesse presentation expansion | After real outputs exist | Presentation should use real Evidence. |
| PR-010 | CMS, WordPress, Elementor and public deployment adapters | Separate approved deployment phase | First release delivers implementation-ready files. |

## Promotion rule

A post-release item becomes release-blocking only when it causes:

- data corruption or false canonical success
- illegal transition or stale approval
- tenant, secret, path or security breach
- missing or materially weak customer output
- unusable Desktop action
- nondeterministic or unsafe Delivery
- a deadline-specific dependency such as Step 3B before day 30

## Review cadence

Review this backlog after the first real customer package and before the first day-30 performance checkpoint.

Live integration must preserve DEC-0025: one complete project handoff to Notion, Notion-owned human execution and Core re-entry only for scheduled Step 3B.
