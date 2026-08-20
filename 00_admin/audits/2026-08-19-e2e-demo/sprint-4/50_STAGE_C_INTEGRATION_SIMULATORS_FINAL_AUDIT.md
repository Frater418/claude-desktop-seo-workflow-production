# Stage C Integration Simulators Final Audit

Date: 2026-08-20
Auditor: Fresh read-only reviewer
Scope: Stage C Notion and n8n simulators, their V2 contracts and tests, plus the necessary Stage A2 context and Stage B event boundaries. No source, test, contract, configuration, fixture, or prior report was changed. No network, provider, live integration, filesystem mutation by a probe, or Stage D work was used.

## Governing Expectations And Evidence Reviewed

The audit read `AGENTS.md`, `00_admin/DECISIONS.md` including DEC-0018 and DEC-0019, and all required Sprint 4 records:

- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/02_INTEGRATION_SIMULATION_RESEARCH.md`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/17_STAGE_A2_IMPLEMENTATION_PLAN.md`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/49_STAGE_C_INTEGRATION_SIMULATORS_IMPLEMENTATION.md`

Primary expectations were: local pure simulators only, Transition Service remains the sole canonical authority, Notion is a non-authoritative projection, n8n only transports and orchestrates typed commands, simulated and live identities are mutually exclusive, and all context, request, predecessor, revision, and hash boundaries fail before dispatch. DEC-0019 specifically makes exact Context Package bytes and hashes authoritative and requires stale, hash-invalid, and cross-tenant inputs to stop before an LLM request.

Implementation and contract evidence inspected:

- `services/integrations/notion_simulator.py`
- `services/integrations/n8n_simulator.py`
- `services/integration_contracts/notion_graph.py`
- `services/context_builder/validator.py`
- `services/context_builder/session_policy.py`
- `services/operator_api/event_store.py`
- `tests/test_notion_simulator.py`
- `tests/test_n8n_simulator.py`
- `tests/contracts/test_integration_contracts_v2.py`
- `standards/integrations/workflow-event-v2.schema.json`
- `standards/integrations/notion-record-v2.schema.json`
- `standards/integrations/n8n-command.schema.json`
- `standards/integrations/n8n-simulation-state.schema.json`
- `standards/integrations/n8n-wait-subscription.schema.json`
- `standards/integrations/n8n-dlq-entry.schema.json`
- `standards/workflow/workflow-graph.json`

## Commands Actually Run

All commands were local and read-only. Inline Python probes used in-memory mappings only and created no repository artifacts.

| Command | Outcome |
|---|---|
| `python --version` | Exit 0. Reported `Python 3.12.3`. |
| `python3 --version` | Exit 0. Reported `Python 3.12.3`. |
| `command -v python3.11` | Exit 1 with no output. Python 3.11 is not installed. |
| `PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v` | Exit 127. `/usr/bin/bash: python3.11: command not found`. |
| `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v` | Exit 0 under Python 3.12.3. Ran 28 tests, `OK`. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; from tests.test_notion_simulator import contracts, load_json; from services.integrations.notion_simulator import materialize_events; events=load_json(Path('tests/fixtures/integrations/v2/positive-workflow-events.json')); snapshot=materialize_events(events, contracts()); print('records=' + ','.join(sorted({record['record_type'] for record in snapshot['records'].values()}))); print('count=' + str(len(snapshot['records'])))"` | Exit 1. Raised `NOTION_SIMULATION_STALE_REVISION` for the schema-valid all-event V2 fixture. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; from tests.test_notion_simulator import contracts, load_json; from services.integrations.notion_simulator import materialize_events; events=load_json(Path('tests/fixtures/integrations/v2/positive-workflow-events.json')); snapshot=materialize_events([events[4], events[5]], contracts()); print([(record_id, record['projected_status']) for record_id, record in sorted(snapshot['records'].items()) if record['record_type']=='gate'])"` | Exit 0. Printed distinct same-gate records: `gate-gate-1-00000005` ready and `gate-gate-1-00000006` approved. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from tests.test_n8n_simulator import command, request, contracts; from services.integrations.n8n_simulator import simulate_n8n; cross=command('wait_for_gate'); cross['target']={'service':'workflow_api','operation':'wait'}; cross['tenant_id']='tenant-other'; cross['project_id']='project-other'; result=simulate_n8n(request(cross), contracts()); print('accepted=' + str(len(result.wait_subscriptions)==1) + ', tenant=' + result.wait_subscriptions[0]['tenant_id'] + ', project=' + result.wait_subscriptions[0]['project_id'])"` | Exit 0. Printed `accepted=True, tenant=tenant-other, project=project-other`; the same simulation state accepts a different tenant and project. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from tests.test_n8n_simulator import command, request, contracts; from services.integrations.n8n_simulator import simulate_n8n; forged={'step_id':'0','status':'released','tenant_id':'tenant-other','project_id':'project-other','run_id':'run-other-0001','artifact_id':'artifact-other-0001','artifact_sha256':'0'*64,'artifact_revision':999,'gate_id':'GATE-0'}; result=simulate_n8n(request(command(), releases=(forged,)), contracts()); print('dispatches=' + str(len(result.dispatch_intents)) + ', accepted_predecessor_tenant=' + forged['tenant_id'])"` | Exit 0. Printed `dispatches=1, accepted_predecessor_tenant=tenant-other`; a bare cross-tenant release is accepted. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "import copy; from dataclasses import replace; from tests.test_n8n_simulator import command, request, contracts; from services.integrations.n8n_simulator import simulate_n8n; base=request(command(), releases=({'step_id':'0','status':'released'},)); package=copy.deepcopy(base.context_package); llm=copy.deepcopy(base.llm_request); package['package_sha256']='0'*64; llm['context_package_sha256']='0'*64; llm['input_sha256']='0'*64; result=simulate_n8n(replace(base, context_package=package, llm_request=llm), contracts()); print('dispatches=' + str(len(result.dispatch_intents)) + ', accepted_hash=' + result.dispatch_intents[0]['context_package_sha256'])"` | Exit 0. Printed one dispatch with the forged all-zero Context Package hash. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from tests.test_n8n_simulator import command, request, contracts; from services.context_builder.session_policy import _cache_projection; from services.integrations.n8n_simulator import simulate_n8n; retry=command('retry_delivery'); retry['target']={'service':'delivery_queue','operation':'retry'}; seed=request(retry, releases=({'step_id':'0','status':'released'},)); cache=_cache_projection(seed.context_package, contracts().worker_profile) | {'session_state':'available','expires_at':'2026-08-21T00:00:00Z'}; fresh=simulate_n8n(request(command(), releases=({'step_id':'0','status':'released'},)), contracts()); reused=simulate_n8n(request(retry, releases=({'step_id':'0','status':'released'},), cache_record=cache), contracts()); recovered=simulate_n8n(request(retry, releases=({'step_id':'0','status':'released'},), cache_record={'session_state':'lost'}), contracts()); denied=simulate_n8n(request(retry, releases=({'step_id':'0','status':'released'},), package_current=False), contracts()); print('fresh='+fresh.technical_session_decision+', reuse='+reused.technical_session_decision+', recover='+recovered.technical_session_decision+', denied='+denied.technical_session_decision)"` | Exit 0. Printed `fresh=fresh_required, reuse=reuse_permitted, recover=recover_fresh, denied=denied`. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "import copy; from dataclasses import replace; from tests.test_n8n_simulator import command, request, contracts; from services.integrations.n8n_simulator import simulate_n8n; retry=command('retry_delivery'); retry['target']={'service':'delivery_queue','operation':'retry'}; first=simulate_n8n(request(retry, releases=({'step_id':'0','status':'released'},)), contracts()); state2=copy.deepcopy(first.state); state2['clock']['current_time']='2026-08-20T00:01:00Z'; base2=request(retry, releases=({'step_id':'0','status':'released'},)); second=simulate_n8n(replace(base2, state=state2), contracts()); state3=copy.deepcopy(second.state); state3['clock']['current_time']='2026-08-20T00:02:00Z'; base3=request(retry, releases=({'step_id':'0','status':'released'},)); third=simulate_n8n(replace(base3, state=state3), contracts()); entry=third.dlq_entries[0]; print('first_failed_at='+entry['first_failed_at']+', failed_at='+entry['failed_at'])"` | Exit 0. Printed `first_failed_at=2026-08-20T00:02:00Z, failed_at=2026-08-20T00:02:00Z`; first failure provenance is overwritten by terminal time. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; from tests.test_notion_simulator import contracts, load_json; from services.integrations.notion_simulator import materialize_events; event=load_json(Path('tests/fixtures/integrations/v2/positive-workflow-events.json'))[-1]; snapshot=materialize_events([event], contracts()); print('record_types=' + ','.join(sorted({record['record_type'] for record in snapshot['records'].values()}))); print('conflicts=' + str(snapshot['conflicts']))"` | Exit 0. Printed only `customer,project,run,step` and `conflicts=[]` for `integration.conflict_detected`. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from tests.test_notion_simulator import contracts, event; from services.integrations.notion_simulator import materialize_events; ordered=[event('project.created','event-demo-0001'),event('task.created','event-demo-0007'),event('assignment.created','event-demo-0008')]; shuffled=[ordered[2],ordered[0],ordered[1]]; print('shuffled_deterministic=' + str(materialize_events(ordered, contracts()) == materialize_events(shuffled, contracts())))"` | Exit 0. Printed `shuffled_deterministic=True` for a same-revision stream. |
| `PYTHONDONTWRITEBYTECODE=1 python3.11 -c "from pathlib import Path; paths=('services/integrations/notion_simulator.py','services/integrations/n8n_simulator.py'); [compile(Path(path).read_text(encoding='utf-8'), path, 'exec') for path in paths]; print('Stage C syntax OK')"` | Exit 127. Required Python 3.11 syntax check could not run because the executable is absent. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; paths=('services/integrations/notion_simulator.py','services/integrations/n8n_simulator.py'); [compile(Path(path).read_text(encoding='utf-8'), path, 'exec') for path in paths]; print('Stage C syntax OK under ' + __import__('sys').version.split()[0])"` | Exit 0. Diagnostic only, not a Python 3.11 substitute. Printed `Stage C syntax OK under 3.12.3`. |

## Required Behavior Coverage

| Required behavior | Evidence and result |
|---|---|
| Exact Notion schema and graph validation | Passed by the 28-test focused suite, including V2 contract graph validation and ordinary materialization. The complete schema-valid V2 event stream fails materialization, which is a finding below. |
| Equal replay and changed duplicate | Passed focused Notion and n8n tests. Equal event replay is deterministic and changed same-event content fails. |
| Out-of-order timestamps and revision rollback | Same-revision shuffled events are deterministic. A global revision watermark rejects the valid all-event fixture after its revision-2 checkpoint precedes valid revision-1 events. |
| Tenant, project, and simulation mixing | Notion rejects mixed event streams and live masquerading. n8n accepts a cross-tenant/project wait in one simulation, failing isolation. |
| Every record type, assignment role, and unassigned case | Focused tests cover four roles and unassigned tasks. The all-event materialization fails, and conflict events produce no conflict or integration-status record. |
| Stale proposal and no authority | Passed focused Notion tests. Stale proposals fail and output is a Core command request without canonical status. Authority constants remain `transition_service` and `atomic_state_writer: false`. |
| Determinism under shuffled events | Passed for a valid same-revision event set. Full ordered V2 coverage is blocked by the revision-watermark defect. |
| Exact n8n graph and released predecessor | Initial route and 30/60/90 dispatch tests pass. The predecessor proof accepts a cross-tenant, hash-wrong bare release object. |
| Context and request hashes | A forged all-zero package hash and matching request hashes dispatch successfully. This fails the required validation boundary. |
| Fresh, cache, and recover flows | Passed direct probe: `fresh_required`, `reuse_permitted`, `recover_fresh`, and `denied`. |
| Forbidden approve and complete flows | Passed focused tests and command schema rejects `approve_gate` and `complete_run`. |
| Wait gate and task behavior | Passed focused tests for `gate.approved` and `task.resolved`; wait output is schema-validated. |
| Replay and conflict behavior | Passed focused equal replay and changed command conflict tests. V2 integration conflict events are not materialized. |
| Retry attempts and DLQ provenance | Bounded attempts and a schema-valid DLQ entry pass. `first_failed_at` is incorrectly set to the terminal attempt time, and the DLQ contract has no immutable original envelope or envelope hash. |
| Day 30, 60, and 90 only, plus immutable 3b plan behavior | Day-only enforcement passes. `simulate_n8n` does not validate immutable Step 3 plan lineage before 3b dispatch because it only schema-validates the package. |
| Cross-identity and live masquerade protection | Live masquerading is rejected. Cross-tenant/project n8n wait and predecessor inputs are accepted. |
| No input mutation, I/O, or fallback behavior | Focused tests pass no-mutation and static no-I/O checks. Direct source inspection confirms caller-injected mappings, deep copies, no filesystem, network, clock, subprocess, or provider calls in the two simulator modules. |
| All ten prescribed archetypes | Contract tests reference exactly ten archetypes, and Notion test materializes a project event for each. There is no n8n parameterized ten-archetype behavioral test. |
| Python 3.11 syntax | Not verified. Python 3.11 is unavailable. Python 3.12.3 compilation passed only as diagnostic evidence. |

## Spec Conformance Findings

### P0

1. `S-P0-01`: `simulate_n8n` dispatches a forged Context Package hash. `services/integrations/n8n_simulator.py:118-129` calls only `RuntimeContractValidator.validate` and `validate_llm_request`; neither performs the Stage A2 semantic package validation that recomputes `package_sha256` in `services/context_builder/validator.py:123-130`. The direct probe dispatched an all-zero hash. This violates DEC-0019 and the Stage C requirement that only validated LLM requests with retained Context Package identity may dispatch.

2. `S-P0-02`: n8n does not bind a simulation state to tenant, project, or run scope. `services/integrations/n8n_simulator.py:68-113` validates only matching simulation IDs for non-dispatch commands. A cross-tenant/project `wait_for_gate` command was accepted and queued against the same simulation. This violates DEC-0018 identity isolation and the Stage B tenant-isolation gate.

### P1

1. `S-P1-01`: Notion cannot materialize its complete schema-valid V2 event fixture. `services/integrations/notion_simulator.py:64-70` applies one global highest revision across events, then rejects any lower revision. The official fixture validly contains a revision-2 Step 3b checkpoint followed by revision-1 Step 4b integration events and fails with `NOTION_SIMULATION_STALE_REVISION`. The research requires out-of-order events to remain auditable without overwriting a newer projection, not wholesale rejection. This prevents the required every-event and every-record-type integration simulation.

2. `S-P1-02`: `integration.conflict_detected` is in the exact V2 event catalog and schema but has no mapping in `services/integrations/notion_simulator.py:116-168`. A valid conflict event returns only base customer/project/run/step records and an empty `conflicts` list. The required stale-conflict operational projection is absent.

3. `S-P1-03`: The n8n predecessor check at `services/integrations/n8n_simulator.py:132-143` accepts only matching `step_id` and `status`. It does not bind tenant, project, run, artifact, artifact hash, artifact revision, gate, or release identity. The direct probe dispatched Step 1 using a deliberately cross-tenant, hash-wrong forged predecessor. This is not the matching released predecessor required by DEC-0019 and the workflow graph.

4. `S-P1-04`: Step 3b dispatch verifies only day and a released Step 4b in `services/integrations/n8n_simulator.py:136-143`. It does not validate an immutable released Step 3 plan or its hash before requesting adjustment work. The declared immutable Step 3b plan behavior is therefore not enforced at the simulator boundary.

### P2

1. `S-P2-01`: The same logical gate is materialized once per event because `_gate_id` includes `event_id` at `services/integrations/notion_simulator.py:130-136,178-179`. A `gate.ready` then `gate.approved` stream produces two distinct GATE-1 records rather than one relation-preserving gate projection with updated provenance. This weakens the required Notion relation model and makes gate history ambiguous.

### P3

None.

## Quality Findings

### P0

None beyond the P0 conformance defects above.

### P1

1. `Q-P1-01`: The required Python 3.11 execution and syntax evidence is unavailable. The repository environment exposes only Python 3.12.3, and `python3.11` is absent. The Stage C report's Python compatibility claim cannot be independently verified under the mandated interpreter.

2. `Q-P1-02`: Test coverage overstates all-event simulator coverage. `tests/test_notion_simulator.py` hand-builds a subset stream and never materializes `tests/fixtures/integrations/v2/positive-workflow-events.json`, although `tests/contracts/test_integration_contracts_v2.py` proves that fixture schema-valid and includes every V2 event. The omitted integration execution test would have exposed `S-P1-01` and `S-P1-02`.

### P2

1. `Q-P2-01`: DLQ provenance is not historically accurate. `_dlq` at `services/integrations/n8n_simulator.py:170-173` derives both `first_failed_at` and `failed_at` from the terminal call clock. The direct three-attempt probe showed both timestamps at `00:02`, not the first attempt at `00:00`. `standards/integrations/n8n-dlq-entry.schema.json` also retains only `original_command_id`, not an immutable original command envelope or hash, contrary to the research provenance expectation.

2. `Q-P2-02`: The ten-archetype evidence is partial. `tests/test_notion_simulator.py:159-168` projects one `project.created` event for each archetype, but `tests/test_n8n_simulator.py` has no parameterized archetype execution. The Stage C plan requires simulator tests across all ten archetypes, including transport, wait, retry, DLQ, resume, and 3b behavior.

### P3

None.

## Residual Risks And Remediation Boundary

- The passing focused suite establishes contract-shape validation, selected deterministic behavior, authority constants, and no-I/O source checks. It does not establish conformance of the simulator behavior to the closed V2 event stream or the protected runtime trust boundary.
- Required corrections are confined to Stage C simulators, V2 simulator contracts where provenance must be represented, and their Stage C tests. They do not require Stage D OpenAPI, generated types, UI, API-integration work, or live integrations.
- No Stage D dependency is a condition of this audit verdict.

## Verdict

REQUEST_CHANGES
