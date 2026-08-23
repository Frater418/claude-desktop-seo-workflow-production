# Last Attempt Cleanup

- Targeted temporary Chrome profiles matching `/tmp/opencode/final-home` and `/tmp/opencode/operator-console-browser-home` received TERM, then bounded KILL if still present.
- `GET http://127.0.0.1:43179/readyz` returned a transport error after cleanup.
- The environment lacks `ss`, so an OS socket-listing receipt could not be produced. The live readiness probe confirms the QA API port is closed.
- Process listing before cleanup is in `preflight-processes.txt`.
