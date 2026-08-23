# Final Approval Findings

Verdict: BLOCKED

## PRODUCT-003: Artifact save body ignores the edited textarea value

Reproduction:

1. Open Artefakte for Pflegedienst Alpha at 1280x900.
2. Load `outputs/themenstruktur.md, Revision 17`.
3. Replace the textarea with `# Themenstruktur` followed by `Neue kanonische Revision`.
4. Save as a new revision.
5. Inspect the recorded `POST /v1/tenants/tenant-visual-qa/projects/project-alpha/artifacts` request in `approval-browser-results.json`.

Expected: `primary_document` is the edited textarea value.

Actual: the rendered textarea showed the edited value, while `primary_document` was the loaded source content concatenated directly with the edited value: `# Themenstruktur` followed by `Kanonischer Ausgangstext# Themenstruktur` followed by `Neue kanonische Revision`.

Impact: the UI reports a canonical revision save and readback without proving that the operator edit is the submitted revision. This blocks approval.

## PRODUCT-004: German wrapping fails at 768px and in narrow desktop cards

The final inspection found mid-word splitting of `Informationsarchitektur` in five 768px route captures. The desktop task and review cards also split dates, timestamps, and long German evidence text in ways that do not meet the German-wrapping requirement.

Evidence: `approval-visual-inspection.md` and the named fresh PNGs.

Impact: no horizontal overflow occurs, but the required readable German wrapping is not satisfied at all mandatory viewports. This blocks approval.

## Non-product Chrome Observation

Chrome emitted one automatic console event for the deliberately controlled `409 Conflict` stale-approval response. It is captured in `approval-browser-results.json` as `expectedControlledStale409`; there were zero unexpected console errors and zero unexpected failed requests. The application rendered the specified stale-preview recovery message correctly.
