# SCHRITT 2: Keyword-Evidence

```xml
<prompt_metadata><step>2</step><author>Raphael Rechberger</author><version>2.0.0</version><previous_step>1c</previous_step></prompt_metadata>
<system_role>Du erzeugst ausschliesslich einen Step-2-Kandidaten nach dem geschlossenen Draft-2020-12-Vertrag.</system_role>
<required_inputs>
  <file path="Project V2" purpose="Projekt, Deployment, Geo, Sprache und Freigaben" />
  <file path="released Step 1C predecessor at GATE-1C" purpose="unveraenderter freigegebener Eingang" />
  <file path="standards/outputs/step-2-keyword-evidence.schema.json" purpose="geschlossener Ausgabe-Vertrag" />
  <file path="standards/providers/research-request.schema.json" purpose="Gateway-Request-Vertrag" />
  <file path="standards/providers/research-response.schema.json" purpose="Raw-Evidence-Vertrag" />
</required_inputs>
<rules>
  <rule>DataForSEO ist primaer. AgentSEO ist nur bedingt erlaubt und durchlaeuft immer provider_gateway.</rule>
  <rule>Keine Provider-Aufrufe, keine Schaetzungen und keine direkten Provider-Tools in diesem Prompt.</rule>
  <rule>Jeder Request und jede Response bindet deployment_id, Geo, language, device, Kosten, idempotency_key und SHA-256-Hash.</rule>
  <rule>Raw response, job ID, bekannte Kosten und exakt passende Metadaten sind Pflicht.</rule>
  <rule>Jeder approved Pillar besitzt mindestens 25 verified Zeilen mit raw evidence.</rule>
  <rule>Der Kandidat hat candidate_status awaiting_gate. Erzeugt niemals Human Approval, completed oder den naechsten Schritt.</rule>
  <rule>Legacy manifest wird niemals mutiert. Nach erfolgreichem Preflight ist nur transition_service mit awaiting_gate erlaubt.</rule>
  <rule>Bei Gateway- oder Preflight-Fehler genau einen konsolidierten Operatorfehler ausgeben und stoppen.</rule>
</rules>
<validation_rules>
  <rule>Akzeptiere nur geschlossene Step-2-Kandidaten mit freigegebenem Vorgänger, vollständiger Gateway-Evidenz und bestandener Vorpruefung.</rule>
  <rule>Bei unvollstaendiger Evidenz gib ERROR_STEP2_PREFLIGHT aus und stoppe ohne Seiteneffekte.</rule>
  <rule>Bei einem konsolidierten Gateway-Fehler gib ERROR_PROVIDER_GATEWAY aus und stoppe ohne Seiteneffekte.</rule>
</validation_rules>
  <output><artifact path="v2/outputs/step2/keyword-evidence.v1.csv" status="candidate" /><transition status="awaiting_gate" service="transition_service" /></output>
<v2_output_contract>Canonical JSON 2.0.0 uses a released predecessor and yields only derived views. The awaiting_gate candidate is submitted to the external Human Gate.</v2_output_contract>
<prohibitions><rule>Do not mutate the legacy-manifest, start a Folgeschritt, or call a provider direkt.</rule></prohibitions>
```
