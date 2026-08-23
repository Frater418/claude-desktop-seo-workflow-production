# Direct Chrome Visual Findings

## Product Defect

PRODUCT-001: the required responsive layout fails at 768x1024, 390x844, and 375x812 for every destination. The evidence panel overlays the main workspace and the shell clips horizontally. This violates the `DESIGN.md` requirement that the panel move below work or become a disclosure at 850px, that mobile use an accessible horizontal navigation row, and that 390px support the work surface without horizontal scrolling.

Reproduce with the production build, a canonical selected project, and any destination at 768px or narrower. Compare `workflow-1280x900.png` with `workflow-768x1024.png` or `workflow-390x844.png`.

## Route Matrix

| Destination | 1280x900 | 768x1024 | 390x844 | 375x812 |
| --- | --- | --- | --- | --- |
| Projekte | PASS | FAIL | FAIL | FAIL |
| Workflow | PASS | FAIL | FAIL | FAIL |
| Aufgaben | PASS | FAIL | FAIL | FAIL |
| Artefakte | PASS | FAIL | FAIL | FAIL |
| Pruefungen und Freigaben | PASS | FAIL | FAIL | FAIL |
| Uebergabe und Export | PASS | FAIL | FAIL | FAIL |

All PNGs have a valid signature, expected viewport dimensions, nonempty compositing, and fresh timestamps. Accessibility snapshots with matching names are saved beside each PNG.

## Visual Validation

`look_at` validated all 24 route PNGs.

- All six desktop captures are fully composed, readable, and show navigation plus expected actions.
- All six tablet captures show right-side clipping and evidence-panel overlap.
- All six 390px captures show clipped navigation and the evidence panel covering or displacing the work surface.
- All six 375px captures show the same defect, with clipped action labels and inaccessible primary content.

## Browser Interaction Evidence

`browser-qa-results.json` records successful identity, project switch, workflow preview, task filters, released-artifact lock, gate evidence, delivery lock, console, and HTTP request evidence. It also records incomplete artifact-edit and context-keyboard scenarios after the fixture switched to the released project. These are not classified as product defects because the disposable fixture state was not reset before those attempted interactions.

The visual product defect is sufficient to block completion of the required mobile and tablet interaction matrix.
