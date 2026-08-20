# Stage B Windows Recovery Test Portability Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Test portability only

## Finding

The Stage B recovery product path passed on OMO, but two Windows tests attempted to create directory symlinks directly. Windows returned WinError 1314 because the current process did not hold symlink privileges.

## Correction

The two tests now inject the same post-append repository finalization failure by mocking `ProjectRepository.finalize_operator_recovery` to raise a safe `RepositoryError`.

This exercises the complete product behavior on both runtimes:

- one event is durably appended
- one recovery sidecar remains
- HTTP returns 503
- readiness returns 503
- an identical replay does not append another event
- replay finalizes the canonical record after recovery
- the sidecar is removed
- readiness returns 200
- a conflicting replay cannot consume the sidecar

Linux symlink/reparse containment remains exercised by OMO and the existing containment test family. No production code or contract changed.

## Verification

```text
Targeted recovery tests on Windows: 2 passed
Targeted recovery tests on OMO: 2 passed
Windows Full Suite: acceptance 7, root 216, contracts 59, total 282 passed
OMO Full Suite: acceptance 7, root 216, contracts 59, total 282 passed
git diff --check: exit 0
```
