# M09 Route-Based Production Release Audit - Section 11 Report

**Autor:** Raphael Rechberger
**Datum:** 2026-08-24
**Status:** PASS at material gate
**Evidence-Level:** focused component, local fixture integration, deterministic package, local API persistence, and synthetic Chrome evidence
**Nicht bewiesen:** PT-11 customer output, M10 real customer route, live Notion, live n8n, deployment, mobile polish, or a complete repository suite

## 1. Change ID and Objective

Change ID: M09-ROUTE-MATRIX-001

Objective: Execute PT-01 through PT-10 against the release candidate under `standards/testing/PROTOTYPE_TEST_POLICY.md`, preserve unrelated green baselines, repair only proven P0/P1 route blockers, and stop before M10 for Hermes controller verification.

## 2. Previous Baseline Evidence

- M06 retained Delivery API, persistence, ZIP, replay, and browser evidence: `00_admin/audits/2026-08-22-m06-delivery-e2e/SECTION_11_REPORT.md`.
- M07 retained diagnostic trace evidence: `00_admin/audits/2026-08-22-m07-diagnostic-trace/SECTION_11_REPORT.md`.
- M08L retained live-provider Step-0 smoke and local runtime integration: `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.
- M08L remains separate live-provider evidence. PT-03 below is local fixture integration and is not described as a real customer or live-provider route.

## 3. M09 Delta Before Matrix Execution

Changed files and symbols:

- `tests/test_intake_provisioning.py`: added one public-route invalid-intake regression proving failure before provisioning writes.
- `apps/operator-console/src/test/m09ReleaseCriticalBrowser.mjs`: added the strict 1280x900 current-source synthetic Chrome harness.
- `tests/support/neutral_step3.py`: replaced stale duplicated Step-3 fixture machine fields with `derive_step3_plan_fields` from the exact released Step-2 predecessor bytes.

No production API, React, CSS, generated client, provider, persistence, or deployment source changed.

## 4. Route Matrix Result

| Cell | Evidence | Result | Evidence level |
|---|---|---|---|
| PT-01 | Two focused `App.test.tsx` cases loaded the canonical tenant/project, rejected demo fallback, switched projects, and read back the selected workspace | PASS | component integration |
| PT-02 | Valid intake/provisioning assertions in the neutral lifecycle plus the new invalid-intake public-route regression with an absent provisioning root | PASS | local API fixture integration |
| PT-03 | Exact neutral route `0 -> 1 -> 1B -> 1C -> 2 -> 3 -> 4A -> 4B`, including artifacts, predecessor bindings, revisions, gates, releases, and visible status | PASS after focused retry | local fixture integration |
| PT-04 | Artifact persistence/readback, stale-parent conflict, all canonical review actions, and stale preview protection | PASS | local service and API integration |
| PT-05 | Checkpoint/final preview policy, no preview writes, exact create identity, and Delivery-only namespace mutation | PASS | local API integration |
| PT-06 | Sorted history, canonical package record, exact ZIP download and headers, immutable replay, checksums, and safe extraction | PASS | local persistence and archive integration |
| PT-07 | Schema-valid deterministic manual Notion pack, ownership boundaries, one-way structured files, assignments, priorities, and deadlines | PASS | deterministic package integration |
| PT-08 | Interrupted Delivery recovery plus unsafe recovery rejection without writes | PASS | local recovery integration |
| PT-09 | Ordered operations, exact replay, immutable close, route isolation, last success, first failure, IDs, timestamps, error data, and evidence references | PASS | local diagnostic persistence and API integration |
| PT-10 | Current production bundle in real Chrome at 1280x900: project selection, workflow transition, canonical artifact load, revision request, Delivery preview/create/history/ZIP download, synthetic diagnostics, same-origin responses, and clean browser instrumentation | PASS after exact-cell retries | synthetic browser integration |

Open P0 findings: none.

Open P1 findings: none.

## 5. Commands and Counts

PT-01:

```text
node ./node_modules/vitest/vitest.mjs run --pool=threads src/App.test.tsx -t "loads the canonical project into the German work shell without demo fallback|lists canonical projects, keeps the selected project marked, and reloads its canonical workspace"
1 file passed, 2 tests passed, 7 skipped
```

PT-02 negative path:

```text
python -m unittest tests.test_intake_provisioning
Ran 1 test
OK
```

PT-02 positive path and PT-03 sequential route:

```text
python -m unittest tests.test_sprint5_package4.Sprint5Package4Tests.test_neutral_markdown_intake_runs_through_released_step_zero_with_canonical_readbacks
Ran 1 test
OK after the PT-03 focused correction
```

PT-04:

```text
python -m unittest tests.test_artifact_revisions.ArtifactRevisionServiceTests.test_persists_first_multi_output_revision_with_exact_bytes_and_readbacks tests.test_artifact_revisions.ArtifactRevisionServiceTests.test_replay_is_stable_but_changed_payload_and_stale_parent_conflict tests.test_action_facade.ActionFacadeTests.test_operator_actions_confirm_through_canonical_record_readback tests.test_action_facade.ActionFacadeTests.test_confirm_rejects_preview_after_canonical_gate_or_run_change
Ran 4 tests
OK
```

PT-05:

```text
python -m unittest tests.test_delivery_api_preview.DeliveryApiPreviewTests.test_preview_checkpoint_reports_eligibility_missing_and_selected_deliverables_without_writes tests.test_delivery_api_preview.DeliveryApiPreviewTests.test_preview_final_reports_policy_failure_without_creating_delivery_files tests.test_delivery_api_create.DeliveryApiCreateTests.test_create_returns_created_export_with_exact_caller_identity_and_no_clock_access tests.test_delivery_api_create.DeliveryApiCreateTests.test_create_changes_only_the_delivery_namespace
Ran 4 tests
OK
```

PT-06:

```text
python -m unittest tests.test_delivery_api_reads.DeliveryApiReadsTests.test_history_is_empty_then_sorted_by_created_at_and_export_id tests.test_delivery_api_reads.DeliveryApiReadsTests.test_package_record_and_download_expose_exact_persisted_archive_with_controlled_headers tests.test_delivery_api_create.DeliveryApiCreateTests.test_identical_create_replay_returns_the_immutable_export_with_replayed_state tests.test_delivery_archive.DeliveryArchiveTests.test_manifest_checksums_metadata_and_safe_extraction_validate_every_byte
Ran 4 tests
OK
```

PT-07:

```text
python -m unittest tests.test_notion_import_pack.NotionImportPackTests.test_builds_schema_valid_deterministic_manual_pack tests.test_notion_import_pack.NotionImportPackTests.test_enforces_core_history_and_notion_ownership_boundaries tests.test_notion_import_pack.NotionImportPackTests.test_generated_structured_files_are_one_way_and_lf_only
Ran 3 tests
OK
```

PT-08:

```text
python -m unittest tests.test_delivery_api_recovery.DeliveryApiRecoveryTests.test_interrupted_delivery_is_unready_conflict_cannot_consume_recovery_and_matching_replay_repairs tests.test_delivery_api_recovery_inventory_safety.DeliveryApiRecoveryInventorySafetyTests.test_unsafe_recovery_inventory_blocks_readiness_and_create_without_writes
Ran 2 tests
OK
```

PT-09:

```text
python -m unittest tests.test_diagnostic_trace_store.DiagnosticTraceStoreTests.test_create_current_ordered_append_exact_replay_and_immutable_close tests.test_diagnostic_trace_api.DiagnosticTraceApiTests.test_append_replays_exact_operation_rejects_reuse_and_preserves_route_isolation tests.test_diagnostic_trace_api.DiagnosticTraceApiTests.test_close_replays_exact_close_identity_and_blocks_later_append
Ran 3 tests
OK
```

PT-10 build and final browser command:

```text
VITE_OPERATOR_TENANT_ID=tenant-browser-qa npm run build
TypeScript no-emit check: PASS
Vite production build: PASS, 50 modules transformed

PLAYWRIGHT_REQUIRE_FROM=/home/coder/.npm/_npx/db89d7302a373f10/node_modules/playwright/package.json node apps/operator-console/src/test/m09ReleaseCriticalBrowser.mjs --dist apps/operator-console/dist --chrome /opt/google/chrome/chrome --output 00_admin/audits/2026-08-24-m09-route-matrix/browser
Exit status: 0
```

PT-10 final evidence:

- Chrome: `/opt/google/chrome/chrome`.
- Viewport: 1280x900 only.
- Screenshot: `browser/m09-release-critical-desktop-1280x900.png`, 126261 bytes.
- Structured evidence: `browser/m09-release-critical-browser-results.json`.
- Console errors: 0.
- Failed requests: 0.
- HTTP responses with status 400 or greater: 0.
- External or cross-origin browser responses: 0.
- Delivery exports created: 1.
- ZIP downloads served: 1.

## 6. Focused Retry Record

### PT-03

Observed failure:

- `KeyError: 'rows'` at the Step-2 to Step-3 fixture boundary.
- After the obsolete key was exposed, Step-3 validation correctly rejected stale static machine-plan collections.

Root cause:

The neutral Step-3 fixture duplicated an obsolete solver projection and static plan. The current deterministic bridge returns `{"items": [...]}` and derives all plan collections from the exact Step-2 predecessor.

Minimal fix:

- `tests/support/neutral_step3.py` now calls `derive_step3_plan_fields(json.loads(predecessor_content))` and installs the complete canonical machine fields.

Retry scope:

- PT-03 only. PT-01 was not restarted.
- PT-04 and PT-05 were still pending and ran later in normal matrix order.

### PT-10

Observed harness failures and bounded corrections:

- The first production build omitted `VITE_OPERATOR_TENANT_ID`; the app correctly stopped at its configuration gate. The bundle was rebuilt with the synthetic tenant.
- The old artifact scenario attempted a save on a non-Step-4 artifact. PT-10 now performs the valid canonical load/readback action. PT-04 separately proves save and stale-revision behavior.
- The artifact assertion raced the asynchronous content readback. The harness now waits for the exact editor value.
- The current app creates diagnostic traces during browser actions. Strict synthetic create, append, and close routes were added.
- Approval is intentionally unavailable for the Step-1B synthetic artifact because current approval requires an exact Step-4 primary/supporting pair. PT-10 uses revision request plus canonical readback. PT-04 separately proves approval and stale approval protection.
- The Delivery preview fixture had one camelCase-to-snake_case identifier typo and one obsolete status phrase. Both were corrected at the harness boundary.

Retry scope:

- PT-10 only at 1280x900.
- No backend, provider, solver, prompt, mobile, or unrelated browser cell was rerun.

## 7. Baseline Plus Delta Classification

Previous baseline evidence:

- M01 through M08L evidence remains retained where the release candidate did not change its covered dependency closure.
- M08L remains the only current live-provider Step-0 evidence.

New focused M09 evidence:

- PT-01 through PT-10 route cells listed above.
- PT-02 invalid-intake no-write regression.
- PT-03 deterministic Step-3 fixture correction.
- PT-10 current-source desktop Chrome evidence.

Not assessed:

- PT-11 controlled real customer output.
- Real AHD customer inputs or professional customer package review.
- Live Notion or n8n writes.
- Deployment, CMS adapters, mobile polish, broad archetypes, and documentation expansion.
- Complete repository discovery or `python tests/run_full_suite.py`.

## 8. Deliberately Retained and Excluded Tests

The following were deliberately not repeated:

- Full repository suite and all-test discovery.
- Complete historical M05 visual viewport matrix.
- Historical M06 and M07 E2E reruns that would rewrite retained evidence packets.
- M08L live-provider run.
- Unrelated prompt, provider, solver, security, deployment, and customer-output suites.
- Broad multi-agent review.

This report does not describe the focused M09 pass as a complete Full-System test.

## 9. Material Gate and Remaining Blocker

Result: PT-01 through PT-10 are green with no open P0/P1 finding in the assessed release-candidate routes.

Remaining blocker: M09 is stopped at the material gate for Hermes controller verification. M10 must not begin until the controller accepts this packet and the selected pilot, exact Project V2 inputs, required provider access, and known AHD source/resource blocker are explicitly resolved or routed.

Next product task after acceptance: M10 first controlled local production output.
