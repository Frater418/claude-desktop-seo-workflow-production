# Approval Reproduction Record

Build command:

```bash
VITE_OPERATOR_TENANT_ID=tenant-visual-qa VITE_OPERATOR_API_BASE_URL= npm run build
```

Browser command:

```bash
HOME=/tmp/opencode/operator-approval-home XDG_CACHE_HOME=/tmp/opencode/operator-approval-cache npm_config_cache=/tmp/opencode/operator-approval-npm-cache npx --yes playwright@1.62.1 test /tmp/opencode/operator-approval.spec.cjs --workers=1 --reporter=line
```

Browser: Chrome channel with executable `/opt/google/chrome/chrome`.

Fixture: strict same-origin temporary API at `http://127.0.0.1:43180`, tenant `tenant-visual-qa`, projects `project-alpha`, `project-beta`, and intake-created `project-intake`. It rejects unknown API paths with HTTP 404 and contains no demo fallback.

Evidence inventory:

- `approval-browser-results.json`: 24 PNG capture records, viewport overflow assertions, all interaction outcomes, network log, console classification, and authoritative request bodies.
- `approval-*.png`: the complete 6 destination by 4 viewport capture matrix.
- `approval-state-primary-hover.png`, `approval-state-primary-focus.png`, and `approval-state-primary-active.png`: representative interaction state frames.
- `approval-visual-inspection.md`: per-capture visual review.
- `approval-findings.md`: release-blocking reproducible defects.

No product file, test file, configuration file, package file, dependency, commit, or deployment was changed during this approval execution.
