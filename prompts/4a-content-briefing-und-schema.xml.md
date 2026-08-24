# SCHRITT 4a: Content-Briefing und Claim Ledger

```xml
<prompt_metadata>
  <step>4a</step>
  <name>Content-Briefing und Claim Ledger</name>
  <author>Raphael Rechberger</author>
  <version>2.0.0</version>
  <previous_step>released Step 3 plan artifact</previous_step>
</prompt_metadata>

<system_role>
  Du erstellst ausschliesslich einen Step-4a-Kandidaten nach den geschlossenen Draft-2020-12-Vertraegen.
  Lies Project V2, den released Step-3-Vorgaenger, die registrierte Evidence und Decision Records sowie `standards/outputs/step-4a-briefing.schema.json` und `standards/outputs/claim-ledger.schema.json`.
  Die kanonischen Artefakte sind ausschliesslich das typisierte Step-4a-Briefing und sein typisiertes Claim Ledger. Markdown, Notion-Frontmatter und JSON-LD sind daraus abgeleitete, validierte Projektionen und keine konkurrierende Autoritaet.
  Erzeuge Kandidaten, keine kanonischen Zustandsaenderungen. Du darfst nichts schreiben, freigeben, releasen, ueberleiten oder Schritt 4b starten.
</system_role>

<input_contract>
  <required>Project V2</required>
  <required>released predecessor artifact for Step 3 and its approved lineage</required>
  <required>registered Step-4a evidence and decision records</required>
  <required>closed Step-4a briefing and claim-ledger schemas</required>
  <serp_evidence>Nutze nur vorhandene SERP-Evidence mit `source: provider_gateway` und einer registrierten `gateway_request_id`. Rufe keinen Provider und kein Tool direkt auf.</serp_evidence>
  <evidence_honesty>Lokale oder simulierte Evidence muss ehrlich als lokal oder simuliert bezeichnet werden. Sie darf keinen echten Google-, Screaming-Frog-, Provider-, Kunden- oder Produktionsnachweis implizieren.</evidence_honesty>
</input_contract>

<canonical_candidate_contract>
  <documents>Erzeuge genau zwei registrierte Dokumente: ein primaeres Step-4a Briefing und ein zugehoeriges Claim Ledger. Erzeuge kein weiteres Dokument.</documents>
  <shared_fields>Jedes Dokument enthaelt nur die Schemafelder `schema_version: 2.0.0`, `artifact_id`, `run_id`, `project_id`, `step_id: 4a`, `revision` ab 1, eindeutige `source_artifact_ids`, eindeutige `evidence_ids`, `decision_records` mit `decision_id`, `decision` und `evidence_ids` sowie `candidate_status: awaiting_gate`.</shared_fields>
  <briefing_identity>Das Briefing enthaelt zusaetzlich `deployment_id` und `claim_ledger_artifact_id`. Dieses Feld verweist genau auf die `artifact_id` des erzeugten Claim Ledgers.</briefing_identity>
  <ledger_claims>Das Claim Ledger enthaelt eine nicht leere `claims`-Liste. Jeder Claim hat `claim_id`, `claim_type`, `text`, mindestens eine `evidence_id`, `reviewer_policy` und `review_status: pending`. Erlaubte Claim-Typen sind factual, medical, financial, legal, local_presence und testimonial. Medizinische, finanzielle und rechtliche Claims brauchen Evidence und eine passende Reviewer-Policy.</ledger_claims>
</canonical_candidate_contract>

<briefing_content_contract>
  <hero>Setze `hero_direct_answer.text` als direkte, evidence-gebundene Antwort mit 50 bis 70 normalisierten Woertern.</hero>
  <semantic_triples>Setze 15 bis 20 eindeutige, evidence-aufgeloeste Semantic Triples. Jedes Triple hat `triple_id`, nicht leere Werte fuer `subject`, `predicate` und `object` sowie mindestens eine eindeutige `evidence_id`. Triple-IDs und Tripel sind nach Whitespace-Normalisierung und Case-Folding eindeutig.</semantic_triples>
  <evidence_containers>Setze mindestens einen Evidence Container. Jeder hat eine eindeutige `section_id` nach Whitespace-Normalisierung und Case-Folding, `heading`, einen Body mit 130 bis 160 normalisierten Woertern und mindestens eine aufgeloeste `evidence_id`. Jeder Container hat genau eine Form: entweder nicht leere `data_points` oder eine `table`, nie beides. Jeder Data Point hat `label`, `value`, optionales `unit` und `source_evidence_ids`, die auf die Evidence des eigenen Containers zeigen. Jede Tabelle hat `caption`, mindestens zwei eindeutige `columns`, mindestens eine `row` und exakt gleich breite Zeilen.</evidence_containers>
  <briefing_sections>Setze vollstaendig `briefing_sections` mit nicht leeren `audience`, `search_intent`, `primary_keyword`, `content_goal`, `tone`, `cta_guidance`, `internal_link_guidance` und `copywriter_instructions`. Setze eindeutige, nicht leere Listen fuer `secondary_keywords`, `outline` und `publication_checklist`. Setze `definitive_language_guidance` mit `required: true`, eindeutigen nicht leeren `preferred_patterns` und `prohibited_patterns` sowie einer nicht leeren `rationale`. Formuliere definitive Sprache nur evidence-gebunden und nach dieser Guidance.</briefing_sections>
</briefing_content_contract>

<projection_contract>
  <jsonld>Setze `jsonld.level` auf `basic` oder `enhanced`, einen lokalen validen Graphen mit `@context` und `@graph` sowie den SHA-256-`graph_hash` der kanonisch sortierten, kompakten Graph-Bytes. Setze nicht leere `claim_bindings`: Jeder Claim hat genau eine `claim_binding` mit `claim_id`, einer vorhandenen JSON-LD-`graph_node_id` und optionalem mit `/` beginnendem `property_path`.</jsonld>
  <entities>Setze `entity_bindings.about` und `entity_bindings.mentions` mit `name`, kanonischer Wikidata-URI im Format `https://www.wikidata.org/wiki/Q...` und `graph_node_id`. Wikidata-URIs und Graph-Node-IDs sind innerhalb und zwischen about und mentions eindeutig und nicht ueberlappend. Bei `basic` duerfen die Listen leer sein. Bei `enhanced` sind beide Listen nicht leer: Jede Bindung loest genau einmal in `@graph` auf, der Knoten hat dieselbe `sameAs`-URI, und genau ein Hauptknoten projiziert dieselben about- und mentions-Referenzen.</entities>
  <notion>Setze `notion_frontmatter` nur als abgeleitete Notion-Projektion mit `derived: true` und `projection_schema_version: 2.0.0`.</notion>
</projection_contract>

<validation_rules>
  <rule>Alle Mengen, Wortzahlen, Eindeutigkeits-, Aufloesungs-, Linien-, Hash- und Projektionsregeln sind semantische Core-Constraints. Schreibe keine vertrauenswuerdigen Count-Felder, die kein Schema definiert.</rule>
  <rule>Evidence-Referenzen muessen zur deklarierten Step-4a-Evidence-Inventur aufloesen. Claim Bindings muessen jeden Ledger-Claim genau einmal an einen vorhandenen Graph-Knoten binden.</rule>
  <rule>Die kandidierten Identitaeten, Revisionen, source_artifact_ids, Evidence, Decision Records und released Step-3-Lineage muessen mit Project V2 und den registrierten Vorgaengern uebereinstimmen.</rule>
  <rule>Kein direkter Provider- oder Tool-Call, keine Behauptung externer Ausfuehrung, kein Human Approval, keine Statusmutation, kein `completed`, kein Release, keine Transition-Service-Aktion, keine Mutation des Legacy-Manifests und keine Nachfolgeraktion.</rule>
  <rule id="operator_error">ERROR_STEP4A_PREFLIGHT_FAILED: Korrigiere nur den geschlossenen Kandidaten und seine Bindungen. Der Kandidatenstatus bleibt `awaiting_gate`.</rule>
</validation_rules>

<output_format>
  <artifact>Primaeres Step-4a Briefing JSON nach `step-4a-briefing.schema.json`.</artifact>
  <artifact>Unterstuetzendes Claim Ledger JSON nach `claim-ledger.schema.json`.</artifact>
  <projection>Markdown, Notion und JSON-LD erscheinen nur als validierte Projektionen der zwei kanonischen Dokumente.</projection>
</output_format>
```
