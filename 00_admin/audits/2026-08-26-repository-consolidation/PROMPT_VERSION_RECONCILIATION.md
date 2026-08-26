# Prompt Version and Registry Reconciliation

**Author:** Raphael Rechberger
**Date:** 2026-08-26
**Scope:** All prompt files plus the 9 active entries in `standards/runtime/official-prompt-registry.json`

## Result

- 15 prompt files are present after preserving the exact Step-1 v2.1.0 predecessor.
- 9 Workflow prompts are active through the official registry.
- 1 Intake prompt is active through `services/operator_api/intake_project_generator.py`.
- 5 older prompt versions remain immutable and are not runtime-selected.
- Every active Workflow prompt hash and every bound output-contract hash matches the official registry.
- The only active semantic inconsistency was the Step-1 metadata pointer to superseded `prompts/0-kickoff.xml.md`.
- The exact v2.1.0 bytes were preserved before the active stable path was advanced to v2.2.0 with logical predecessor Step `0`.

## Complete prompt matrix

| Path | Embedded version | Runtime status | Selection authority | SHA-256 |
|---|---:|---|---|---|
| `prompts/0-kickoff-v1.10.0.xml.md` | 1.10.0 | active | Official registry Step 0 | `eac03e7bc82437bb6a5a567ad8765c6cad4066a6816200ae91a29d7a5edf9e30` |
| `prompts/0-kickoff-v1.9.0.xml.md` | 1.9.0 | superseded, reproducibility only | none | `f90a0cb583f095b671ff06e215b238127d75b98c21469dc279edcf4d701958ed` |
| `prompts/0-kickoff.xml.md` | 1.8.0 | superseded, reproducibility only | none | `e9d4619897808b05495c555d75f62819731582aa5bae9f2357f0d0573e7c375c` |
| `prompts/1-pillar-identifikation.xml.md` | 2.2.0 | active | Official registry Step 1 | `3658bed19f033ad8a135f633dcaeb97c9b6094a5b5d448b879c83ff25edd723c` |
| `prompts/1-pillar-identifikation-v2.1.0.xml.md` | 2.1.0 | superseded, exact predecessor | none | `a7312773dbdd80787f38b603ee9ed234cf3bb8d0d86b90e5822fa24680ce80bb` |
| `prompts/1b-seitenarchitektur.xml.md` | 2.1.0 | active | Official registry Step 1B | `71d5bbbea3839aa447b60866de75cb3b31a764659572b704c33f9eb801667fac` |
| `prompts/1c-pillar-template.xml.md` | 2.1.0 | active | Official registry Step 1C | `7b12fac9cec125aa1932242a9a0d0b1fdf580cccd7faefa855a5c4c3bc1eefdb` |
| `prompts/2-cluster-recherche.xml.md` | 2.2.0 | active | Official registry Step 2 | `a3c498d84b4d7187a2a0335a5fc6607226870ad415c8e6ebcf7c664ca75aec23` |
| `prompts/3-120-tage-plan.xml.md` | 2.1.0 | active | Official registry Step 3 | `adc175eb01d0cb92b4d9165a7e1ab8def889a5a9c3ea649789095e623a5e49e5` |
| `prompts/3b-performance-check.xml.md` | 2.0.0 | active, post-release only | Official registry Step 3B | `ff5d5aff300823ab859e72f150a331fadab6b426b4de71d77350363872215369` |
| `prompts/4a-content-briefing-und-schema.xml.md` | 2.2.0 | active | Official registry Step 4A | `f97bcd37990e8207916ff88c6ce4b0980aeefeecbfb77eeae1200a4bd5dec3f9` |
| `prompts/4b-landingpage-html.xml.md` | 2.1.0 | active | Official registry Step 4B | `35520d1069c45b6346c3ed971489dfa21e46749b838418acfe941961201352bc` |
| `prompts/intake-project-v2-v1.3.0.xml.md` | 1.3.0 | active Intake | `intake_project_generator.py` | `1599f8b0c61151612601280c807270a25ebb813b62e246868f7b0a1ae1b28f6a` |
| `prompts/intake-project-v2-v1.2.0.xml.md` | 1.2.0 | superseded, reproducibility only | none | `7dd0522b3f353d2e840988ad1448e187eaa0d2d374c2bc6ec726901f06ebbfab` |
| `prompts/intake-project-v2.xml.md` | 1.1.3 | superseded, reproducibility only | none | `16907a5db60c82353bd1bf902db4e587cc1b00f6f2765a1331707da5af42293c` |

## Step-1 v2.2.0 coordinated review

| Component | Decision |
|---|---|
| Prompt version | Advanced from 2.1.0 to 2.2.0 |
| Prompt path | Stable active path retained so Step-0 `next_step` and runtime path contracts remain valid |
| Old prompt bytes | Preserved as `prompts/1-pillar-identifikation-v2.1.0.xml.md` |
| Output schema | Unchanged at Step-1 Topic Inventory 2.0.0 because candidate shape and semantics did not change |
| Validator | Unchanged because only predecessor metadata was corrected to the existing logical Step-0 binding |
| Renderer | Unchanged because output shape is unchanged |
| Quality Gates | Unchanged because the released Step-0 source requirement already existed and remains fail-closed |
| Context Package | Uses official registry version and SHA-256, therefore new runs bind v2.2.0 while old records remain reproducible by hash |
| Activation | Immediate for new Step-1 executions through the official registry; no historical run is rewritten |

## Runtime and policy checks

Active prompts:

- do not invoke providers directly;
- route allowed operations through bounded Heartweb tools;
- keep Core state transitions, approvals, releases, hashing and persistence outside the agent;
- prohibit invented metrics, claims, locations, Evidence and silent fallbacks;
- bind outputs to registered contracts and released predecessor closure.

## Verification evidence

```text
python -m unittest tests.contracts.test_llm_runtime_contracts.LlmRuntimeContractTests.test_official_registry_matches_current_prompts_outputs_and_workflow_steps
Ran 1 test in 0.310s
OK

python -m unittest tests.test_intake_project_generator
Ran 4 tests in 0.025s
OK
```

The generated repository registry must classify the five predecessor files as superseded and regenerate their current hashes before final integration.
