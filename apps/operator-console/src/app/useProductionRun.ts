import { useCallback, useEffect, useRef, useState } from "react"
import { OperatorApiError } from "../api/client"
import type { OperatorApiClient, ProductionConfirmResult, ProductionIntent, ProductionPreview } from "../api/client"

export type ToolInteractionRead = Readonly<Record<string, unknown>> & {
  readonly interaction_id: string
  readonly operation_id: string
  readonly confirmation_scope: string
  readonly cost_mode: string
  readonly request_sha256: string
  readonly request: Readonly<Record<string, unknown>>
  readonly maximum_cost_usd?: number | null
}

export type ProductionRunState =
  | { readonly kind: "idle" }
  | { readonly kind: "previewing" }
  | { readonly kind: "blocked"; readonly preview: ProductionPreview }
  | { readonly kind: "awaiting-confirmation"; readonly intent: ProductionIntent; readonly preview: ProductionPreview }
  | { readonly kind: "confirming" }
  | { readonly kind: "running"; readonly result: ProductionConfirmResult }
  | { readonly kind: "awaiting-tool-decision"; readonly projectId: string; readonly result: ProductionConfirmResult; readonly interaction: ToolInteractionRead }
  | { readonly kind: "deciding" }
  | { readonly kind: "retrying" }
  | { readonly kind: "rerunning" }
  | { readonly kind: "reloading" }
  | { readonly kind: "completed"; readonly replay: boolean; readonly projectId: string; readonly result: ProductionConfirmResult }
  | { readonly kind: "denied" }
  | { readonly kind: "failed"; readonly message: string; readonly technicalRetry?: { readonly projectId: string; readonly result: ProductionConfirmResult } }

type ProductionRunConfig = {
  readonly client: OperatorApiClient
  readonly reload: () => Promise<void>
  readonly intent: ProductionIntent
}

export type SteeredRerunInput = {
  readonly findings: readonly string[]
  readonly affectedSections: readonly string[]
  readonly immutableConstraints: readonly string[]
  readonly instruction: string
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Der Produktionslauf konnte nicht verarbeitet werden."
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function interactionFrom(result: ProductionConfirmResult): ToolInteractionRead | null {
  const interactions = result.canonical["interactions"]
  if (!Array.isArray(interactions) || interactions.length !== 1 || !isRecord(interactions[0])) return null
  const interaction = interactions[0]
  if (
    typeof interaction["interaction_id"] !== "string"
    || typeof interaction["operation_id"] !== "string"
    || typeof interaction["confirmation_scope"] !== "string"
    || typeof interaction["cost_mode"] !== "string"
    || typeof interaction["request_sha256"] !== "string"
    || !isRecord(interaction["request"])
  ) return null
  return interaction as ToolInteractionRead
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

export function useProductionRun({ client, reload, intent }: ProductionRunConfig): {
  readonly state: ProductionRunState
  readonly preview: (intent: ProductionIntent) => Promise<void>
  readonly confirm: () => Promise<void>
  readonly decideTool: (approved: boolean, reason: string) => Promise<void>
  readonly retryTechnical: (reason: string) => Promise<void>
  readonly rerunWithSteering: (input: SteeredRerunInput) => Promise<void>
} {
  const [state, setState] = useState<ProductionRunState>({ kind: "idle" })
  const requestGeneration = useRef(0)

  const advance = useCallback(async (projectId: string, initial: ProductionConfirmResult, generation: number): Promise<void> => {
    let result = initial
    while (requestGeneration.current === generation) {
      if (result.status === "completed") {
        setState({ kind: "reloading" })
        try {
          await reload()
          if (requestGeneration.current === generation) setState({ kind: "completed", replay: result.replay, projectId, result })
        } catch (error) {
          if (requestGeneration.current === generation) setState({ kind: "failed", message: errorMessage(error) })
        }
        return
      }
      if (result.status === "denied") {
        setState({ kind: "denied" })
        return
      }
      if (result.status === "failed") {
        const execution = result.canonical["execution"]
        const error = isRecord(execution) ? execution["error"] : null
        const message = isRecord(error) && typeof error["message"] === "string" ? error["message"] : "Der Produktionslauf ist fail-closed abgebrochen."
        const code = isRecord(error) && typeof error["code"] === "string" ? error["code"] : null
        const retryable = code !== null && new Set([
          "ERROR_LLM_BACKEND_UNAVAILABLE",
          "ERROR_LLM_BACKEND_TIMEOUT",
          "ERROR_LLM_BACKEND_STREAM_UNAVAILABLE",
          "ERROR_LLM_BACKEND_RESPONSE_INVALID",
          "ERROR_LLM_BACKEND_RUN_FAILED",
          "ERROR_STEP_AGENT_EVENT_EVIDENCE_UNAVAILABLE",
        ]).has(code)
        setState({
          kind: "failed",
          message,
          ...(retryable ? { technicalRetry: { projectId, result } } : {}),
        })
        return
      }
      if (result.status === "interaction_required" || result.status === "approval_required") {
        const interaction = interactionFrom(result)
        if (interaction === null) {
          setState({ kind: "failed", message: "Die wartende Toolfreigabe ist nicht eindeutig lesbar." })
          return
        }
        setState({ kind: "awaiting-tool-decision", projectId, result, interaction })
        return
      }
      setState({ kind: "running", result })
      await wait(1500)
      if (requestGeneration.current !== generation) return
      try {
        result = await client.refreshProductionExecution(projectId, result.execution_id, new AbortController().signal)
      } catch (error) {
        if (requestGeneration.current === generation) setState({ kind: "failed", message: errorMessage(error) })
        return
      }
    }
  }, [client, reload])

  useEffect(() => {
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    const controller = new AbortController()
    void client.getActiveProductionExecution(intent.project_id, intent.run_id, controller.signal)
      .then(async (result) => {
        if (requestGeneration.current !== generation) return
        if (result === null) {
          const latest = await client.getLatestProductionExecution(intent.project_id, intent.run_id, controller.signal)
          if (requestGeneration.current !== generation) return
          if (latest === null) {
            setState({ kind: "idle" })
            return
          }
          await advance(intent.project_id, latest, generation)
          return
        }
        await advance(intent.project_id, result, generation)
      })
      .catch((error: unknown) => {
        if (requestGeneration.current === generation && !controller.signal.aborted) {
          setState({ kind: "failed", message: errorMessage(error) })
        }
      })
    return () => {
      controller.abort()
      if (requestGeneration.current === generation) requestGeneration.current += 1
    }
  }, [advance, client, intent.project_id, intent.run_id])

  const preview = useCallback(async (intent: ProductionIntent): Promise<void> => {
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    setState({ kind: "previewing" })
    try {
      const result = await client.previewProductionRun(intent.project_id, intent, new AbortController().signal)
      if (requestGeneration.current !== generation) return
      setState(result.allowed ? { kind: "awaiting-confirmation", intent, preview: result } : { kind: "blocked", preview: result })
    } catch (error) {
      if (requestGeneration.current === generation) setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [client])

  const confirm = useCallback(async (): Promise<void> => {
    if (state.kind !== "awaiting-confirmation") return
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    setState({ kind: "confirming" })
    try {
      const result = await client.confirmProductionRun(
        state.intent.project_id,
        {
          confirmed: true,
          idempotency_key: `idem-${crypto.randomUUID()}`,
          intent: state.intent,
          preview_hash: state.preview.preview_hash,
        },
        new AbortController().signal,
      )
      await advance(state.intent.project_id, result, generation)
    } catch (error) {
      if (error instanceof OperatorApiError && error.status === 409) {
        setState({ kind: "reloading" })
        try {
          await reload()
          setState({ kind: "failed", message: "Der kanonische Stand hat sich geändert. Bitte Produktionsvorschau neu erstellen." })
        } catch (reloadError) {
          setState({ kind: "failed", message: errorMessage(reloadError) })
        }
        return
      }
      setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [advance, client, reload, state])

  const decideTool = useCallback(async (approved: boolean, reason: string): Promise<void> => {
    if (state.kind !== "awaiting-tool-decision") return
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    setState({ kind: "deciding" })
    try {
      const result = await client.decideProductionInteraction(
        state.projectId,
        state.result.execution_id,
        state.interaction.interaction_id,
        {
          approved,
          expected_request_sha256: state.interaction.request_sha256,
          reason,
        },
        new AbortController().signal,
      )
      await advance(state.projectId, result, generation)
    } catch (error) {
      setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [advance, client, state])

  const retryTechnical = useCallback(async (reason: string): Promise<void> => {
    if (state.kind !== "failed" || state.technicalRetry === undefined) return
    const execution = state.technicalRetry.result.canonical["execution"]
    const executionSha256 = isRecord(execution) && typeof execution["record_sha256"] === "string"
      ? execution["record_sha256"]
      : null
    if (executionSha256 === null) {
      setState({ kind: "failed", message: "Der technische Retry ist nicht an einen lesbaren Execution-Hash gebunden." })
      return
    }
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    setState({ kind: "retrying" })
    try {
      const result = await client.retryProductionExecutionTechnically(
        state.technicalRetry.projectId,
        state.technicalRetry.result.execution_id,
        {
          idempotency_key: `idem-${crypto.randomUUID()}`,
          expected_execution_sha256: executionSha256,
          reason,
        },
        new AbortController().signal,
      )
      await advance(state.technicalRetry.projectId, result, generation)
    } catch (error) {
      setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [advance, client, state])

  const rerunWithSteering = useCallback(async (input: SteeredRerunInput): Promise<void> => {
    if (state.kind !== "completed") return
    const execution = state.result.canonical["execution"]
    const completion = state.result.canonical["completion"]
    const executionSha256 = isRecord(execution) && typeof execution["record_sha256"] === "string"
      ? execution["record_sha256"]
      : null
    const artifacts = isRecord(completion) && Array.isArray(completion["artifacts"])
      ? completion["artifacts"].filter(isRecord)
      : []
    const gates = isRecord(completion) && Array.isArray(completion["quality_gate_runs"])
      ? completion["quality_gate_runs"].filter(isRecord)
      : []
    const domainGate = gates.find((gate) => gate["quality_gate_id"] === "qg-domain-contract")
    const primaryId = domainGate !== undefined && typeof domainGate["artifact_id"] === "string" ? domainGate["artifact_id"] : null
    const primary = artifacts.find(
      (artifact) => primaryId !== null && artifact["artifact_id"] === primaryId,
    )
    const artifactSha256 = primary !== undefined && typeof primary["content_sha256"] === "string"
      ? primary["content_sha256"]
      : null
    const artifactRevision = primary !== undefined && typeof primary["revision"] === "number"
      ? primary["revision"]
      : null
    if (executionSha256 === null || artifactSha256 === null || artifactRevision === null) {
      setState({ kind: "failed", message: "Der fachliche Rerun ist nicht an eine eindeutige Artefaktrevision gebunden." })
      return
    }
    const generation = requestGeneration.current + 1
    requestGeneration.current = generation
    setState({ kind: "rerunning" })
    try {
      const result = await client.rerunProductionExecutionWithSteering(
        state.projectId,
        state.result.execution_id,
        {
          idempotency_key: `idem-${crypto.randomUUID()}`,
          expected_execution_sha256: executionSha256,
          expected_artifact_sha256: artifactSha256,
          expected_artifact_revision: artifactRevision,
          findings: input.findings,
          affected_sections: input.affectedSections,
          immutable_constraints: input.immutableConstraints,
          instruction: input.instruction,
          confirmed: true,
        },
        new AbortController().signal,
      )
      await advance(state.projectId, result, generation)
    } catch (error) {
      setState({ kind: "failed", message: errorMessage(error) })
    }
  }, [advance, client, state])

  return { state, preview, confirm, decideTool, retryTechnical, rerunWithSteering }
}
