# Windows JSON-LD Import Portability Fix

Date: 2026-08-19

## Finding

The OMO Python 3.12 suite passed while Windows Python 3.11 could not import Step 4A. The direct import `from mcp.tools.validate_schema_jsonld import validate_text` resolved the installed external `mcp` package on Windows instead of the repository-local `mcp/tools/validate_schema_jsonld.py` file.

This was a package namespace collision, not a Python 3.11 syntax defect.

## RED Evidence

```text
python -m unittest tests.test_step4a_import_portability -v
```

Result before the fix: 2 tests failed. Step 4A depended on the external `mcp` package shape and the portable adapter did not exist.

## Fix

- Added `services/jsonld_validation.py` as a repository-local file loader.
- The adapter loads the validator by verified project path without importing through the external `mcp` package name.
- Missing, damaged or incompatible validator artifacts raise `ERROR_JSONLD_VALIDATOR_UNAVAILABLE`.
- The error has exactly one `workflow_defect` route owned by `workflow_maintainer`.
- Step 4A converts adapter failure into a structured preflight error.
- Added a subprocess regression that injects a foreign `mcp` package and proves Step 4A still imports.

## GREEN Evidence

```text
python -m unittest tests.test_step4a_import_portability tests.test_step4a_contract tests.test_step4a_renderer tests.test_operator_error_routing -v
```

Result: 15 tests passed on Windows Python 3.11.

```text
python tests/run_full_suite.py
```

Windows result: acceptance 7, root discovery 156, contract discovery 37, total 200 tests passed at the portability-fix checkpoint.

After the mandatory-lineage fix, the final Windows and OMO suites both passed 202 tests.

## Side Effects

No network, provider, crawl, deployment, commit or push operation was performed.
