import type {
  ActionBlocker,
  ActionConfirmRequest,
  ActionConfirmResult,
  ActionIntent,
  ActionPreview,
  ApiOperationMap,
  ArtifactCandidateSaveRequest,
  ArtifactContentResponse,
  ArtifactDiffRequest,
  ArtifactDiffResponse,
  ArtifactRecord,
  ArtifactRevisionListResponse,
  ArtifactValidationRequest,
  DataEnvelope,
  IntakeAcceptanceRequest,
  IntakePreviewRequest,
} from "../generated/api-types"
import {
  parseArtifacts,
  parseContext,
  parseCurrentRun,
  parseGates,
  parseIntegrations,
  parseIntakePreview,
  parseIntakeAcceptance,
  parseProject,
  parseProjectList,
  parseReleases,
  parseRun,
  parseSteps,
  parseTasks,
  parseWorkflow,
} from "./readModels"
import { parseArtifactPreflight } from "./artifactPreflightReadModel"
import {
  parseDeliveryExportHistory,
  parseDeliveryExportResult,
  parseDeliveryPackageRecord,
  parseDeliveryPreview,
} from "./deliveryReadModels"
import type {
  ContextRead,
  CurrentRun,
  GateRead,
  IntegrationRead,
  IntakePreviewRead,
  IntakeAcceptanceRead,
  ProjectSummary,
  RunRead,
  ReleaseRead,
  StepRead,
  TaskRead,
  WorkflowRead,
} from "./readModels"
import type { ArtifactPreflightRead } from "./artifactPreflightReadModel"
import type {
  DeliveryCreateRequest,
  DeliveryExportResultRead,
  DeliveryPackageRecordRead,
  DeliveryPreviewRead,
  DeliveryScope,
} from "./deliveryReadModels"
import { requestDeliveryDownload, type DeliveryDownload } from "./deliveryDownload"
import { OperatorApiError } from "./operatorApiError"

export { OperatorApiError } from "./operatorApiError"
export type { DeliveryDownload } from "./deliveryDownload"

type ReadyResponse = ApiOperationMap["readyz"]["responses"]["200"]

type OperatorApiClientConfig = { readonly baseUrl: string; readonly tenantId: string }

export type OperatorApiClient = {
  readonly readyz: (signal: AbortSignal) => Promise<ReadyResponse>
  readonly listProjects: (signal: AbortSignal) => Promise<readonly ProjectSummary[]>
  readonly getProject: (projectId: string, signal: AbortSignal) => Promise<ProjectSummary>
  readonly getCurrentRun: (projectId: string, signal: AbortSignal) => Promise<CurrentRun>
  readonly getRun: (projectId: string, runId: string, signal: AbortSignal) => Promise<RunRead>
  readonly getWorkflow: (projectId: string, signal: AbortSignal) => Promise<WorkflowRead>
  readonly listSteps: (projectId: string, signal: AbortSignal) => Promise<readonly StepRead[]>
  readonly listTasks: (projectId: string, signal: AbortSignal) => Promise<readonly TaskRead[]>
  readonly listArtifacts: (projectId: string, signal: AbortSignal) => Promise<readonly ArtifactRecord[]>
  readonly listReleases: (projectId: string, signal: AbortSignal) => Promise<readonly ReleaseRead[]>
  readonly listGates: (projectId: string, signal: AbortSignal) => Promise<readonly GateRead[]>
  readonly listContextPackages: (projectId: string, signal: AbortSignal) => Promise<readonly ContextRead[]>
  readonly getIntegrationStatus: (projectId: string, signal: AbortSignal) => Promise<readonly IntegrationRead[]>
  readonly previewMarkdownIntake: (request: IntakePreviewRequest, signal: AbortSignal) => Promise<IntakePreviewRead>
  readonly acceptMarkdownIntake: (request: IntakeAcceptanceRequest, signal: AbortSignal) => Promise<IntakeAcceptanceRead>
  readonly getArtifactContent: (projectId: string, artifactId: string, signal: AbortSignal) => Promise<ArtifactContentResponse>
  readonly saveArtifactRevision: (projectId: string, request: ArtifactCandidateSaveRequest, signal: AbortSignal) => Promise<DataEnvelope>
  readonly listArtifactRevisions: (projectId: string, runId: string, stepId: string, signal: AbortSignal) => Promise<ArtifactRevisionListResponse>
  readonly compareArtifactRevisions: (projectId: string, request: ArtifactDiffRequest, signal: AbortSignal) => Promise<ArtifactDiffResponse>
  readonly validateArtifactRevision: (projectId: string, artifactId: string, request: ArtifactValidationRequest, signal: AbortSignal) => Promise<ArtifactPreflightRead>
  readonly previewAdminAction: (projectId: string, verb: string, request: ActionIntent, signal: AbortSignal) => Promise<ActionPreview>
  readonly confirmAdminAction: (projectId: string, verb: string, request: ActionConfirmRequest, signal: AbortSignal) => Promise<ActionConfirmResult>
  readonly previewDelivery: (projectId: string, scope: DeliveryScope, signal: AbortSignal) => Promise<DeliveryPreviewRead>
  readonly createDeliveryExport: (projectId: string, request: DeliveryCreateRequest, signal: AbortSignal) => Promise<DeliveryExportResultRead>
  readonly listDeliveryExports: (projectId: string, signal: AbortSignal) => Promise<readonly DeliveryExportResultRead[]>
  readonly getDeliveryExport: (projectId: string, exportId: string, signal: AbortSignal) => Promise<DeliveryPackageRecordRead>
  readonly downloadDeliveryExport: (projectId: string, exportId: string, signal: AbortSignal) => Promise<DeliveryDownload>
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function hasString(record: Record<string, unknown>, key: string): boolean {
  return typeof record[key] === "string"
}

function stringValue(record: Record<string, unknown>, key: string): string | null {
  const value = record[key]
  return typeof value === "string" ? value : null
}

function isDataEnvelope(value: unknown): value is DataEnvelope {
  return isRecord(value) && "data" in value
}

function isArtifactRecord(value: unknown): value is ArtifactRecord {
  if (!isRecord(value)) return false
  return ["artifact_id", "content_sha256", "created_at", "input_hash", "project_id", "run_id", "step_id", "storage_key", "tenant_id"].every((key) => hasString(value, key)) && typeof value["revision"] === "number"
}

function isActionIntent(value: unknown): value is ActionIntent {
  if (!isRecord(value)) return false
  return ["action", "project_id", "run_id", "step_id", "tenant_id"].every((key) => hasString(value, key)) && typeof value["expected_revision"] === "number"
}

function isActionBlocker(value: unknown): value is ActionBlocker {
  return isRecord(value) && ["code", "message", "remediation"].every((key) => hasString(value, key))
}

function isActionPreview(value: unknown): value is ActionPreview {
  return isRecord(value) && typeof value["allowed"] === "boolean" && Array.isArray(value["blockers"]) && value["blockers"].every(isActionBlocker) && isRecord(value["consequence"]) && isActionIntent(value["intent"]) && hasString(value, "preview_hash")
}

function isActionConfirmResult(value: unknown): value is ActionConfirmResult {
  return isRecord(value) && isRecord(value["canonical"]) && hasString(value, "preview_hash") && Array.isArray(value["readback_urls"]) && value["readback_urls"].every((url) => typeof url === "string") && typeof value["replay"] === "boolean"
}

function isArtifactContentResponse(value: unknown): value is ArtifactContentResponse {
  return isRecord(value) && isArtifactRecord(value["artifact"]) && hasString(value, "content_base64")
}

function isArtifactRevisionListResponse(value: unknown): value is ArtifactRevisionListResponse {
  return isRecord(value) && Array.isArray(value["artifacts"]) && value["artifacts"].every(isArtifactRecord)
}

function isArtifactDiffResponse(value: unknown): value is ArtifactDiffResponse {
  return isRecord(value) && isArtifactRecord(value["left_artifact"]) && isArtifactRecord(value["right_artifact"]) && hasString(value, "unified_diff")
}

function requestUrl(baseUrl: string, path: string): string {
  return baseUrl === "" ? path : `${baseUrl.replace(/\/$/, "")}${path}`
}

async function request(baseUrl: string, path: string, init: RequestInit, signal: AbortSignal): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(requestUrl(baseUrl, path), { ...init, signal })
  } catch (error) {
    if (error instanceof TypeError) throw new OperatorApiError({ kind: "network", status: 0, message: "Die lokale Operator-API ist nicht erreichbar." })
    throw error
  }
  let payload: unknown
  try {
    payload = await response.json()
  } catch (error) {
    if (error instanceof SyntaxError) throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat ungueltiges JSON geliefert." })
    throw error
  }
  if (!response.ok) {
    const message = isRecord(payload) ? stringValue(payload, "message") ?? `Die lokale Operator-API hat HTTP ${response.status} geliefert.` : `Die lokale Operator-API hat HTTP ${response.status} geliefert.`
    throw new OperatorApiError({ kind: "http", status: response.status, message })
  }
  return payload
}

async function getEnvelope(baseUrl: string, path: string, signal: AbortSignal): Promise<DataEnvelope> {
  const payload = await request(baseUrl, path, { method: "GET" }, signal)
  if (isDataEnvelope(payload)) return payload
  throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die lokale Operator-API hat keine lesbare Datenantwort geliefert." })
}

async function getRead<T>(baseUrl: string, path: string, signal: AbortSignal, parser: (payload: unknown) => T): Promise<T> {
  return parser(await request(baseUrl, path, { method: "GET" }, signal))
}

async function postJson(baseUrl: string, path: string, body: object, signal: AbortSignal): Promise<unknown> {
  return request(baseUrl, path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }, signal)
}

function projectPath(tenantId: string, projectId: string): string {
  return `/v1/tenants/${encodeURIComponent(tenantId)}/projects/${encodeURIComponent(projectId)}`
}

export function createOperatorApiClient(config: OperatorApiClientConfig): OperatorApiClient {
  const projects = `/v1/tenants/${encodeURIComponent(config.tenantId)}/projects`
  const deliveryPath = (projectId: string): string => `${projectPath(config.tenantId, projectId)}/delivery`
  const envelopePost = async (path: string, body: object, signal: AbortSignal): Promise<DataEnvelope> => {
    const payload = await postJson(config.baseUrl, path, body, signal)
    if (isDataEnvelope(payload)) return payload
    throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die lokale Operator-API hat keine lesbare Datenantwort geliefert." })
  }
  return {
    readyz: (signal) => getEnvelope(config.baseUrl, "/readyz", signal),
    listProjects: (signal) => getRead(config.baseUrl, projects, signal, (payload) => parseProjectList(payload, config.tenantId)),
    getProject: (projectId, signal) => getRead(config.baseUrl, projectPath(config.tenantId, projectId), signal, (payload) => parseProject(payload, config.tenantId, projectId)),
    getCurrentRun: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/runs/current`, signal, (payload) => parseCurrentRun(payload, config.tenantId, projectId)),
    getRun: (projectId, runId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/runs/${encodeURIComponent(runId)}`, signal, (payload) => parseRun(payload, config.tenantId, projectId, runId)),
    getWorkflow: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/workflow`, signal, (payload) => parseWorkflow(payload, config.tenantId, projectId)),
    listSteps: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/steps`, signal, (payload) => parseSteps(payload, config.tenantId, projectId)),
    listTasks: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/tasks`, signal, (payload) => parseTasks(payload, config.tenantId, projectId)),
    listArtifacts: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/artifacts`, signal, (payload) => parseArtifacts(payload, config.tenantId, projectId)),
    listReleases: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/releases`, signal, (payload) => parseReleases(payload, config.tenantId, projectId)),
    listGates: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/gates`, signal, (payload) => parseGates(payload, config.tenantId, projectId)),
    listContextPackages: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/context-packages`, signal, (payload) => parseContext(payload, config.tenantId, projectId)),
    getIntegrationStatus: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/integrations/status`, signal, (payload) => parseIntegrations(payload, config.tenantId, projectId)),
    previewMarkdownIntake: async (body, signal) => parseIntakePreview(await postJson(config.baseUrl, `/v1/tenants/${encodeURIComponent(config.tenantId)}/intake/preview`, body, signal)),
    acceptMarkdownIntake: async (body, signal) => parseIntakeAcceptance(await envelopePost(`/v1/tenants/${encodeURIComponent(config.tenantId)}/intake/accept`, body, signal), config.tenantId),
    getArtifactContent: async (projectId, artifactId, signal) => {
      const payload = await request(config.baseUrl, `${projectPath(config.tenantId, projectId)}/artifacts/${encodeURIComponent(artifactId)}/content`, { method: "GET" }, signal)
      if (isArtifactContentResponse(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der Artefaktinhalt ist nicht lesbar." })
    },
    saveArtifactRevision: (projectId, body, signal) => envelopePost(`${projectPath(config.tenantId, projectId)}/artifacts`, body, signal),
    listArtifactRevisions: async (projectId, runId, stepId, signal) => {
      const payload = await request(config.baseUrl, `${projectPath(config.tenantId, projectId)}/runs/${encodeURIComponent(runId)}/steps/${encodeURIComponent(stepId)}/artifact-revisions`, { method: "GET" }, signal)
      if (isArtifactRevisionListResponse(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Revisionsliste ist nicht lesbar." })
    },
    compareArtifactRevisions: async (projectId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/artifact-revisions/compare`, body, signal)
      if (isArtifactDiffResponse(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der Revisionsvergleich ist nicht lesbar." })
    },
    validateArtifactRevision: async (projectId, artifactId, body, signal) => parseArtifactPreflight(await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/artifacts/${encodeURIComponent(artifactId)}/validate`, body, signal)),
    previewAdminAction: async (projectId, verb, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/actions/${encodeURIComponent(verb)}/preview`, body, signal)
      if (isActionPreview(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Aktionsvorschau ist nicht lesbar." })
    },
    confirmAdminAction: async (projectId, verb, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/actions/${encodeURIComponent(verb)}/confirm`, body, signal)
      if (isActionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Aktionsbestaetigung ist nicht lesbar." })
    },
    previewDelivery: (projectId, scope, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/preview?${new URLSearchParams({ scope }).toString()}`, signal, (payload) => parseDeliveryPreview(payload, scope)),
    createDeliveryExport: async (projectId, body, signal) => parseDeliveryExportResult(await postJson(config.baseUrl, `${deliveryPath(projectId)}/exports`, body, signal), config.tenantId, projectId),
    listDeliveryExports: (projectId, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/exports`, signal, (payload) => parseDeliveryExportHistory(payload, config.tenantId, projectId)),
    getDeliveryExport: (projectId, exportId, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/exports/${encodeURIComponent(exportId)}`, signal, (payload) => parseDeliveryPackageRecord(payload, config.tenantId, projectId, exportId)),
    downloadDeliveryExport: (projectId, exportId, signal) => requestDeliveryDownload(config.baseUrl, `${deliveryPath(projectId)}/exports/${encodeURIComponent(exportId)}/download`, signal),
  }
}
