# Candidate Classification Before E2E Execution

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Checkpoint: `00_admin/checkpoints/2026-08-19-pre-e2e/`

## Verified

| Component | Evidence | Allowed Use |
|---|---|---|
| AHD Step-0 Legacy Baseline | 4 von 4 Dateien byte-identisch | unveraenderlicher freigegebener Vorgaenger |
| Host Full Suite | Acceptance 7 von 7, Unit und Contract 77 von 77 | Regression Baseline |
| OMO Full Suite | Acceptance 7 von 7, Unit und Contract 77 von 77 | Container Regression Baseline |
| OMO Runtime | healthy, Restart Count 0, jsonschema 4.26.0, model_fallback false | Entwicklungs- und Reviewruntime |
| Domain Contract Fixtures | Bestandteil der gruenen Full Suite | Contract Regression |
| Capacity Solver Strict Tests | Bestandteil der gruenen Full Suite | deterministischer Planungsbaustein |
| JSON-LD Validator Level Tests | Bestandteil der gruenen Full Suite | lokaler Validator, externe Eligibility weiterhin separat |

## Candidate, Independent Review Required

| Component | Current Evidence | Restriction |
|---|---|---|
| `services/transition_service/service.py` | 9 lokale Tests gruen | kein produktiver Statuswriter vor Sprint-1-Spec- und Quality-Review |
| Quality Gate Registry 1.1 | Registry- und Coverage-Tests gruen | Applicability und alle Steps in Sprint 1 erneut pruefen |
| `services/quality_gate_registry/evaluator.py` | 6 Evaluator-Tests gruen | kein produktiver Gateentscheid vor Review |
| Crawl Disposition Policy 1.0 | 13 Crawl- und Policytests gruen | reale AHD-Policy-Disposition noch kanonisch registrieren |
| Step-1 Preflight CLI | Step-1-Suite gruen | AHD-Bundle noch auf Crawl 005, Gate Context und Storage Binding migrieren |
| AHD Step-1 Topic Inventory v1 | Schema und bisheriger Preflight gruen | nicht released, basiert noch auf frueherer Crawl-Lineage |
| Workflow Control Map HTML | lokal renderbar | Designentwurf, keine produktive Operator Console |

## Blocked

| Component | Blocker | Required Resolution |
|---|---|---|
| AHD Crawl 005 Gate | `ERROR_CRAWL_RESOURCE_4XX`, ein fehlendes Bild | technische Reparatur oder expliziter Step-1-Waiver durch Raphael; vor Production weiterhin blockierend |
| AHD GATE-1 | Step-1-Revision mit Crawl-005-Lineage und Human Review fehlt | Sprint 6 |
| Step 1b und Folgeschritte | GATE-1 nicht released und V2-Vertraege fehlen | Sprints 3 und 6 |
| Step 2 Provider Research | Provider Readiness und Kostenfreigabe noch nicht ausgefuehrt | Sprint 8 Readiness Gate |
| Operator Console | kein UI-Projekt vorhanden | Sprint 5 |
| Local Workflow API | nicht vorhanden | Sprint 4 |
| Notion und n8n Liveintegration | absichtlich ausserhalb der lokalen Welle | nur Simulatoren und Vertrage |

## Superseded or Historical Only

| Component | Status | Rule |
|---|---|---|
| AHD Crawl 001 | invalidated | niemals als Evidence verwenden |
| AHD Crawl 002 | superseded | niemals als kanonischen Crawl verwenden |
| AHD Crawl 003 | superseded | falsche Deployment-ID fuer finales Project V2 |
| AHD Crawl 004 | historical | vor Crawl Policy 1.0 erzeugt, nicht fuer neuen Step-1-Release verwenden |
| Legacy Markdown-only Step-1 Contract | superseded by V2 candidate | nicht als Source of Truth verwenden |
| Direkte AgentSEO-Pfade in spaeteren Legacy-Prompts | migration required | keine Providercalls vor Sprint 3 und Provider Gateway Gate |

## Shared-File Ownership

Nur Hermes aktualisiert nach unabhaengiger Verifikation:

- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `standards/quality/quality-gate-registry.json`
- `standards/workflow/workflow-graph.json`
- AHD `v2/runtime/`
- AHD Presentation Matrix
- Sprint Checkpoint Manifests

Implementer-Subagenten duerfen diese Dateien nicht parallel schreiben.
