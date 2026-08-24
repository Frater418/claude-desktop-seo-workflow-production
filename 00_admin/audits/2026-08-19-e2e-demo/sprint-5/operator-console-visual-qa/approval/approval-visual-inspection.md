# Approval Visual Inspection

Inspection timestamp: 2026-08-21T15:18:23Z to 2026-08-21T15:18:30Z

Every listed capture was opened with `look_at` after the final browser run. Bottom-edge continuation is normal document scrolling, not internal component clipping.

| Capture | Result | Inspection |
| --- | --- | --- |
| approval-projekte-1280x900.png | PASS | No overlap, horizontal overflow, malformed German wrapping, or compositing defect. |
| approval-workflow-1280x900.png | PASS | No overlap, horizontal overflow, malformed German wrapping, or compositing defect. |
| approval-aufgaben-1280x900.png | FAIL | Task-row date wraps as `2026-` plus the remaining date. |
| approval-artefakte-1280x900.png | PASS | No overlap, horizontal overflow, malformed German wrapping, or compositing defect. |
| approval-pruefungen-und-freigaben-1280x900.png | FAIL | Verification text and timestamp wrap awkwardly in the narrow card. |
| approval-uebergabe-und-export-1280x900.png | PASS | No overlap, horizontal overflow, malformed German wrapping, or compositing defect. |
| approval-projekte-768x1024.png | FAIL | `Informationsarchitektur` splits as `Informationsarc` and `hitektur`. |
| approval-workflow-768x1024.png | PASS | No overlap, horizontal overflow, malformed German wrapping, or compositing defect. |
| approval-aufgaben-768x1024.png | FAIL | `Informationsarchitektur` splits as `Informationsarchi` and `tektur`. |
| approval-artefakte-768x1024.png | FAIL | `Informationsarchitektur` splits as `Informationsarchi` and `tektur`. |
| approval-pruefungen-und-freigaben-768x1024.png | FAIL | `Informationsarchitektur`, timestamp, and checker version have malformed wrapping. |
| approval-uebergabe-und-export-768x1024.png | FAIL | `Informationsarchitektur` splits as `Informationsarchi` and `tektur`. |
| approval-projekte-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-workflow-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-aufgaben-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-artefakte-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-pruefungen-und-freigaben-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-uebergabe-und-export-390x844.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-projekte-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-workflow-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-aufgaben-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-artefakte-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-pruefungen-und-freigaben-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |
| approval-uebergabe-und-export-375x812.png | PASS | No overlap, overflow, malformed wrapping, clipping, or compositing defect. |

Result: 16 of 24 visual cells pass. The eight failed cells are release blockers because this approval gate requires clean German wrapping at every required viewport.
