# Foundation Domain Implementation

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Paket: Foundation Gate A, Domain und Markt

## Korrigierte Artefakte

- `standards/domain/project.schema.json`: geschlossener Project Contract mit Schema-Version, Autor, Zeitstempel, Legacy-Manifest-SHA-256, Zielgruppen, Geschaeftsziel, Brand Tone und Core Services.
- `standards/domain/entity-domain-gbp.schema.json` und `standards/domain/search-deployment.schema.json`: hyphenierte IDs, referenzierbare Brand-, Domain-, Location- und Service-Area-Records sowie vollstaendige Deploymentfelder.
- `standards/domain/market-registry.json`: DE, AT, CH, FR, LU, LK, ID, AE, GB und US mit ausschliesslich `unknown`-Providerstatus und null Provider-Codes ohne Evidenz.
- `tests/fixtures/domain/`: zehn positive Kundenarchetypen und vier negative Fixtures mit den korrigierten Contracts.
- `tests/contracts/test_real_customer_domain_fixtures.py`: prueft Registry-Aufloesung und alle Deploymentreferenzen auf deklarierte Brand-, Domain-, Location- und Service-Area-IDs.

## Testnachweis

Ausgefuehrt:

`python3 -m unittest tests.contracts.test_real_customer_domain_fixtures tests.contracts.test_workflow_graph tests.contracts.test_transition_contract`

Ergebnis: 16 Tests bestanden.

## Begrenzungen

- Provider-Location-Codes bleiben null, bis konkrete Provider-Evidenz vorliegt.
- Dieses Paket aendert keine AHD-Step-0-Baseline.
