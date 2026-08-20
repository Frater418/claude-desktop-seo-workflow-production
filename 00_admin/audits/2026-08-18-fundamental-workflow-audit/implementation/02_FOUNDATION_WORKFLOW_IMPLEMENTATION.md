# Foundation Workflow Implementation

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Paket: Foundation Gate A, Package B Workflow und Traceability

## Korrigierte Artefakte

- `standards/workflow/workflow-graph.schema.json` und `standards/workflow/workflow-graph.json`: der einzige Initialpfad bleibt `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`.
- Schritt 3b bleibt ein wiederholbarer Post-Publication-Sideflow an Tag 30, 60 und 90 und ist keine Initialkante.
- `standards/runtime/transition-command.schema.json`, `run-envelope.schema.json` und `quality-gate-run.schema.json`: Runtime IDs verwenden hyphenierte Prefixe. Quality-Gate-Run-IDs verwenden `qgr-`.
- `tests/fixtures/workflow/` und die drei Contracttests verwenden dieselbe ID-Konvention und pruefen die unzulaessige Initialtransition `3 -> 3b` weiter.

## Testnachweis

Ausgefuehrt:

`python3 -m unittest tests.contracts.test_real_customer_domain_fixtures tests.contracts.test_workflow_graph tests.contracts.test_transition_contract`

Ergebnis: 16 Tests bestanden.

## Grenzen

Die Schemas und Tests sind Foundation Contracts. Persistente Runtime, RBAC und externe Orchestrierung sind nicht Teil dieses Packages.
