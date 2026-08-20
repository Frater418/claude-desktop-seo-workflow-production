# Sprint 5 Package 1 Operator Console Vertical Slice

Date: 2026-08-20
Author: Raphael Rechberger
Status: complete for Tasks 5.1 through 5.5 only

## Scope

This package creates the first visible Heartweb Operator Console vertical slice in `apps/operator-console`. It provides a React 18, TypeScript, and Vite application with a strict local simulation mode, real browser API transport, a project dashboard, the initial workflow route, the separate 3b sideflow, and selected-step detail.

The work stops after master-plan Tasks 5.1, 5.2, 5.3, 5.4, and 5.5. Artifact preview and diff, run history, task queue, Review Center, integration center, presentation matrix, commands, and all enabled human mutations remain outside this package.

## Package Versions

Runtime measured during validation:

```text
Node.js v22.23.2
npm 10.9.8
```

Pinned direct package versions:

```text
react 18.3.1
react-dom 18.3.1
@testing-library/jest-dom 6.6.3
@testing-library/react 16.0.1
@types/react 18.3.12
@types/react-dom 18.3.1
@vitejs/plugin-react 6.1.0
jsdom 25.0.1
typescript 5.7.2
vite 8.2.2
vitest 4.1.11
@rolldown/binding-linux-x64-gnu 1.2.5
@rolldown/binding-win32-x64-msvc 1.2.5
@rollup/rollup-linux-x64-gnu 4.62.4
@rollup/rollup-win32-x64-msvc 4.62.4
```

## Mode Semantics

`?mode=demo` is the sole simulation activation string. It renders the visible label `Local simulation`, a client-neutral Northwind Facilities rollout, a current architecture gate, one navigation conflict blocker, pending tasks, current artifacts, a pending review, and explicitly simulated Notion and n8n badges.

Every other search string is real API mode. This includes an empty search, reordered parameters, repeated parameters, additional parameters, and different casing. Real API mode never auto-switches to simulation data.

## Real API Behavior

`src/api/client.ts` imports only generated API types and uses browser `fetch` with `AbortSignal`, URL-encoded tenant IDs, a same-origin default base URL, and optional Vite environment configuration. Normal mode calls `GET /readyz`, then `GET /v1/tenants/{tenant_id}/projects` using the configured tenant or the explicit neutral default `tenant-local`.

The generated `DataEnvelope.data` remains `unknown` at the boundary. The console accepts a real project-list array only as transport evidence and does not invent a projection interface. Network, non-2xx, invalid envelope, and unparseable project-list responses render an explicit unavailable state with no simulated data.

The local simulation can be started with:

```text
cd apps/operator-console
npm run dev -- --host 127.0.0.1
```

Open the reported local URL with `?mode=demo` appended.

## Package Files

The Package 1 working tree contains these new console and report files:

- `apps/operator-console/index.html`
- `apps/operator-console/package.json`
- `apps/operator-console/package-lock.json`
- `apps/operator-console/tsconfig.json`
- `apps/operator-console/vite.config.ts`
- `apps/operator-console/src/main.tsx`
- `apps/operator-console/src/App.tsx`
- `apps/operator-console/src/App.test.tsx`
- `apps/operator-console/src/styles.css`
- `apps/operator-console/src/api/client.ts`
- `apps/operator-console/src/dev/neutralDemo.ts`
- `apps/operator-console/src/features/projects/ProjectDashboard.tsx`
- `apps/operator-console/src/features/workflow/WorkflowTimeline.tsx`
- `apps/operator-console/src/features/workflow/StepDetail.tsx`
- `apps/operator-console/src/test/setup.ts`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-5/01_OPERATOR_CONSOLE_VERTICAL_SLICE.md`

`.gitignore` is updated only with the scoped `apps/operator-console/node_modules/`, `apps/operator-console/dist/`, and `apps/operator-console/coverage/` entries while preserving every original line. The pre-existing generated `apps/operator-console/src/generated/api-types.ts` remains byte-unmodified. No backend, OpenAPI, generated type, Project State, plan, Control Map, future UI feature, or unrelated PDF was modified by Package 1.

## Validation

The initial lock-generation attempt encountered a transient clean-install failure:

```text
npm ci
Exit 1
EUSAGE: Missing caniuse-lite@1.0.30001809 from lock file
```

The root cause was a stale `node_modules/.package-lock.json`. Its stale `node_modules/caniuse-lite` record contained only `{ "dev": true }`, which led to an incomplete generated lock entry. After explicit user authorization, only the untracked `node_modules` tree and malformed untracked `package-lock.json` were removed.

The controller then found npm audit findings in the originally pinned Vite 5 and Vitest 2 lines. The dev toolchain was upgraded to Vite 8.2.2, Vitest 4.1.11, and @vitejs/plugin-react 6.1.0. Exact Windows x64 and Linux x64 Rollup and Rolldown bindings are declared as optional dependencies to avoid npm optional-platform resolution drift across Host and OMO. React and application behavior were not changed.

Windows npm generated directory junctions instead of executable `.cmd` shims in `node_modules/.bin`. Package scripts therefore call the pinned local Node CLI entry points directly. Vitest uses its supported threads pool because the Windows fork pool failed transitive module resolution in the mounted workspace.

Final controller commands:

```text
cd apps/operator-console && npm install --ignore-scripts --no-audit --no-fund
Exit 0. Platform-specific native bindings installed.

cd apps/operator-console && npm audit --audit-level=moderate
Exit 0. 0 vulnerabilities.

cd apps/operator-console && npm test
Exit 0. 1 test file passed, 11 tests passed.

cd apps/operator-console && npm run build
Exit 0. TypeScript strict check passed. Vite 8.2.2 built 20 modules in 262ms.

python scripts/generate_operator_api_contracts.py --check
Exit 0 with no output.

isolated temp copy && npm ci --ignore-scripts --no-audit --no-fund
Exit 0. 145 packages installed from the final lockfile.

isolated npm audit, npm test, npm run build
Exit 0. 0 vulnerabilities, 11 tests passed, Vite 8.2.2 production build passed.
```

Focused tests cover exact demo activation, non-demo no-fallback behavior, the exact initial route and separate 3b sideflow, click selection, closed technical disclosure, and disabled preview actions.

TypeScript LSP diagnostics were unavailable because the TypeScript language server is not installed and installation was previously declined. The production TypeScript compiler check passed through `npm run build`.

## Browser QA

The controller opened the real Vite application in explicit `?mode=demo` mode and rendered desktop, tablet, and mobile views with local Chrome. Desktop and tablet passed without overlap or horizontal overflow. The first mobile screenshot appeared clipped because Chrome CLI enforced a 504-pixel minimum layout viewport before cropping. Chrome CDP was then used for a real 390 by 844 pixel mobile emulation.

The mobile layout was improved with zero-minimum grid sizing and a one-column metrics layout. Final CDP measurements:

```text
viewport width: 390
document scrollWidth: 390
app right edge: 390
dashboard: left 14, right 376
next action: left 29, right 361
metrics: left 29, right 361
```

The final mobile screenshot passed visual inspection with no clipped text, card overflow, or undersized timeline controls. The local demo remains available at `http://127.0.0.1:4173/?mode=demo` while the tracked development server process is running.

## Limitations

- Real API projections are not rendered beyond transport availability because the generated API contract intentionally exposes `data` as `unknown`.
- Simulation integrations are explicitly local and simulated. They are not production or live integrations.
- Preview buttons are disabled and make no command API calls.
- The final audit reports zero vulnerabilities. npm emits one deprecation warning for transitive `whatwg-encoding@3.1.1`.
