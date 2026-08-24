# Browser Launch Failure

## Required Playwright MCP

Command surface attempted: `playwright.browser_tabs` followed by `playwright.browser_navigate` for `http://127.0.0.1:43179/`.

Result for both attempts:

```text
Error: async initializeServer: Chromium distribution 'chrome' is not found at /opt/google/chrome/chrome
Run "npx playwright install chrome"
```

## Required Fallback Search

- `skill agent-browser`: unavailable.
- `skill_mcp` server `agent-browser`: unavailable.
- `/usr/local/bin/agent-browser`: absent.
- `/usr/local/bin/dev-browser`: absent.

No fallback was available and no browser or package installation was performed.
