# Host-Verified Git Baseline for OMO Audit

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Quelle: Windows Host Git

## Branch

`master` entspricht `origin/master` bei Commit `5e78679`.

## Bereits vor dem fundamentalen Audit vorhandene tracked Aenderungen

- `.gitignore`
- `mcp/tools/capacity_matrix_solver.py`
- `mcp/tools/validate_schema_jsonld.py`
- `prompts/0-kickoff.xml.md`
- `standards/manifest.schema.json`
- `tests/fixtures/sample_manifest.json`
- `tests/run_acceptance_tests.py`

## Bereits vor dem fundamentalen Audit vorhandene untracked Kandidatenbereiche

- `.hermes/`
- `03_research/provider-strategy-2026-08-18/`
- `services/`
- `tests/fixtures/sample_briefing.md`
- `tests/fixtures/sample_landingpage.html`
- `tests/test_agentseo_location_guard.py`
- `tests/test_prompt0_contract.py`

## Durch den Audit neu hinzugefuegt

- `00_admin/audits/2026-08-18-fundamental-workflow-audit/`

## Verbindliche OMO-Regel

Git-Ausgaben innerhalb des Linux-Containers zeigen auf dem Windows-Mount grossflaechige falsche Aenderungen durch Line-Ending-Interpretation. Diese Container-Git-Ausgaben sind keine gueltige Audit-Evidenz.

OMO darf fuer diesen Audit keine `git status`, `git diff`, `git diff --check`, `git ls-files` oder vergleichbare Repository-Diff-Befehle verwenden. Massgeblich ist ausschliesslich diese Host-Baseline. Der Audit bewertet Dateiinhalt und Funktionsverhalten, nicht Container-Git-Metadaten.
