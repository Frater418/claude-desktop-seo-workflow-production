# Sprint 1 Rereview Fix Report

Author: Raphael Rechberger
Audit date: 2026-08-19

## Actual Changed Files

- `services/operator_routing/router.py`
- `standards/operator/error-routing-policy.json`
- `tests/test_operator_error_routing.py`
- `services/quality_gate_runner/waiver_resolution.py`
- `tests/test_crawl_waiver_resolution.py`
- `tests/test_screaming_frog_quality_gate.py`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-1/07_REREVIEW_FIX.md`

## Red-Green Evidence

- Red: `python -m unittest tests.test_operator_error_routing tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate -v` exited 1. The real ledger contention code was rejected as `ERROR_OPERATOR_ROUTING_UNKNOWN_CODE`, and waiver CLI tests failed because the controlled root and identity arguments were absent.
- Green: `python -m unittest tests.test_operator_error_routing tests.test_transition_service tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate -v` exited 0. All 38 tests passed, including real transition CLI ledger contention routing, controlled run-scoped waiver output, input collision, traversal, absolute path, symlink escape, pre-existing output, and intermediate Screaming Frog symlink escape rejection before mkdir, preflight, or subprocess.

## Commands And Outcomes

- `python -m unittest tests.test_operator_error_routing tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate -v`: exit 1, 25 tests run, 10 expected red errors for the missing routing and controlled CLI behavior.
- `python -m unittest tests.test_operator_error_routing tests.test_transition_service tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate -v`: exit 0, 38 tests passed.
- `python tests/run_full_suite.py`: exit 0, 7 of 7 acceptance tests and 101 discovered unit tests passed.
- `python -m services.quality_gate_runner.waiver_resolution --help`: exit 0, displayed controlled root and tenant, project, run identity arguments with no caller-selected output argument.
- `lsp_diagnostics` on every changed Python file: basedpyright was unavailable because its installation had previously been declined.
