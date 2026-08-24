type Step4ArtifactPayloadFieldsProps = {
  readonly disabled: boolean
  readonly supportingDocument: string
  readonly bundle: string
  readonly gateContext: string
  readonly setSupportingDocument: (value: string) => void
  readonly setBundle: (value: string) => void
  readonly setGateContext: (value: string) => void
}

export function Step4ArtifactPayloadFields({ disabled, supportingDocument, bundle, gateContext, setSupportingDocument, setBundle, setGateContext }: Step4ArtifactPayloadFieldsProps): JSX.Element {
  return <><label>Unterstuetzendes registriertes Dokument<textarea aria-label="Unterstuetzendes registriertes Dokument" value={supportingDocument} onChange={(event) => setSupportingDocument(event.currentTarget.value)} disabled={disabled} /></label><label>Operatives Preflight-Bundle<textarea aria-label="Operatives Preflight-Bundle" value={bundle} onChange={(event) => setBundle(event.currentTarget.value)} disabled={disabled} /></label><label>Lokaler GateContext und Nachweise<textarea aria-label="Lokaler GateContext und Nachweise" value={gateContext} onChange={(event) => setGateContext(event.currentTarget.value)} disabled={disabled} /></label></>
}
