# Sprint 3 Ultimate Quality Approval

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Fresh independent read-only final audit of Sprint 3 Tasks 3.1 through 3.10. `AGENTS.md`, the Sprint 3 task matrix, reports 18 through 20, the current provider gateway, Step 2 and Step 3 preflights, renderers and tests, predecessor paths, prompts, output and lineage contracts, schemas, `.gitattributes`, and the current worktree diff were inspected. Earlier reports were navigation only and were not used as proof.

## Final Verdict

APPROVED

No P0 through P3 defect was independently reproduced. The provider hash and public renderer trust-boundary fixes close the previously reported false-green paths.

## Findings

### P0

No P0 findings verified.

### P1

No P1 findings verified.

The provider gateway calculates the SHA-256 value from canonical UTF-8 `raw_response` bytes and rejects any unequal declared digest. Step 2 compares each row to the gateway-calculated digest. Step 2 and Step 3 public render and write paths call their operational preflights before deriving content or preparing a destination.

### P2

No P2 findings verified.

`.gitattributes` defines text normalization and LF output for the repository's relevant textual source and contract formats, while declared binary formats are unset as text. `git check-attr text eol` returned `text: set` and `eol: lf` for Python, JSON, prompt Markdown, and output-contract Markdown samples, and `text: unset` for the PDF sample.

### P3

No P3 findings verified.

## Task Resolution Matrix

| Task | Result | Independently observed current control |
| --- | --- | --- |
| 3.1 Step 1B architecture | Pass | Closed candidate, exact released predecessor lineage, decision and link validation, and deterministic views are covered by the passing suite. |
| 3.2 Step 1C design | Pass | Design and template lineage, service-area safety, accessibility, JSON-LD references, and multi-template rendering are covered by the passing suite. |
| 3.3 Step 1C templates | Pass | Controlled per-template destinations and complete template rendering are covered by `test_cross_step_safety` and controlled-output tests. |
| 3.4 Provider contracts | Pass | A stale asserted raw-response hash was independently rejected after recomputing the canonical payload digest. |
| 3.5 Step 2 evidence | Pass | Exact provider-record coverage, gateway validation, declared unique row evidence, released lineage, and candidate-only renderer rejection were reproduced. |
| 3.6 Step 3 plan | Pass | Released Step 2 byte binding, deterministic solver projection, canonical solver hashes, and candidate-only renderer rejection were reproduced. |
| 3.7 Step 4A briefing | Pass | Local JSON-LD validation, canonical graph hashing, claim binding, YMYL evidence, and repository-local import portability passed. |
| 3.8 Step 4B page | Pass | Canonical page and staging hashes, unsafe markup rejection, deployment binding, service-area controls, and actual graph rendering passed. |
| 3.9 Step 3B adjustment | Pass | Released source artifact, new revision, and changed content hash checks passed. |
| 3.10 V2 integration | Pass | Prompt predecessor and controlled output contracts agree with public preflight and renderer boundaries. |

## Independently Reproduced Evidence

1. `env PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: PASS. Acceptance: 7. Root discovery: 171. Contract discovery: 37. Total: 215 tests.

2. `env PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_preflight_common tests.test_step2_renderer tests.test_step3_renderer tests.test_step4a_import_portability tests.test_cross_step_safety tests.test_operator_error_routing -v`
   Result: PASS. 30 tests, including stale provider-hash rejection, operational lineage acceptance and omission rejection, candidate-only Step 2 and Step 3 render and write rejection, previous malicious-driver controls, stable operator routing, and Windows external-MCP import portability.

3. Direct in-memory probe using complete non-AHD Step 2 and Step 3 fixtures, with only the first provider `raw_response` changed while preserving its old declared digest.
   Result: `declared_equals_computed=False`, `gateway_blocked=True`, and `step2_preflight_blocked=True`. The gateway returned the `raw_response_hash_mismatch` violation. Candidate-only Step 2 and Step 3 renderer calls both raised their renderer errors and emitted no derived content.

4. Direct public CLI probes streamed candidate-only JSON through `/dev/stdin` to `python -m services.step2_preflight.render` and `python -m services.step3_preflight.render` with the repository root as `--workspace-root`.
   Result: both exited with `RendererError` before `prepare_step_output`; errors included missing released predecessor lineage. A subsequent `v2/**` inspection returned no files, so neither probe emitted an output.

5. `git diff --check`
   Result: exit code 0. Git printed CRLF-to-LF conversion warnings for existing modified tracked files, but no whitespace diagnostics.

6. `git check-attr text eol -- .gitattributes services/provider_gateway/core.py services/step2_preflight/render.py standards/outputs/step-2-keyword-evidence.schema.json prompts/2-cluster-recherche.xml.md standards/dateinamen-und-output-vertrag.md docs/07-geo-research-und-copywriter-guidelines.pdf`
   Result: inspected textual files resolved to `text: set` and `eol: lf`; the PDF resolved to `text: unset`.

7. `env PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; roots=[Path('services'),Path('standards/outputs'),Path('prompts')]; files=[path for root in roots for path in root.rglob('*') if path.is_file() and path.suffix in {'.py','.json','.md'}]; forbidden=[path for path in files if '\u2013' in path.read_text(encoding='utf-8') or '\u2014' in path.read_text(encoding='utf-8')]; ahd=[path for path in files if 'ahd' in path.read_text(encoding='utf-8').casefold()]; print({'files_scanned':len(files),'forbidden_dash_matches':len(forbidden),'ahd_matches':len(ahd)})"`
   Result: 66 text artifacts scanned, zero U+2013 matches, zero U+2014 matches, and zero case-insensitive `AHD` matches. Passing provider, Step 2, Step 3, Step 4A, Step 4B, and cross-step tests use contrasting non-AHD fixtures.

8. `env PYTHONDONTWRITEBYTECODE=1 python -c "import ast; from pathlib import Path; files=[path for path in Path('services').rglob('*.py')]+[path for path in Path('tests').rglob('*.py')]; [ast.parse(path.read_text(encoding='utf-8'), filename=str(path), feature_version=(3, 11)) for path in files]; print({'python_311_syntax_files_parsed':len(files)})"`
   Result: 88 Python files parsed successfully with Python 3.11 grammar.

## Limits

- `python3.11 --version` is unavailable in this Linux environment. Python 3.11 grammar compatibility was checked locally, while native Windows Python 3.11 execution remains controller-provided evidence.
- No network, provider, crawler, browser, deployment, external validator, commit, push, stage, or destructive action was used.
- The worktree contains the reviewed uncommitted Sprint 3 changes. This audit created only this report and did not alter source, tests, fixtures, schemas, prompts, state, configuration, or existing reports.

APPROVED
