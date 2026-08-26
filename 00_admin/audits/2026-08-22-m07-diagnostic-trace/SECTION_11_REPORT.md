Change ID: M07-DIAGNOSTIC-TRACE-001

Observed failure:
The M06 browser cell started a diagnostic trace but did not configure the automated M06 scenario, append normalized browser evidence, or close and reconstruct the trace.

Changed files and symbols:
tests/test_delivery_e2e.py
apps/operator-console/src/test/deliveryE2EBrowser.mjs
tests/support/diagnostic_trace_e2e.py

Affected route, flow and gate:
Uebergabe und Export
POST diagnostic-traces
POST diagnostic-traces/{trace_id}/entries
POST diagnostic-traces/{trace_id}/close
PT-09 and the existing 1280x900 M06 Delivery Center cell

Focused red test:
python -m unittest tests.test_delivery_e2e.DeliveryE2ETests.test_neutral_delivery_route_from_checkpoint_to_final

Direct closure tests selected:
One isolated red execution with M07_DIAGNOSTIC_ROOT
One approved-root green execution of the exact M06 E2E cell

Why each test is in scope:
The browser driver proves the real Console creates, records, observes, and closes the automated Delivery trace.
The Python reconstruction proves immutable JSONL, current pointer, index, closed-only semantics, and close replay without mutation.

Unrelated tests deliberately retained from baseline:
All other browser cells, M05 viewport matrix, full suite, live integrations, deployment, and unrelated routes.

Result:
Focused M07 trace trace-4859cf1f6a9548deaf0a59af0a9174e9 closed at 2026-08-22T10:15:30Z. Immutable run SHA-256 ca2a54365b5771947e11916ed83c1763cde29d865f8db219feafe833d2e144bc. Checkpoint ZIP SHA-256 81ddd22a1486153d348bc4a42300953f6fc9ae29e9bdf0425c55863679fd6897. Final ZIP SHA-256 b41544273f480de57e57457153d006ccd6e56ef06d8637197ad007651afdf2e5.

Remaining blocker:
None.

Next product task:
None.

Evidence classification:
Previous baseline evidence: M06 frozen Delivery audit
New focused evidence: M07 closed automated diagnostic trace for the existing M06 cell
Not assessed: other browser cells, live integrations, deployment, and other routes
