# Sprint 3 Host Integration Fix

**Author:** Raphael Rechberger
**Date:** 2026-08-19
**Scope:** Independently observed Sprint 3 host-integration failures only.

## Changes

- Replaced the Python 3.12-only `type JsonValue =` declarations in the provider gateway and Step 2 and Step 3 preflight validators with `typing.TypeAlias` declarations. The declarations are valid Python 3.11 and Python 3.12 syntax.
- Restored the prompt acceptance contract in prompts 1b, 1c, 2 and 3. Every prompt now contains a `<validation_rules>` block and at least one stable `ERROR_` code while retaining the V2 prohibitions and `awaiting_gate` behavior.
- Added all 26 Sprint 3 runtime errors to the independent canonical catalog and exactly one route and owner mapping for each. The existing AST production-emission completeness test was retained unchanged.
- No Lane C source or fixtures were edited. Lane C remains outside this repair scope.

## TDD Evidence

The existing routing completeness regression was run before the repair:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_error_routing -v
```

Result: 8 tests ran with 1 expected failure. The unchanged AST regression reported 25 literal Sprint 3 emitted codes absent from `CANONICAL_RUNTIME_ERROR_CODES`. The provider gateway's separately declared consolidated `ERROR_PROVIDER_GATEWAY` code was included in the repaired catalog and policy as well.

The same regression passed after the repair. No test was weakened, deleted, broadened or otherwise changed.

## Verification

### Focused Lane A

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_step1b_contract tests.test_step1c_contract
```

Result: 11 tests passed in 0.198 seconds.

### Focused Lane B

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_provider_gateway tests.test_step2_contract tests.test_step3_contract
```

Result: 9 tests passed in 0.072 seconds.

### Acceptance

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_acceptance_tests.py
```

Result: 7/7 acceptance tests passed. This includes the strict fail-fast validation across all 9 prompts.

### Independent Routing

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_operator_error_routing
```

Result: 8 tests passed in 0.423 seconds. The policy schema, duplicate and missing-map guards, canonical-only policy ownership and AST production-emission completeness regression all passed.

### OMO Multi-Phase Full Suite

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: passed. Acceptance runner: 7 tests. Root unittest discovery: 136 tests. Contract unittest discovery: 35 tests. Total: 178 tests.

## Diagnostics and Environment Limits

- `lsp_diagnostics` was requested for `services/provider_gateway/core.py`, `services/step2_preflight/validator.py`, `services/step3_preflight/validator.py` and `services/operator_routing/router.py`.
- The configured basedpyright server is not installed and installation was previously declined, so no LSP diagnostic result could be produced.
- Validation used only local test runners. No provider call, network activity, crawl, deployment, commit, state mutation or Lane C source or fixture change occurred.

## Post-Write Review

- Single responsibility: the three validators retain their individual contract boundaries, and the router retains the independent canonical error inventory.
- Boundary purity: no runtime payload boundary or schema changed.
- Variants and escape hatches: no tagged-variant branches, `Any`, casts, suppressions, broad exception handling or fallback path was added.
- Defensive layers, parameter bloat, redundant destructive-action verification, negative naming and logging changes: none added.
- Test lock: the unchanged AST regression fails when an emitted Sprint 3 runtime code is absent from the canonical routing catalog.
- Size: all changed Python files remain below 250 pure lines.
