# Windows Reparse Test Fix

## Scope

Changed only these test files:

- `tests/test_crawl_waiver_resolution.py`
- `tests/test_screaming_frog_quality_gate.py`

The implementation duplicates a small deterministic fixture helper in each authorized file. On POSIX it creates a real directory symlink with `Path.symlink_to(..., target_is_directory=True)`. On Windows it creates a real directory junction through:

```text
subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, shell=False)
```

`check=True` makes junction creation failures loud. `shell=False` and the argument vector avoid shell interpolation. `mklink /J` is a junction mechanism that does not require Developer Mode or administrative rights.

Each test explicitly removes only its created link after the rejection check. POSIX removes the symlink with `unlink()`. Windows removes the junction with `rmdir()`. The waiver test proves the external evidence file still exists after cleanup. The Screaming Frog test proves the external directory and its sentinel file still exist after cleanup.

## Red Evidence

Independent Windows verification of the prior direct `Path.symlink_to` setup failed with `WinError 1314`, before either real containment assertion could run.

For local TDD, the two existing real escape tests were first changed to call the new portable fixture seam before that seam was implemented. This command was run:

```text
python -m unittest tests.test_crawl_waiver_resolution.CrawlWaiverResolutionTests.test_cli_rejects_input_symlink_escape_before_output_creation tests.test_screaming_frog_quality_gate.ScreamingFrogQualityGateTests.test_intermediate_symlink_escape_is_rejected_before_mkdir_preflight_or_subprocess
```

It failed as expected with two `NameError` exceptions for the missing `create_directory_link` fixture. This established the red state for the adapted tests. The prior direct symlink implementation remains known-red on Windows because it raises `WinError 1314`.

## Green Evidence

After implementing the POSIX symlink and Windows junction branches, the same focused command passed:

```text
Ran 2 tests in 0.004s
OK
```

The complete two-module suite passed:

```text
python -m unittest tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate
Ran 18 tests in 0.186s
OK
```

The required full suite passed:

```text
python tests/run_full_suite.py
Acceptance tests: 7/7 passed
Unittest discovery: 101 tests passed in 2.678s
```

## Preserved Rejection Behavior

- The waiver-resolution escape test still rejects with `ERROR_CRAWL_WAIVER_EVIDENCE_INVALID` before the `tenants` output path exists.
- The Screaming Frog escape test still rejects with `ERROR_SCREAMING_FROG_OUTPUT_PATH_INVALID` before `mkdir`, `preflight`, and the crawler subprocess are called.
- No `Path.resolve` behavior is mocked and both tests use a genuine filesystem escape object.

## Limitation

The verification host is Linux and exercised the real POSIX directory-symlink branch. Linux cannot execute the Windows `mklink /J` junction branch. Windows host verification is still required to execute that branch and confirm the platform-native reparse point end to end.
