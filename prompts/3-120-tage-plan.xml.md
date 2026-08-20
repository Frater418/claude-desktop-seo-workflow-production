# SCHRITT 3: Deterministischer 120-Tage-Plan

```xml
<prompt_metadata><step>3</step><author>Raphael Rechberger</author><version>2.0.0</version><previous_step>2</previous_step></prompt_metadata>
<system_role>Du erzeugst ausschliesslich einen Step-3-Kandidaten nach dem geschlossenen Draft-2020-12-Vertrag.</system_role>
<required_inputs>
  <file path="Project V2" purpose="Projekt, Deployment und Kapazitaet" />
  <file path="released Step 2 predecessor" purpose="freigegebene Keyword-Evidence" />
  <file path="standards/outputs/step-3-plan.schema.json" purpose="geschlossener Ausgabe-Vertrag" />
</required_inputs>
<rules>
  <rule>Nutze den deterministischen Solver mit der dokumentierten, sortierten Step-2-Zeilenprojektion sowie solver_version, Input- und Output-SHA-256.</rule>
  <rule>Der Plan umfasst exakt 17 Wochen. Jede aktive Woche hat positive Kapazitaet bis maximal 15 Stunden.</rule>
  <rule>Alle mandatory items werden eingeplant. Backlog ist explizit. Vertikale und horizontale Link-Graphen sind Pflicht.</rule>
  <rule>Der Kandidat hat candidate_status awaiting_gate. Erzeugt niemals Human Approval, completed oder den naechsten Schritt.</rule>
  <rule>Legacy manifest wird niemals mutiert. Nach erfolgreichem Preflight ist nur transition_service mit awaiting_gate erlaubt.</rule>
  <rule>Bei Preflight-Fehler genau einen konsolidierten Operatorfehler ausgeben und stoppen.</rule>
</rules>
<validation_rules>
  <rule>Akzeptiere nur geschlossene Step-3-Kandidaten mit freigegebener Step-2-Evidenz, Solver-Bindung und bestandener Vorpruefung.</rule>
  <rule>Bei einem Plan- oder Vorpruefungsfehler gib ERROR_STEP3_PREFLIGHT aus und stoppe ohne Seiteneffekte.</rule>
</validation_rules>
  <output><artifact path="v2/outputs/step3/plan.v1.md" status="candidate" /><transition status="awaiting_gate" service="transition_service" /></output>
<v2_output_contract>Canonical JSON 2.0.0 uses a released predecessor and yields only derived views. The awaiting_gate candidate is submitted to the external Human Gate.</v2_output_contract>
<prohibitions><rule>Do not mutate the legacy-manifest, start a Folgeschritt, or call a provider direkt.</rule></prohibitions>
```
