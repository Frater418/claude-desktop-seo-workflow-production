# Browser Resume Failure

## Resolved Historical Failure

The missing Chrome error recorded in `browser-launch-failure.md` is superseded. Chrome Stable is now available at `/opt/google/chrome/chrome`.

## Current Playwright MCP Attempt

Command surface attempted: `playwright.browser_tabs` with `action: "list"`.

Result:

```text
Error: async initializeServer: EACCES: permission denied, mkdir '/home/coder/.cache/ms-playwright/b'
```

The MCP initialization fails before it can create a page or use the Chrome channel. No cache permission, browser, package, source, test, or product configuration was changed.
