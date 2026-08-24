import type { DiagnosticTraceOperation } from "../generated/api-types"
import type { OperatorApiClient } from "./client"
import { OperatorApiError } from "./operatorApiError"

const actions = {
  acceptMarkdownIntake: "accept_markdown_intake",
  confirmAdminAction: "confirm_admin_action",
  createDeliveryExport: "create_delivery_export",
  downloadDeliveryExport: "download_delivery_export",
  previewAdminAction: "preview_admin_action",
  saveArtifactRevision: "save_artifact_revision",
  validateArtifactRevision: "validate_artifact_revision",
} as const

type DiagnosticAction = (typeof actions)[keyof typeof actions]
type OperationDefinition = { readonly action: DiagnosticAction; readonly apiMethod: DiagnosticTraceOperation["api_method"]; readonly route: string }
type OperationBase = OperationDefinition & { readonly occurredAt: string; readonly operationId: string }
type Failure = { readonly apiStatus: number; readonly errorCode: string; readonly remediation: string }
type TrackInput<T> = { readonly operation: OperationDefinition; readonly execute: () => Promise<T>; readonly successStatus: (result: T) => number }

export type DiagnosticTraceRecorder = Pick<{ readonly record: (entry: DiagnosticTraceOperation) => Promise<void> }, "record">
type DiagnosticOperatorApiConfig = { readonly api: OperatorApiClient; readonly now?: () => Date; readonly reporter: DiagnosticTraceRecorder; readonly tenantId: string }

function utcSeconds(date: Date): string {
  return date.toISOString().replace(/\.\d{3}Z$/, "Z")
}

function projectRoute(tenantId: string, projectId: string): string {
  return `/v1/tenants/${encodeURIComponent(tenantId)}/projects/${encodeURIComponent(projectId)}`
}

function operationId(sequence: number, action: DiagnosticAction): string {
  return `operation-${String(sequence).padStart(4, "0")}-${action.replaceAll("_", "-")}`
}

function fallbackErrorCode(kind: OperatorApiError["kind"]): string {
  switch (kind) {
    case "http":
      return "ERROR_DIAGNOSTIC_OPERATOR_HTTP"
    case "network":
      return "ERROR_DIAGNOSTIC_OPERATOR_NETWORK"
    case "unparseable":
      return "ERROR_DIAGNOSTIC_OPERATOR_UNPARSEABLE"
    default: {
      const unreachableKind: never = kind
      return unreachableKind
    }
  }
}

function failure(error: unknown): Failure {
  if (error instanceof OperatorApiError) return { apiStatus: error.status >= 100 && error.status <= 599 ? error.status : 599, errorCode: error.code ?? fallbackErrorCode(error.kind), remediation: "retry-operator-action" }
  return { apiStatus: 599, errorCode: "ERROR_DIAGNOSTIC_OPERATOR_UNEXPECTED", remediation: "retry-operator-action" }
}

function successfulEntry(operation: OperationBase, apiStatus: number): DiagnosticTraceOperation {
  return { action: operation.action, api_method: operation.apiMethod, api_status: apiStatus, disabled_actions: [], evidence_references: [], expected_actions: [operation.action], occurred_at: operation.occurredAt, operation_id: operation.operationId, rendered_actions: [operation.action], route: operation.route }
}

function failedEntry(operation: OperationBase, outcome: Failure): DiagnosticTraceOperation {
  return { ...successfulEntry(operation, outcome.apiStatus), error_code: outcome.errorCode, remediation: outcome.remediation }
}

async function reportWithoutChangingActionResult(reporter: DiagnosticTraceRecorder, entry: DiagnosticTraceOperation): Promise<void> {
  await reporter.record(entry).then(() => undefined, () => undefined)
}

export function createDiagnosticOperatorApiClient(config: DiagnosticOperatorApiConfig): OperatorApiClient {
  let sequence = 0
  const now = config.now ?? (() => new Date())
  const baseRoute = (projectId: string): string => projectRoute(config.tenantId, projectId)
  const nextOperation = (definition: OperationDefinition): OperationBase => {
    sequence += 1
    return { ...definition, occurredAt: utcSeconds(now()), operationId: operationId(sequence, definition.action) }
  }
  const track = async <T>(input: TrackInput<T>): Promise<T> => {
    try {
      const result = await input.execute()
      await reportWithoutChangingActionResult(config.reporter, successfulEntry(nextOperation(input.operation), input.successStatus(result)))
      return result
    } catch (error) {
      await reportWithoutChangingActionResult(config.reporter, failedEntry(nextOperation(input.operation), failure(error)))
      throw error
    }
  }
  return {
    ...config.api,
    acceptMarkdownIntake: (request, signal) => track({ execute: () => config.api.acceptMarkdownIntake(request, signal), operation: { action: actions.acceptMarkdownIntake, apiMethod: "POST", route: `/v1/tenants/${encodeURIComponent(config.tenantId)}/intake/accept` }, successStatus: () => 200 }),
    previewAdminAction: (projectId, verb, request, signal) => track({ execute: () => config.api.previewAdminAction(projectId, verb, request, signal), operation: { action: actions.previewAdminAction, apiMethod: "POST", route: `${baseRoute(projectId)}/actions/${encodeURIComponent(verb)}/preview` }, successStatus: () => 200 }),
    confirmAdminAction: (projectId, verb, request, signal) => track({ execute: () => config.api.confirmAdminAction(projectId, verb, request, signal), operation: { action: actions.confirmAdminAction, apiMethod: "POST", route: `${baseRoute(projectId)}/actions/${encodeURIComponent(verb)}/confirm` }, successStatus: () => 200 }),
    saveArtifactRevision: (projectId, request, signal) => track({ execute: () => config.api.saveArtifactRevision(projectId, request, signal), operation: { action: actions.saveArtifactRevision, apiMethod: "POST", route: `${baseRoute(projectId)}/artifacts` }, successStatus: () => 200 }),
    validateArtifactRevision: (projectId, artifactId, request, signal) => track({ execute: () => config.api.validateArtifactRevision(projectId, artifactId, request, signal), operation: { action: actions.validateArtifactRevision, apiMethod: "POST", route: `${baseRoute(projectId)}/artifacts/${encodeURIComponent(artifactId)}/validate` }, successStatus: () => 200 }),
    createDeliveryExport: (projectId, request, signal) => track({ execute: () => config.api.createDeliveryExport(projectId, request, signal), operation: { action: actions.createDeliveryExport, apiMethod: "POST", route: `${baseRoute(projectId)}/delivery/exports` }, successStatus: (result) => result.replayState === "replayed" ? 200 : 201 }),
    downloadDeliveryExport: (projectId, exportId, signal) => track({ execute: () => config.api.downloadDeliveryExport(projectId, exportId, signal), operation: { action: actions.downloadDeliveryExport, apiMethod: "GET", route: `${baseRoute(projectId)}/delivery/exports/${encodeURIComponent(exportId)}/download` }, successStatus: () => 200 }),
  }
}
