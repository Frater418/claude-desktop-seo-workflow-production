# Sprint 3 Output Contract Integration

## Scope

This change harmonizes the authorized canonical output and support-output schemas for Steps 1, 1b, 1c, 2, 3, 3b, 4a, and 4b. Step 0, renderer work, runtime services, quality registry, operator routing, provider gateway, project state, and plans were not changed.

The V2 common contract is now consistently required: `schema_version`, `artifact_id`, `run_id`, `project_id`, `step_id`, `revision`, `source_artifact_ids`, `evidence_ids`, `decision_records`, and `candidate_status: awaiting_gate`. Deployment IDs remain required only on deployment-scoped schemas.

Step 1 now carries the same lifecycle fields while retaining its specialized source, competitor, existing URL, and crawl evidence arrays. Step 1b and Step 1c use `candidate_status` rather than generic output `status`. Steps 2 and 3 now use `awaiting_gate` rather than `candidate`.

## RED Evidence

The meta-contract test was created and run before production harmonization:

```text
python -m unittest tests.contracts.test_output_contracts_v2 -v
```

The initial valid RED run reported 14 failures. It showed that Step 1 lacked the common lifecycle fields, Steps 1b and 1c required generic `status`, and Steps 2 and 3 constrained `candidate_status` to `candidate`. It also showed prompt-boundary wording gaps.

## Contract and Prompt Coverage

`tests/contracts/test_output_contracts_v2.py` covers all eleven authorized schemas, including the Step 1c design-system and template outputs, the Step 4a claim ledger, and the Step 4b staging evidence support output. It verifies Draft 2020-12, a closed root object, all common required fields, exact step constants, `awaiting_gate`, no AHD or client literals, and unique schema IDs.

The same test parses each of the eight V2 prompt XML bodies and verifies the 2.0.0 version, released predecessor, canonical JSON, derived-view wording, awaiting-gate status, external Human Gate, and structured prohibition language for legacy-manifest mutation, automatic next steps, and direct provider calls. It inspects the prohibition section so explicit prohibitions are not mistaken for forbidden actions.

Non-AHD product, solar, outdoor retail, and B2B fixtures remain covered by the focused Step 1b through 4b tests. The contracts remain data-driven and contain no customer-specific values.

## Verification

Focused verification command:

```text
python -m unittest tests.test_step1_contract_v2 tests.test_step1b_contract tests.test_step1c_contract tests.test_step2_contract tests.test_step3_contract tests.test_step3b_contract tests.test_step4a_contract tests.test_step4b_contract tests.contracts.test_output_contracts_v2 -v
```

Result: 47 tests passed.

OMO multi-phase full suite command:

```text
python tests/run_full_suite.py
```

Result: acceptance 7 of 7, root unittest discovery 136, contract unittest discovery 37, total 180 tests passed.

LSP diagnostics were requested for each changed Python test file. `basedpyright` is not installed in this environment and had previously been declined, so no LSP diagnostic result was available. No network, provider call, crawl, deployment, or commit was performed.
