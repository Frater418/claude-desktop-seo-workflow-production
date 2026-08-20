# Sprint 5 Package 2 Artifact and Run Workspace

Date: 2026-08-20
Author: Raphael Rechberger
Status: complete and controller verified

## Scope Boundary

This package implements master-plan Tasks 5.6 and 5.7 only. It adds a demo-only Artifact Preview, immutable Revision Diff, LLM Run History, Context Package Summary, and disabled Revision Run Preview to the existing Operator Console.

The Package 1 dashboard, timeline, selected-step detail, exact `?mode=demo` activation, and real API unavailable and available behavior are preserved. The workspace switch is rendered only after exact demo activation. No router, API projection, mutation, command dispatch, backend contract, generated type, Package 3 feature, or customer-specific constant was added.

## Changed Files

- `apps/operator-console/src/App.tsx`
- `apps/operator-console/src/App.test.tsx`
- `apps/operator-console/src/styles.css`
- `apps/operator-console/src/features/artifacts/ArtifactPreview.tsx`
- `apps/operator-console/src/features/artifacts/RevisionDiff.tsx`
- `apps/operator-console/src/features/runs/RunHistory.tsx`
- `apps/operator-console/src/features/runs/ContextPackageSummary.tsx`
- `apps/operator-console/src/features/runs/RevisionRunPreview.tsx`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-5/02_ARTIFACT_AND_RUN_WORKSPACE.md`

## Implementation Notes

- Demo mode has controlled `Workflow` and `Artifacts & runs` tabs with tab and tabpanel semantics. Workflow retains its default selected step `1b` when revisited.
- Artifact records show human-readable identity and location data by default. Hashes, storage IDs, package ID, package hash, technical session decision, and comparison hashes remain under closed `Technical details` disclosures.
- Revision comparisons show Added, Changed, Removed, Unchanged, and operator impact. Rejected candidates are retained and a new revision is described as a new artifact identity, not an in-place overwrite.
- Run history presents one `local_core` logical session plus released, rejected, and pending recovery technical LLM runs. Technical sessions are explicitly replaceable cache, not source of truth.
- The lost cache state presents `recover fresh` and the aligned technical `recover_fresh` decision. The immutable context package remains valid and supports deterministic rebuild.
- Revision dispatch is a disabled Review Center handoff. It documents immutable fields, forbidden changes, fresh execution, forbidden technical-session reuse, expected output contracts, and a new artifact identity preview. It issues no command.

## Focused Tests Added

`apps/operator-console/src/App.test.tsx` adds behavioral tests for:

- switching between the demo workspaces while preserving the Workflow route
- selecting an artifact and updating its revision diff
- keeping artifact technical details closed by default
- showing `recover fresh` for a lost technical session while the immutable package remains valid
- showing revision immutable and forbidden fields with the Review Center dispatch control disabled

## Controller Validation Required

The controller owns validation. The following commands and browser QA were not run by this implementation worker:

```text
cd apps/operator-console && npm test
cd apps/operator-console && npm run build
python scripts/generate_operator_api_contracts.py --check
```

Browser QA is also required for `?mode=demo` at desktop, tablet, and mobile widths. Verify keyboard tab operation, artifact selection, closed technical disclosures, the disabled Review Center control, long-content wrapping, and zero horizontal overflow.

## Controller Validation

The stable Package 2 workspace was verified after Sisyphus completed its report:

```text
cd apps/operator-console && npm test
Exit 0. 1 test file passed, 16 tests passed.

cd apps/operator-console && npm run build
Exit 0. TypeScript passed. Vite 8.2.2 built 25 modules.

cd apps/operator-console && npm audit --audit-level=moderate
Exit 0. 0 vulnerabilities.

python scripts/generate_operator_api_contracts.py --check
Exit 0.
```

One worker test expected the sentence `Immutable context package remains valid` without its rendered period. The controller corrected only that exact matcher. Product behavior did not change.

Local Chrome CDP opened the actual Vite demo and selected `Artifacts & runs` at desktop 1440 by 1100 and mobile 390 by 844. Both passed visual inspection. CDP assertions confirmed:

- active tab: `Artifacts & runs`
- desktop document scrollWidth within viewport
- mobile document scrollWidth exactly 390
- all workspace and artifact panels within viewport bounds
- zero open Technical Details disclosures by default
- disabled Review Center dispatch
- visible `recover fresh`, Immutable Fields, and Forbidden Changes

Desktop and mobile screenshots show a professional operator hierarchy without clipping or overlap.

## Static Review

Every Package 2 source and test file was re-read before the worker report was written. TypeScript and CSS LSP diagnostics could not run because their language servers are not installed and installation was previously declined. No LSP installation was attempted. Controller tests, build, audit, codegen and browser QA are the final executable evidence.
