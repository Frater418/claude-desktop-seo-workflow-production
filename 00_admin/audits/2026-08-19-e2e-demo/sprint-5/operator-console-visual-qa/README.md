# Operator Console Production Visual QA

## Verdict

BLOCKED: no PASS verdict is possible. The required browser capture surface could not launch.

## Precise Defect List

1. BLOCKER-001: the required Playwright MCP browser cannot initialize because its configured Chromium channel requires `/opt/google/chrome/chrome`, which is absent. The MCP returned: `Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome`.
2. BLOCKER-002: no installed `agent-browser` or `dev-browser` fallback is exposed to this session. `agent-browser` is not an available skill or MCP server, and `/usr/local/bin/agent-browser` and `/usr/local/bin/dev-browser` do not exist.

No browser was installed. The request prohibits replacing the required installed-browser fallback with a global package installation.

## Route and Viewport Matrix

All 24 required captures are BLOCKED by BLOCKER-001 and BLOCKER-002. No screenshot, accessibility snapshot, console log, network log, layout measurement, hover, focus, active-state, keyboard, or motion observation was fabricated.

| Destination | 1280x900 | 768x1024 | 390x844 | 375x812 |
| --- | --- | --- | --- | --- |
| Projekte | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Workflow | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Aufgaben | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Artefakte | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Pruefungen und Freigaben | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Uebergabe und Export | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

## What Was Verified

- Production build completed with `VITE_OPERATOR_TENANT_ID=tenant-visual-qa` and explicit same-origin `VITE_OPERATOR_API_BASE_URL=`.
- The built JavaScript contains `tenant-visual-qa`.
- The same-origin preview served from the real local Operator API returned the production HTML shell.
- The real local Operator API reported ready and exposed two disposable canonical projects: `project-alpha` and `project-beta`.
- `project-alpha` has editable artifact revisions and task filter data. `project-beta` contains a released artifact record for lock behavior.

## Missing Evidence By Cause

- Screenshots: no browser process could render them.
- Accessibility snapshots: no browser process could expose the accessibility tree.
- Console and network logs: no browser process could load the application.
- Overflow, clipping, focus, keyboard exclusion, state styling, and motion checks: browser-only checks, not run.
- Scenario requests: no browser could issue and observe them. The API fixture was read-verified only.
- Screenshot `look_at` validation: impossible because no fresh screenshot exists.

See `build.log`, `operator-api-preview.log`, `api-readback.md`, `browser-launch-failure.md`, and `cleanup.md` for reproducible evidence.
