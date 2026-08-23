# Redacted Operator Console QA Harness

The harness uses synthetic tenant, project, artifact, task, and intake values only. It must bind localhost only, serve the current production build, reject unknown paths, and retain only these source files after cleanup.

The run used Chrome at `/opt/google/chrome/chrome`, a temporary `/tmp/opencode` HOME, XDG cache, npm cache, and browser profile, plus an ephemeral `npx --yes --package=playwright@1.62.1` package cache. The driver records strict request and interaction evidence in `footer-pass-browser-results.json`.
