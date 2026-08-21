import { useCallback, useRef, useState } from "react"
import { OperatorApiError } from "../api/client"
import type { ActionConfirmRequest, ActionConfirmResult, ActionIntent, ActionPreview } from "../generated/api-types"

export type AdminActionClient = {
  readonly previewAdminAction: (projectId: string, verb: string, request: ActionIntent, signal: AbortSignal) => Promise<ActionPreview>
  readonly confirmAdminAction: (projectId: string, verb: string, request: ActionConfirmRequest, signal: AbortSignal) => Promise<ActionConfirmResult>
}

export type AdminActionState =
  | { readonly kind: "idle"; readonly notice?: string }
  | { readonly kind: "previewing" }
  | { readonly kind: "blocked"; readonly preview: ActionPreview }
  | { readonly kind: "awaiting-confirmation"; readonly intent: ActionIntent; readonly preview: ActionPreview }
  | { readonly kind: "confirming" }
  | { readonly kind: "reloading" }
  | { readonly kind: "completed"; readonly replay: boolean }
  | { readonly kind: "failed"; readonly message: string }

type AdminActionConfig = { readonly client: AdminActionClient; readonly reload: () => Promise<void> }

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Die Aktion konnte nicht verarbeitet werden."
}

export function useAdminAction({ client, reload }: AdminActionConfig): { readonly state: AdminActionState; readonly preview: (intent: ActionIntent) => Promise<void>; readonly confirm: () => Promise<void> } {
  const [state, setState] = useState<AdminActionState>({ kind: "idle" })
  const previewRequest = useRef(0)

  const preview = useCallback(async (intent: ActionIntent): Promise<void> => {
    const requestId = previewRequest.current + 1
    previewRequest.current = requestId
    setState({ kind: "previewing" })
    try {
      const result = await client.previewAdminAction(intent.project_id, intent.action, intent, new AbortController().signal)
      if (previewRequest.current !== requestId) return
      setState(result.allowed ? { kind: "awaiting-confirmation", intent, preview: result } : { kind: "blocked", preview: result })
    } catch (error) {
      if (previewRequest.current === requestId) setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [client])

  const confirm = useCallback(async (): Promise<void> => {
    if (state.kind !== "awaiting-confirmation") return
    previewRequest.current += 1
    setState({ kind: "confirming" })
    let result: ActionConfirmResult
    try {
      result = await client.confirmAdminAction(state.intent.project_id, state.intent.action, { confirmed: true, idempotency_key: `idem-${crypto.randomUUID()}`, intent: state.intent, preview_hash: state.preview.preview_hash }, new AbortController().signal)
    } catch (error) {
      if (error instanceof OperatorApiError && error.status === 409) {
        setState({ kind: "reloading" })
        try {
          await reload()
          setState({ kind: "idle", notice: "Kanonischer Stand wurde aktualisiert. Bitte Vorschau erneut erstellen." })
        } catch (reloadError) {
          setState({ kind: "failed", message: errorMessage(reloadError) })
        }
        return
      }
      setState({ kind: "failed", message: errorMessage(error) })
      return
    }
    setState({ kind: "reloading" })
    try {
      await reload()
      setState({ kind: "completed", replay: result.replay })
    } catch (error) {
      setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [client, reload, state])

  return { state, preview, confirm }
}
