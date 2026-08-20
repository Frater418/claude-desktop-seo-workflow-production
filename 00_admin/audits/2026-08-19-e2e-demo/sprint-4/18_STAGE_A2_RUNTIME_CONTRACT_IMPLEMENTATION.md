# Sprint 4 Stage A2 Package A2.1 Runtime Contract Implementation

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Package A2.1 only. No provider, API, event, simulator, UI, routing, state, prompt, or existing-contract change was made.

## Delivered Contracts

Created six closed Draft 2020-12 runtime schemas with stable runtime IDs:

- `logical-project-session.schema.json`
- `official-prompt-registry.schema.json`
- `worker-profile.schema.json`
- `context-package.schema.json`
- `llm-run-request.schema.json`
- `llm-run-result.schema.json`

Created the repository-owned official prompt registry. It has exactly one active entry for each workflow step: `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`. Each entry binds current prompt bytes, parsed prompt metadata version, and every named output-contract byte hash. The ordered multi-output bindings cover Step 1c, Step 4a, and Step 4b.

The logical-session contract supports immutable session revisions and the two controller binding modes. The context, request, and result contracts keep local Core authority separate from candidate generation and cache-only technical-session hints.

## TDD Evidence

RED command:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py
```

RED outcome: failed before implementation with `FileNotFoundError` for `standards/runtime/logical-project-session.schema.json`. The runner completed 0 tests and reported 1 setup error.

GREEN command:

```sh
docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python -m unittest tests/contracts/test_llm_runtime_contracts.py'
```

GREEN outcome: 7 tests passed in 0.268 seconds.

Full-suite command:

```sh
docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python tests/run_full_suite.py'
```

Full-suite outcome: 7 acceptance tests, 178 root unittest tests, and 58 contract unittest tests passed. Total: 243 tests.

## Limitations

- This environment has no `python3.11` executable. The attempted command `python3.11 -m unittest tests/contracts/test_llm_runtime_contracts.py` returned `command not found`. The executed OMO runtime used Python 3.12. The new suite uses Python 3.11-compatible stdlib syntax and installed `jsonschema` plus `referencing` only.
- `standards/manifest.schema.json`, named explicitly by Prompt 0, has no existing `$id` or schema-version declaration. Its registry binding uses the stable repository contract ID `https://heartweb.example/schema/manifest.schema.json` and registry version `1.0.0`, while its exact current bytes are SHA-256 bound.
- Cross-record semantic validation, canonical package hashing, source resolution, and cache-match comparisons remain Package A2.2 work. This package establishes the closed record shapes and fixtures only.
