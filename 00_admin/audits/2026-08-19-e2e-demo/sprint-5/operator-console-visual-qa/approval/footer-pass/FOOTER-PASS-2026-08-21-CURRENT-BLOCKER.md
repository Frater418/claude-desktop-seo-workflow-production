# Footer Pass Current-Source Blocker

Verdict: BLOCKED

The current production build and strict same-origin synthetic fixture started successfully. The run used Chrome at `/opt/google/chrome/chrome`, isolated `/tmp/opencode` runtime state, and the preserved redacted harness source.

## Precise Blocker

At narrow width, after the lower `Projekte` capture sets `.workspace-frame.scrollTop` to its maximum, navigating to the distinct `Workflow` route does not reset it to `0` by the next `requestAnimationFrame`.

The harness records the initial requested scenario separately: intake acceptance, nonzero workspace scroll, and navigation to `Projekte` passed both immediate and settled reset checks with computed `overflow-anchor: none`. The later normal route transition from a scrolled workspace still fails. This violates the required route navigation reset contract and blocks the remaining 11 lower/full-page captures and current PASS publication.

## Completed Fresh Evidence

- Current source production build passed with explicit synthetic tenant and same-origin API base.
- Strict localhost server rejected `GET /unexpected-path` with HTTP 404.
- Canonical fixture task status `open` rendered exactly as `Offen` through `.task-detail dd`.
- Workflow preview and confirmation reached canonical readback.
- Artifact content load, exact replacement save, readback, comparison, and validation passed.
- All six review decisions passed their preview, confirmation removal, re-enabled selector, and canonical readback checks.
- Intake preview and acceptance reached `Schritt 0 bereit`.
- Fresh evidence contains 24 core captures, eight state captures, and one lower capture. Every generated capture was inspected with `look_at`.

No current PASS claim is made for `approval/footer-pass/`.
