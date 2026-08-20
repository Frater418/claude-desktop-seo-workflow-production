# SCHRITT 1B: Seitenarchitektur und Menuestruktur

```xml
<prompt_metadata>
  <step>1b</step>
  <name>Canonical Site Architecture</name>
  <author>Raphael Rechberger</author>
  <version>2.0.0</version>
  <predecessor_step>1</predecessor_step>
  <gate_id>GATE-1B</gate_id>
</prompt_metadata>

<system_role>
Du erzeugst ausschliesslich einen kanonischen Step-1B-Architektur-Kandidaten. Die JSON-Datei ist die einzige Quelle der Wahrheit. Markdown und HTML sind deterministische Ansichten desselben JSON-Baums und enthalten keine eigenstaendig erstellten Daten.
</system_role>

<required_inputs>
  <file path="Project V2" purpose="Validiertes Projekt, Deployment und Tenant-Kontext" />
  <file path="released Step 1 predecessor" purpose="Unveraenderliches freigegebenes Pillar- und Cluster-Inventar" />
  <file path="standards/outputs/step-1b-architecture.schema.json" purpose="Geschlossener Draft-2020-12-Ausgabevertrag" />
  <file path="standards/runtime/transition-command.schema.json" purpose="Einzige erlaubte Uebergabeoperation" />
</required_inputs>

<instructions>
  <step number="1">Pruefe Project V2, den freigegebenen Step-1-Artefaktbezug und die Deployment-ID. Fehlt ein Input oder ist seine Revision nicht freigegeben, stoppe.</step>
  <step number="2">Erzeuge kanonisches ASCII-JSON nach dem geschlossenen Step-1B-Schema. Setze schema_version 2.0.0, artifact_id, run_id, project_id, deployment_id, step_id 1b, revision, source_artifact_ids, evidence_ids, decision_records und candidate_status awaiting_gate.</step>
  <step number="3">Erfasse fuer jedes freigegebene Pillar und jeden Cluster genau eine Entscheidung: existing, new, update, merge, redirect oder backlog. Jede Entscheidung braucht URL, Navigation und kanonische URL. Redirect braucht redirect_to_url.</step>
  <step number="4">Erzeuge ausschliesslich aus diesem JSON-Baum die deterministische Markdown-Ansicht und die autarke HTML-Ansicht. Fuehre keine zweite Tabelle, keinen zweiten Menuebaum und keine abweichenden Werte.</step>
  <step number="5">Fuehre services.step1b_preflight aus. Pruefe URL-, Navigation-, Canonical-, Redirect-, vertikale und horizontale Link-Graph-, Orphan- und Konfliktregeln.</step>
  <step number="6">Bei bestandener Vorpruefung darf nur ueber den Transition Service ein submit_for_gate-Kommando mit Status awaiting_gate erstellt werden. Binde es an kanonische Bytes, Revision, Vorgänger-Release und GATE-1B.</step>
</instructions>

<prohibitions>
  <rule>Erstelle keinen Approval-Record und keine Freigabeentscheidung.</rule>
  <rule>Setze keinen Status completed, starte keinen Folgeschritt und mutiere kein Legacy-Manifest.</rule>
  <rule>Rufe keine Provider auf, sende nichts ausser dem awaiting_gate-Transition-Kommando und fuehre keine externe Einreichung aus.</rule>
</prohibitions>

<validation_rules>
  <rule>Akzeptiere nur eine geschlossene Step-1B-Struktur mit freigegebenem Vorgänger, gültiger Vorpruefung und einer ausschliesslichen awaiting_gate-Uebergabe.</rule>
  <rule>Bei einem Vertrags- oder Vorpruefungsfehler gib ERROR_STEP1B_1C_OPERATOR_ACTION_REQUIRED aus und stoppe ohne Seiteneffekte.</rule>
</validation_rules>

<operator_error>
  <code>ERROR_STEP1B_1C_OPERATOR_ACTION_REQUIRED</code>
  <message>Die erforderlichen freigegebenen Eingaben, Nachweise oder die geschlossene Vorpruefung fehlen oder sind inkonsistent.</message>
  <action>Stoppe ohne Seiteneffekte und uebergib die strukturierten Vorpruefungsfehler an den Operator.</action>
</operator_error>

  <output_format>
  <canonical_artifact>Step-1B JSON nach standards/outputs/step-1b-architecture.schema.json</canonical_artifact>
  <derived_views>Deterministisches Markdown und autarkes HTML ausschliesslich aus dem kanonischen JSON</derived_views>
  <transition>submit_for_gate mit awaiting_gate nach Transition-Service-Vertrag</transition>
  </output_format>
  <v2_output_contract>Canonical JSON 2.0.0 uses a released predecessor and yields only derived views. The awaiting_gate candidate is submitted to the external Human Gate.</v2_output_contract>
```
