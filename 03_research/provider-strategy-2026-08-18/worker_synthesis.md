# Provider-Strategie: AgentSEO vs. DataForSEO

Stand: 18.08.2026
Autor: Raphael Rechberger

## Evidenzbasis und Grenzen

Die Recherche startete mit `exa_raw.json`. Die ergänzende Webrecherche wurde ausschließlich über Firecrawl für offizielle Seiten von `agentseo.dev`, `dataforseo.com` und `docs.dataforseo.com` ausgeführt. Die vollständigen Firecrawl-Antworten liegen in `firecrawl_raw.json`.

Die Preisangaben sind die zum Abrufzeitpunkt sichtbaren offiziellen Angaben. AgentSEO weist Credits pro Plan aus, aber keine in den geprüften Seiten vollständig aufgelöste Credit-Tabelle je Endpoint. Deshalb ist kein belastbarer 1:1-Preis pro AgentSEO-Request ableitbar. DataForSEO weist produktbezogene Stückpreise aus. Nicht belegte Kostenschätzungen werden vermieden.

## Kernbefunde

- **AgentSEO-Preismodell:** Hobby 0 USD/Monat mit einmalig 100 Live-Credits, Starter 9 USD/Monat mit 2.000 Credits, Pro 49 USD/Monat mit 10.000 Credits und Agency 149 USD/Monat mit 35.000 Credits. Die Pläne haben harte Limits, kein Overages-Modell und liefern laut Anbieter normalisiertes JSON und Markdown statt Rohdatenbereinigung.[1]
- **DataForSEO-Kosten:** Die allgemeine Preis-Seite nennt Pay-as-you-go und eine Mindestzahlung von 50 USD.[7] Google Organic SERP kostet laut Produktseite 0,0006 USD je SERP mit 10 Ergebnissen in der Standard Queue, 0,0012 USD in der Priority Queue und 0,002 USD im Live-Modus. Die angegebenen mittleren Laufzeiten sind ungefähr 5 Minuten, bis zu 1 Minute beziehungsweise bis zu 6 Sekunden.[8]
- **Keyword-Daten:** DataForSEO beschreibt Google Ads, Bing Ads und Trends als Pay-as-you-go APIs. Die Keyword-API-Seite nennt ab 0,05 USD je 1.000 Keywords und für Google Ads 0,06 USD je Task in der Standard Queue beziehungsweise 0,09 USD im Live-Modus, jeweils mit bis zu 1.000 Keywords je Task.[10]
- **DataForSEO Labs:** Die offizielle Labs-Preisseite nennt unter anderem 0,00012 USD je Keyword oder Item für viele Endpoints, 0,00012 USD je historische SERP und 0,012 USD je Search-Intent-Task. Clickstream-Anreicherung verdoppelt laut Seite den Requestpreis.[9]
- **Datenkontrolle:** DataForSEO liefert direkte strukturierte Providerdaten, mehrere Funktionen und eine gemeinsame JSON-Taxonomie über den API-Stack.[11][14][15] AgentSEO abstrahiert diese Ebene zugunsten kompakter, agentenorientierter Antworten und ergänzt `agent_workflow`, Evidenz, Limitationen, empfohlene Aktionen und teilweise Markdown-Zusammenfassungen.[2]
- **Geo-Targeting:** DataForSEO dokumentiert SERP-Ergebnisse abhängig von Suchmaschine, Sprache und Ort sowie Geräte- und Betriebssystemparameter. Die offizielle SERP-Produktbeschreibung nennt regionale, distriktsbezogene und GPS-basierte Abfragen.[14] AgentSEO dokumentiert `location` plus optional `location_code`, wobei `location_code` gewinnt, und `language` als ISO-Code.[2][3] Im Projekt ist zusätzlich der bestätigte AgentSEO-Defekt zu beachten: `location_code` 2276 liefert deutsche Daten, aber `country_iso_code` US; der Hosted-MCP-SERP-Vertrag lässt `location_code` aus, REST akzeptiert es. AgentSEO darf für Geo-kritische Produktionsdaten daher nicht ohne nachgelagerte Geo-Prüfung eingesetzt werden.
- **Output-Mehrwert:** AgentSEO publiziert einen kleinen, ausdrücklich begrenzten Benchmark mit drei Queries: 88,6 Prozent weniger UTF-8-Bytes im normalisierten Core-JSON und 72,6 Prozent weniger im angereicherten Output. Der Anbieter bezeichnet dies als richtungsweisende Stichprobe, nicht als allgemeine Latenz-, Token- oder Kosten-Garantie.[4] Das ist ein belegter Parsing- und Übergabemehrwert, aber kein Beweis für bessere Rohdatenqualität.
- **n8n:** AgentSEO beschreibt einen HTTP-Request-Schritt, einen Poll-Schritt und die Weiterleitung nach Slack, Notion, Sheets oder CMS. Die Seite positioniert dies ausdrücklich als unterstützten HTTP-Workflow, nicht als nativen n8n-Node.[5] DataForSEO bietet eine offizielle n8n-Integrationsseite und verweist auf einen n8n-Node.[12] Die offizielle MCP-n8n-Anleitung beschreibt außerdem lokalen Start per `npx dataforseo-mcp-server http`, n8n `MCP Client Tool` sowie einen Remote-Endpunkt.[13]
- **Lock-in:** AgentSEO bindet an Credits, eigene normalisierte Schemas, Agent-Workflow-Blöcke und seine REST/MCP-Oberfläche. DataForSEO bindet an dessen API- und Taxonomie-Verträge, lässt aber die Rohantwort und die Syntheselogik im eigenen System. Für das Projekt ist DataForSEO als Rohdatenanker und Hermes als eigene Normalisierung die reversiblere Schicht. AgentSEO ist ein optionaler Beschleuniger für agentische Mehrwertschritte.

## Entscheidung je Workflow-Schritt

| Workflow-Schritt | Empfehlung | Begründung und Kontrollpunkt |
|---|---|---|
| 1. Markt, Sprache, Ort und Device festlegen | **Hermes-eigene Synthese** | Manifest, `country`, `location_code` und `language` sind die autoritative Eingabe. Provider dürfen diese Werte nicht stillschweigend ersetzen. Bei AgentSEO zusätzlich Rückgabe-Geo gegen Sollwerte prüfen. |
| 2. Keyword-Ideen, Suchvolumen, CPC und Wettbewerb | **DataForSEO direkt** | Direkter Zugriff auf Google Ads, Bing Ads, Trends und Labs mit publizierten Stückpreisen sowie historischen und Clickstream-bezogenen Optionen.[9][10][15] Hermes behält Rohpayload und kann die Auswahl deterministisch filtern. |
| 3. SERP-Snapshot und Ranking-Evidenz | **DataForSEO direkt** | Die Preise, Queue-Modi, Funktionen, Geräte- und Geo-Parameter sind explizit dokumentiert.[8][14] Für dieses Projekt ist die direkte REST-Kontrolle wichtiger als AgentSEO-Komfort. Standard Queue ist für nicht zeitkritische Bulk-Abfragen preislich und operativ naheliegend; Live nur bei begründetem Echtzeitbedarf. |
| 4. Geo-kritische lokale SERP oder Local Audit | **A/B-Test** | AgentSEO bietet kompakte Workflows und `location_code`, ist aber wegen des bestätigten Codes- und Länderdefekts nicht allein vertrauenswürdig. Gleiche Keywords, Orte, Sprache und Device gegen DataForSEO ausführen und `country_iso_code`, Resultate und Fehlerquote vergleichen. |
| 5. Rohdaten speichern, normalisieren und Provider-Adapter | **Hermes-eigene Synthese** | Raw-first mit unveränderten Providerantworten, danach ein eigenes kanonisches Schema. Dadurch bleiben Providerwechsel, Reproduzierbarkeit und Geo-Validierung möglich. AgentSEOs Benchmark belegt kleinere Payloads, nicht automatisch bessere Daten.[4] |
| 6. Content Gap, Opportunity-Findung, Refresh- oder SERP-Brief | **AgentSEO** | AgentSEO bündelt solche Workflows und liefert zusätzlich `agent_workflow`, Aktionen, Evidenz, Limitationen und nächste Calls.[2] Die Ausgabe muss als Vorschlag behandelt und gegen Hermes-Rohdaten sowie Regeln geprüft werden. Credit-Verbrauch pro Endpoint vor Produktion messen, da die Pricing-Seite keine vollständige Endpoint-Creditmatrix liefert.[1] |
| 7. Deterministische 120-Tage-Planung und Priorisierung | **Hermes-eigene Synthese** | Agentische Empfehlungen werden nicht zur Autorität. Hermes wendet die Projektregeln, Mengenregeln, Manifest-Schema und Kapazitätslogik auf verifizierte Daten an. |
| 8. Wiederkehrender n8n-Workflow | **A/B-Test** | DataForSEO hat n8n-Integration und Node/MCP-Pfade.[12][13] AgentSEO hat einen dokumentierten HTTP-plus-Poll-Weg, aber keinen nativen Node.[5] Zuerst dieselbe Teilstrecke mit identischen Inputs messen: Setup-Aufwand, Polling-Fehler, Geo-Treue, Payload-Nacharbeit und Kosten pro erfolgreichem Ergebnis. |
| 9. Endredaktion, Briefing und Notion-Übergabe | **Hermes-eigene Synthese** | Provideroutput ist Evidenz oder Vorschlag. Hermes erzeugt das autoritative Dokument, prüft Quellen, Schema, Mengen und Projektformatierung. |

## Praktische Architekturentscheidung

1. DataForSEO direkt als Rohdaten- und Geo-Referenzpfad für Keyword-, SERP- und Labs-Schritte.
2. Hermes speichert jede Rohantwort unverändert, versieht sie mit Provider, Modus, Ort, Sprache, Device und Abrufzeit und erzeugt ein eigenes kanonisches Schema.
3. AgentSEO nur dort zuschalten, wo sein agentischer Output einen klaren Mehrwert gegenüber Hermes-eigener Synthese liefert: Content Gap, Opportunity, Refresh-Brief und vergleichbare Entscheidungsvorlagen.
4. Für Geo-kritische AgentSEO-Aufrufe zwingend A/B gegen DataForSEO und Rückgabeprüfung durchführen. Der bekannte `location_code`-Defekt ist ein Produktionsblocker für ungeprüfte Nutzung.
5. In n8n zuerst DataForSEO direkt und AgentSEO HTTP-plus-Poll als getrennte Adapter abbilden. Keine Providerantwort ungeprüft in Notion oder CMS schreiben.

## Offene Punkte für einen echten A/B-Test

- AgentSEO-Creditverbrauch je konkret verwendetem Endpoint und Plan erfassen.
- Gleiche Keyword-, SERP-, Location-, Language- und Device-Matrix über beide Anbieter ausführen.
- Für jede Antwort Rohpayload, normalisierte Nutzfelder, HTTP-Zeit, Pollingzeit, Fehler, Geo-Konsistenz und Nacharbeitszeit speichern.
- AgentSEO-Benchmark nicht verallgemeinern: Er umfasst drei Queries und misst UTF-8-Bytes, nicht Datenqualität oder End-to-End-Kosten.[4]

## Quellen

[1] https://www.agentseo.dev/pricing
[2] https://www.agentseo.dev/docs/api-reference
[3] https://www.agentseo.dev/docs/quickstart
[4] https://www.agentseo.dev/research/payload-benchmark
[5] https://www.agentseo.dev/integrations/n8n
[6] https://www.agentseo.dev/docs/authentication
[7] https://dataforseo.com/pricing
[8] https://dataforseo.com/pricing/google-serp/google-organic-serp-api
[9] https://dataforseo.com/pricing/dataforseo-labs/dataforseo-google-api
[10] https://dataforseo.com/apis/keyword-data-api
[11] https://dataforseo.com/solutions/seo
[12] https://dataforseo.com/n8n-integration
[13] https://dataforseo.com/help-center/connecting-dataforseo-mcp-server-to-your-n8n-workflows
[14] https://docs.dataforseo.com/v3/serp-overview
[15] https://docs.dataforseo.com/v3/dataforseo_labs/overview.md
