# Sprint 3 Provider Hash and Renderer Gate Fix

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Sprint 3 P1 provider raw-response hashing and Step 2 and Step 3 public renderer trust boundaries.

## Implemented Controls

- `validate_exchange` now computes SHA-256 from exact canonical UTF-8 bytes produced by `json.dumps(raw_response, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")`.
- The provider gateway rejects a declared digest that differs from those bytes with the stable `raw_response_hash_mismatch` gateway violation. Returned `raw_response_sha256` is the computed digest.
- Step 2 operational preflight therefore compares each verified row with the gateway-computed digest while retaining exact one-record, unique evidence-ID coverage.
- `render_step2` and `write_step2` now require `validate_step2_preflight` on the full operational bundle before deriving rows or preparing an output path.
- `render_step3` and `write_step3` now require `validate_step3_preflight` on the full operational bundle before deriving a plan or preparing an output path.

## RED Evidence

1. Command:
   `env PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_preflight_common tests.test_step2_renderer tests.test_step3_renderer`

   Result before production changes: 15 tests run, 7 failures. Six failures were the intended provider stale-hash, Step 2 tampered full-bundle, Step 2 candidate-only render/write, and Step 3 candidate-only render/write probes. One additional failure exposed test-fixture ordering: the Step 3 positive fixture projected Step 2 rows before the helper bound their computed hashes.

2. After correcting that test-fixture ordering without changing production behavior, the same command remained RED with 15 tests run and 6 failures. Each failure was an intended probe: unchecked stale raw hash, accepted tampered Step 2 provider evidence, or candidate-only Step 2 or Step 3 rendering and writing.

## GREEN Verification

1. `env PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_preflight_common tests.test_step2_renderer tests.test_step3_renderer`
   Result: PASS, 15 tests.

2. `env PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_step2_contract tests.test_step2_renderer tests.test_step3_contract tests.test_step3_renderer tests.test_final_review_fixes tests.test_preflight_common`
   Result: PASS, 28 tests.

3. `env PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: PASS, 215 total tests: 7 acceptance, 171 root discovery, and 37 contract discovery.

4. `git diff --check`
   Result: PASS. Git emitted existing CRLF conversion warnings for tracked files outside this task allowlist, but reported no whitespace errors. No EOL or whitespace-policy changes were made.

5. LSP diagnostics were requested for every changed Python file. `basedpyright` is not installed and prior installation was declined, so no LSP result was available.

## Scope Confirmation

- No provider, network, crawl, deployment, browser, commit, push, or destructive command was used.
- No AHD or client-specific production constant was added.
- Closed awaiting-gate candidate validation remains available for non-emission validation paths.
- Public Step 2 and Step 3 artifact emission accepts only complete operational preflight bundles.
