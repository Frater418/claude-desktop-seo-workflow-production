Change ID: M06-DELIVERY-E2E-001

Observed failure:
The previous M05 browser harness used synthetic same-origin Delivery responses and a non-ZIP body, so it did not prove the production UI, real local Task 6 API, persisted workspace, ZIP integrity, or exact replay together.

Changed files and symbols:
tests/test_delivery_e2e.py
apps/operator-console/src/test/deliveryE2EBrowser.mjs
No production symbols changed.

Affected route, flow and gate:
Uebergabe und Export
GET delivery/preview
POST delivery/exports
GET delivery/exports
GET delivery/exports/{export_id}
GET delivery/exports/{export_id}/download
PT-05, PT-06, PT-07, focused Delivery Center portion of PT-10

Focused red test:
python -m unittest tests.test_delivery_e2e.DeliveryE2ETests.test_neutral_delivery_route_from_checkpoint_to_final

Direct closure tests selected:
Production frontend build
One neutral M06 E2E test
One 1280x900 real-browser Delivery Center driver

Why each test is in scope:
The build creates the production bundle used by the browser.
The Python E2E proves API, persistence, policy, ZIP, checksums, replay and boundaries.
The browser driver proves the actual Delivery Center route uses that real API and workspace.

Unrelated tests deliberately retained from baseline:
All M04 Delivery tests
M05 component tests
M05 synthetic three-viewport browser harness
Workflow, provider, prompt, solver, AHD and integration tests
Full repository suite and broad review

Result:
Production build exit status 0. Focused unittest exit status 0. Checkpoint ZIP SHA-256 81ddd22a1486153d348bc4a42300953f6fc9ae29e9bdf0425c55863679fd6897. Final ZIP SHA-256 b41544273f480de57e57457153d006ccd6e56ef06d8637197ad007651afdf2e5. Export IDs delivery-export-aa3335ee5ab249b02303c7abb8074b34 and delivery-export-00000002. Replay states checkpoint and final replayed. Cleanup passed.

Remaining blocker:
None.

Next product task:
M07 diagnostic trace

Evidence classification:
Previous baseline evidence: M04 backend and M05 browser/component evidence
New focused evidence: M06 neutral real UI/API/persistence route
Not assessed: live integrations, providers, customer AHD output, Task 7 diagnostics, deployment, other routes and viewports
