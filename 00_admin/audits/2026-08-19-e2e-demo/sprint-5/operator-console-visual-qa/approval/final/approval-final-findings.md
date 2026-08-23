# Final Current-Build Approval Findings

Verdict: BLOCKED

## PRODUCT-003 remains blocking

The final artifact interaction loaded the canonical source, called Playwright `fill()` with exactly:

```text
# Themenstruktur

Neue kanonische Revision
```

The controlled textarea still read back as:

```text
# Themenstruktur

Kanonischer Ausgangstext
```

The strict fixture rejected the save with HTTP 422 because `primary_document` was not the exact replacement. The exact rendered and submitted values are recorded in `approval-final-browser-results.json` under `artifactTextarea` and `artifactRequest`.

This prevents save, readback, comparison, and validation of the edited artifact. It is a release blocker.

## PRODUCT-004 is incomplete

The prior 768px malformed wrapping is fixed. All five required `Informationsarchitektur` tablet routes pass, and all date, ISO timestamp, `Vollstaendigkeitsnachweis`, and `step-validation-service-1.0.0` tablet and review tokens are intact.

However, `approval-final-aufgaben-1280x900.png` visibly clips task-list dates at the right edge as `2026-08-`. The mandatory readable-date condition is therefore not met at every required viewport.

## Non-product browser observations

Chrome emitted automatic console entries for the deliberately controlled stale 409 and the expected strict-fixture 422 artifact rejection. `consoleClassification.unexpected` is empty. `/favicon.svg` returned 200 and no `/favicon.ico` request occurred.
