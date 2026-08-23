# PQ-4 Baseline Plus Delta Evidence

Author: Raphael Rechberger

## Scope

- Change ID: M08-PQ4
- Changed closure: Step 4A and Step 4B schemas, validators, renderers, local gate separation, immutable artifact preflight, Console artifact/review surfaces, and generated API contracts.
- Observable outcome: professional typed Copywriter and Developer packages are locally validated, deterministically rendered, revision-bound, and reviewable before approval.
- Excluded baseline: unrelated workflow steps, Delivery, solver, provider, archive, mobile browser matrix, and full repository discovery were not repeated.

## Focused Evidence

- Step 4A contract and renderer closure: 17 tests passed.
- Step 4B contract, renderer, JSON-LD, and localization closure: 37 tests passed, plus the final 5-test localization cell.
- Local immutable Step 4 API closure: 20 tests passed.
- Generated contract closure: 14 tests passed and `generate_operator_api_contracts.py --check` passed.
- Final Console closure: 51 tests passed across `client.test.ts`, `useOperatorWorkspace.test.tsx`, and `ReviewWorkspace.test.tsx`.
- Production Console build: `npm run build` passed.
- Desktop PT-04/PT-10 delta cell: `pq4-console-browser-results.json` passed with no console errors, failed requests, HTTP errors, or horizontal overflow.
- Fresh visual evidence: `pq4-console-review-desktop.png`, `pq4-console-review-payload.png`, and `pq4-console-review-confirmation.png` passed focused visual inspection.

## Honest Boundary

Local fixtures prove contract shape, deterministic rendering, hashes, provenance handling, and review behavior. They do not prove Google Rich Results, Screaming Frog, Lighthouse, axe, visual comparison, staging, production, provider, or customer execution. PQ0-4A-003 and PQ0-4B-004 therefore remain `deferred_external`.
