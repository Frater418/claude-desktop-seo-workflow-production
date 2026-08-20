# Stage C Integration Simulators Terminal Review

Date: 2026-08-20
Auditor: New read-only terminal reviewer
Scope: Final read-only review of the corrected Stage C Notion and n8n simulators, V2 simulator contracts, fixtures, and A2 validation boundary. Only this report was created. No source, test, schema, fixture, contract, configuration, prior report, commit, push, network, provider, live-integration, or Stage D action was performed.

## Evidence Reviewed

Read: `AGENTS.md`; DEC-0018 and DEC-0019 in `00_admin/DECISIONS.md`; reports 50 and 51; `services/integrations/notion_simulator.py`; `services/integrations/n8n_simulator.py`; `services/context_builder/validator.py`; `tests/test_notion_simulator.py`; `tests/test_n8n_simulator.py`; `tests/contracts/test_integration_contracts_v2.py`; all changed n8n V2 schemas and positive fixtures; the V1 schema and fixture parity paths exercised by the contract test; the V2 event, record, projection, snapshot, proposal, command, wait, retry, DLQ, and state contracts; the workflow graph; and the full-suite runner.

DEC-0018 requires a locally executable Core with Transition Service as the protected authority, n8n as typed orchestration and transport, and Notion as a non-authoritative operational projection. DEC-0019 requires exact immutable Context Package sources, hashes, revisions, prompt identity, worker and request bindings, with stale, hash-invalid, or cross-tenant inputs rejected before dispatch.

The inspected correction is confined to the Stage C simulator and integration-contract boundary described in report 51. Working-tree inspection also found the separate `services/operator_routing/router.py` and `tests/test_operator_error_routing.py` bare-return AST scanner guard, plus its policy entries. Its only relevant effect here is that the full suite now completes. No Stage D, API, Core, prompt, output, workflow, UI, commit, or push change was introduced by this review. The current `HEAD` remains `9a5e45ac032e415b00b07ef45a6ad290b4a343d9` from 2026-08-19.

## Commands And Outcomes

All commands were local. `PYTHONDONTWRITEBYTECODE=1` prevented bytecode artifacts. Inline probes used only in-memory mappings and repository reads.

| Command | Outcome |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python --version` | Exit 0: `Python 3.12.3`. |
| `command -v python3.11` | Exit 1 with no output. Host Python 3.11 is unavailable in this terminal. |
| `PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v` | Exit 127: `python3.11: command not found`. The claimed Host Python 3.11 results are not independently substantiated in this environment. |
| `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v` | Exit 0 under Python 3.12.3: 38 tests ran, `OK`. This substantiates the OMO focused-suite claim. |
| `PYTHONDONTWRITEBYTECODE=1 python -c "import json; from pathlib import Path; from jsonschema import Draft202012Validator; paths=sorted(Path('standards/integrations').glob('*.schema.json')); [Draft202012Validator.check_schema(json.loads(path.read_text(encoding='utf-8'))) for path in paths]; print(f'meta_validated={len(paths)}')"` | Exit 0: `meta_validated=12`. |
| `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py` | Exit 0 under Python 3.12.3: acceptance 7, root unittest 241, contracts 59, total 307 tests. This substantiates the OMO full-suite claim. |
| `GIT_MASTER=1 git status --short` | Read-only inventory showed uncommitted Stage A2, B, C, and documentation work, the separate routing repair, and no Stage D path. This review added only report 52. |
| `GIT_MASTER=1 git diff -- services/operator_routing/router.py tests/test_operator_error_routing.py standards/operator/error-routing-policy.json` | Read-only diff confirmed the unrelated scanner repair is only `node.value is not None` before `ast.walk(node.value)`, with matching A2 error-routing inventory entries. |

### Pure API Probe Outcomes

Exact local probe commands:

```text
PYTHONDONTWRITEBYTECODE=1 python -c "from pathlib import Path; from tests.test_notion_simulator import contracts, event, load_json; from services.integration_contracts.notion_graph import NotionGraphTarget, validate_notion_graph; from services.integrations.notion_simulator import materialize_events; events=load_json(Path('tests/fixtures/integrations/v2/positive-workflow-events.json')); snapshot=materialize_events(events, contracts()); gates=materialize_events([event('gate.ready','event-demo-0005'),event('gate.approved','event-demo-0006')], contracts()); shuffled=materialize_events(list(reversed(events)), contracts()); print('records='+str(len(snapshot['records']))+', conflicts='+str(len(snapshot['conflicts']))+', graph='+str(validate_notion_graph(snapshot, NotionGraphTarget.SNAPSHOT, contracts().graph_schemas).valid)); print('conflict_record='+snapshot['records']['integration-status-00000001']['source_event_id']+', gate_count='+str(sum(record['record_type']=='gate' for record in gates['records'].values()))+', gate_status='+next(record['projected_status'] for record in gates['records'].values() if record['record_type']=='gate')+', shuffled_equal='+str(snapshot==shuffled))"
PYTHONDONTWRITEBYTECODE=1 python -c "import copy; from dataclasses import replace; from tests.test_n8n_simulator import command, contracts, request, state; from services.integrations.n8n_simulator import N8nSimulationError, simulate_n8n; targets={'dispatch_tool_run':{'service':'tool_runner','operation':'dispatch'},'wait_for_gate':{'service':'workflow_api','operation':'wait'},'retry_delivery':{'service':'delivery_queue','operation':'retry'},'resume_run':{'service':'workflow_api','operation':'resume'},'dead_letter':{'service':'delivery_queue','operation':'dead_letter'}}; results=[]; exec(\"for kind, target in targets.items():\\n value=command(kind); value['target']=target; value['tenant_id']='tenant-other';\\n try: simulate_n8n(request(value), contracts())\\n except N8nSimulationError as exc: results.append(kind+':'+exc.code)\\n else: results.append(kind+':ACCEPTED')\"); base=request(command()); forged_package=copy.deepcopy(base.context_package); forged_request=copy.deepcopy(base.llm_request); forged_package['package_sha256']='0'*64; forged_request['context_package_sha256']='0'*64; forged_request['input_sha256']='0'*64; checks=[]; scenarios=(('scope_simulation',replace(base,state={**state(),'simulation_id':'sim-other-0001'})),('forged_package',replace(base,context_package=forged_package,llm_request=forged_request)),('missing_record',replace(base,current_records={})),('bare_release',replace(base,releases=({'step_id':'0','status':'released'},)))); exec(\"for label, candidate in scenarios:\\n try: simulate_n8n(candidate, contracts())\\n except N8nSimulationError as exc: checks.append(label+':'+exc.code)\\n else: checks.append(label+':ACCEPTED')\"); print('scope='+'|'.join(results)); print('boundaries='+'|'.join(checks))"
PYTHONDONTWRITEBYTECODE=1 python -c "import copy; from dataclasses import replace; from pathlib import Path; from tests.test_n8n_simulator import command, contracts, load_json, request, state; from services.context_builder.session_policy import _cache_projection; from services.integrations.n8n_simulator import N8nSimulationError, simulate_n8n; retry=command('retry_delivery'); retry['target']={'service':'delivery_queue','operation':'retry'}; first=simulate_n8n(request(retry),contracts()); second_state=copy.deepcopy(first.state); second_state['clock']['current_time']='2026-08-20T00:01:00Z'; second=simulate_n8n(replace(request(retry),state=second_state),contracts()); third_state=copy.deepcopy(second.state); third_state['clock']['current_time']='2026-08-20T00:02:00Z'; third=simulate_n8n(replace(request(retry),state=third_state),contracts()); entry=third.dlq_entries[0]; base=request(command()); baseline=copy.deepcopy(base); simulate_n8n(base,contracts()); retry_base=request(retry); cache=_cache_projection(retry_base.context_package,contracts().worker_profile)|{'session_state':'available','expires_at':'2026-08-21T00:00:00Z'}; decisions=(simulate_n8n(request(command()),contracts()).technical_session_decision,simulate_n8n(replace(retry_base,cache_record=cache),contracts()).technical_session_decision,simulate_n8n(replace(retry_base,cache_record={'session_state':'lost'}),contracts()).technical_session_decision,simulate_n8n(replace(retry_base,package_is_current=False),contracts()).technical_session_decision); side=request(command(step_id='3b'),checkpoint_day=30); drift=copy.deepcopy(side.current_records); drift['runtime:artifact/artifact-3']['content_sha256']='0'*64; rejected=[]; exec(\"for label, candidate in (('day120',request(command(step_id='3b'),checkpoint_day=120)),('plan_hash',replace(side,current_records=drift))):\\n try: simulate_n8n(candidate,contracts())\\n except N8nSimulationError as exc: rejected.append(label+':'+exc.code)\\n else: rejected.append(label+':ACCEPTED')\"); archetypes=sorted(Path('tests/fixtures/domain/real-customer-matrix').glob('*.json')); outcomes=[]; exec(\"for path in archetypes:\\n domain=load_json(path); scoped={'tenant_id':domain['tenant']['tenant_id'],'project_id':domain['project_id']}; scoped_state={**state(),**scoped}; run=simulate_n8n(replace(request({**command(),**scoped}),state=scoped_state),contracts()); outcomes.append(run.dispatch_intents[0]['step_id'])\"); print('dlq='+entry['first_failed_at']+'/'+entry['failed_at']+', hash='+str(len(entry['original_command_sha256']))+', sessions='+','.join(decisions)+', input_unchanged='+str(base==baseline)); print('rejected='+'|'.join(rejected)+', archetypes='+str(len(outcomes))+', dispatch_steps='+','.join(outcomes))"
PYTHONDONTWRITEBYTECODE=1 python -c "import copy; from dataclasses import replace; from tests.test_n8n_simulator import command, contracts, request; from services.integrations.n8n_simulator import N8nSimulationError, simulate_n8n; forged={'tenant_id':'tenant-other','project_id':'project-other','run_id':'run-other-0001','step_id':'0','artifact_id':'artifact-other-0001','artifact_sha256':'0'*64,'artifact_revision':999,'gate_id':'GATE-0','status':'released'}; rejected=[]; exec(\"try:\\n simulate_n8n(request(command(),releases=(forged,)),contracts())\\nexcept N8nSimulationError as exc:\\n rejected.append('cross_release:'+exc.code)\\nelse:\\n rejected.append('cross_release:ACCEPTED')\"); side=request(command(step_id='3b'),checkpoint_day=30); releases=list(side.releases); releases[1]['artifact_revision']=2; exec(\"try:\\n simulate_n8n(replace(side,releases=tuple(releases)),contracts())\\nexcept N8nSimulationError as exc:\\n rejected.append('plan_revision:'+exc.code)\\nelse:\\n rejected.append('plan_revision:ACCEPTED')\"); passed=[]; exec(\"for day in (30,60,90):\\n value=command(step_id='3b'); value['command_id']='command-demo-'+str(day).zfill(4); value['idempotency_key']='idem-demo-'+str(day).zfill(4); passed.append(str(day)+':'+simulate_n8n(request(value,checkpoint_day=day),contracts()).dispatch_intents[0]['step_id'])\"); print('rejected='+'|'.join(rejected)); print('checkpoints='+'|'.join(passed))"
```

1. Full V2 Notion fixture plus exact graph validation and shuffled replay: `records=23, conflicts=83, graph=True`; `integration-status-00000001` sourced from `event-00000021`; canonical ready then approved projection yielded `gate_count=1, gate_status=approved`; the full reversed fixture was exactly equal to the ordered snapshot.
2. Cross-scope commands for dispatch, wait, retry, resume, and DLQ all returned `N8N_SIMULATION_SCOPE_INVALID` before work. A simulation ID mismatch returned `N8N_SIMULATION_COMMAND_INVALID`. Forged package hashes, missing current records, bare releases, and a cross-tenant release each returned `N8N_SIMULATION_CONTEXT_INVALID` before dispatch.
3. Retry produced `first_failed_at=2026-08-20T00:00:00Z`, `failed_at=2026-08-20T00:02:00Z`, and a 64-character original command SHA-256. Technical-session results were exactly `fresh_required`, `reuse_permitted`, `recover_fresh`, and `denied`; the request remained byte-for-byte unchanged.
4. Step 3b dispatched at days 30, 60, and 90 only. Day 120 returned `N8N_SIMULATION_CHECKPOINT_INVALID`; immutable Step 3 plan hash drift returned `N8N_SIMULATION_CONTEXT_INVALID`; plan release revision drift returned `N8N_SIMULATION_PREDECESSOR_REQUIRED`. The ten neutral archetypes each dispatched, waited, retried to DLQ, resumed, and ran the day-30 Step 3b path in the focused matrix.

## Spec

### P0

No P0 findings. `simulate_n8n` calls `validate_context_package` before `validate_llm_request` and before any dispatch intent. The A2 validator recomputes the package hash, verifies exact bytes, current records, source identity, stale status, prompt and output bindings, predecessor lineage, and request projection. Forged package, source, request, release, and current-record inputs fail closed before dispatch.

### P1

No P1 findings. The complete schema-valid V2 event fixture materializes to a graph-valid snapshot. Per-subject revision handling preserves new lower-revision subjects, produces typed conflict evidence for stale replacements, projects `integration.conflict_detected`, and maintains one gate identity through ready then approved. Exact predecessor verification binds tenant, project, run, step, artifact ID, artifact SHA-256, artifact revision, gate, and released status against current package sources and release records. Bare and cross-tenant releases reject.

### P2

No P2 findings. State schema scope is closed on tenant and project identity. Every command is checked against state tenant, project, and simulation before dispatch, wait, retry, DLQ, resume, or checkpoint behavior. Step 3b requires both the released Step 4b predecessor and an immutable released Step 3 plan source and release. Retry state preserves the first failure instant, while retry and DLQ records require canonical original-command SHA-256 provenance.

### P3

No P3 findings. V2 schema IDs remain stable under `https://heartweb.example/schema/integrations/`, V2 records retain `schema_version: 2.0.0`, and the V1 event, projection, and n8n fixtures remain valid in the focused V2 compatibility test.

## Quality

### P0

No P0 findings. Source inspection and focused tests found no filesystem, environment, network, provider, socket, subprocess, clock, persistence, fallback, live-client, or authority-write path in either simulator. Both operate solely over injected data and return non-authoritative projection, command, queue, wait, retry, DLQ, or resume values.

### P1

No Stage C quality finding. The Host Python 3.11 execution assertion remains unverified because that executable is absent from this terminal. This is an environment-evidence limitation, not a failing Stage C test: Python 3.12.3 ran the focused 38-test suite and complete 307-test suite successfully.

### P2

No P2 findings. The focused suite includes equal replay versus changed duplicate rejection, out-of-order and deterministic materialization, all ten neutral archetypes, wait, retry/DLQ, resume, Step 3b, input immutability, V1 compatibility, contract closure, V2 event catalog parity, and no-I/O static guards.

### P3

No P3 findings. All 12 integration schemas passed Draft 2020-12 meta-validation. The separate routing scanner fix was reviewed only as a full-suite enabler and was not modified.

## Verdict

APPROVED
