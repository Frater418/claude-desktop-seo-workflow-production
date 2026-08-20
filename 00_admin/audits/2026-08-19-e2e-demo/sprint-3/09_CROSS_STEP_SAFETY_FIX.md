# Sprint 3 Cross-Step Safety Fix

Date: 2026-08-19

## Scope

This remediation addresses the verified false-green drivers in Sprint 3 reviews 07 and 08 within the permitted Step preflight, renderer, routing, contract-test, and audit surfaces.

## RED Evidence

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_cross_step_safety -v
```

Before the remediation, the suite reported five regressions: empty Step 2 evidence, forged non-hex Step 3 hashes, omitted second Step 1C template, reused Step 3B revision and hash, and malformed URL plus script markup in Step 4B. The first RED execution also exposed two incorrect fixture paths in the new test. Those paths were corrected before evaluating the production behavior.

## Changes

- Step 2 preflight now rejects empty or non-canonical submissions and accepts the closed candidate envelope. The renderer flattens only verified nested canonical rows.
- Step 3 rejects hashes that are not lowercase hexadecimal SHA-256 values.
- Step 1C renders every valid template under a deterministic identity key while preserving the compatibility `html` projection.
- Step 3B rejects a proposed plan that reuses the source revision or content hash.
- Step 4B applies `FormatChecker` and rejects executable or embedded markup before rendering.
- `ERROR_STEP4B_MARKUP_UNSAFE` is included in the canonical routing inventory and has exactly one operator mapping.

## GREEN Evidence

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_cross_step_safety tests.test_step1c_contract tests.test_step1c_renderer tests.test_step2_contract tests.test_step2_renderer tests.test_step3_contract tests.test_step3_renderer tests.test_step3b_contract tests.test_step4b_contract tests.test_step4b_renderer tests.test_operator_error_routing -v
```

Result: 37 tests passed.

## Environment Limits

- Python 3.12 was used. Python 3.11 is not installed in this environment.
- `basedpyright` is unavailable because installation was previously declined. `lsp_diagnostics` therefore could not execute.
- No network, provider, crawl, or deployment operation was performed.

## Remaining Required Work

The broader shared `preflight_common` implementation, released-predecessor and Project V2 enforcement, controlled V2 output paths, Step 4A graph carriage and validation, Step 4B Project V2 locale and service-area binding, prompt updates, and the full OMO suite are not implemented by this partial remediation and require completion before the Sprint 3 request can be approved.
