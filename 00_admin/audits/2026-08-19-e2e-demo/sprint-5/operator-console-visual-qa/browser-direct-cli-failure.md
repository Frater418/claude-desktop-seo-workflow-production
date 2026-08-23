# Direct Playwright Fallback Failure

## Superseded MCP Failures

- `browser-launch-failure.md`: superseded because Chrome Stable is now available at `/opt/google/chrome/chrome`.
- `browser-resume-failure.md`: superseded for this run because the requested direct Node path uses an isolated `/tmp/opencode/operator-console-browser-home` instead of the MCP cache path.

## Current Blocker

The requested direct Playwright Node or CLI fallback is not installed locally.

```text
apps/operator-console/node_modules/playwright: absent
npx --no-install playwright --version: missing packages: ["playwright@1.62.1"]
npx --no-install @playwright/test --version: missing packages: ["@playwright/test@1.62.1"]
```

Using `npx playwright` without `--no-install` would download and install the missing package, which the request explicitly prohibits. No package, browser, fixture, preview process, or product file was created in this attempt.
