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
  parseAcceptedIntake,
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
  AcceptedIntakeRead,
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

export type ProductionIntent = {
  readonly tenant_id: string
  readonly project_id: string
  readonly run_id: string
  readonly step_id: "0" | "1" | "1b" | "1c" | "2" | "3" | "4a" | "4b"
  readonly expected_revision: number
}

export type ProductionPreview = {
  readonly intent: ProductionIntent
  readonly allowed: boolean
  readonly blockers: readonly ActionBlocker[]
  readonly consequence: Readonly<Record<string, unknown>>
  readonly preview_hash: string
}

export type ProductionConfirmRequest = {
  readonly intent: ProductionIntent
  readonly preview_hash: string
  readonly idempotency_key: string
  readonly confirmed: true
}

export type ProductionConfirmResult = {
  readonly replay: boolean
  readonly execution_id: string
  readonly status: "prepared" | "running" | "interaction_required" | "approval_required" | "denied" | "completed" | "failed"
  readonly preview_hash: string
  readonly readback_urls: readonly string[]
  readonly canonical: Readonly<Record<string, unknown>>
}

export type ToolInteractionDecisionRequest = {
  readonly approved: boolean
  readonly expected_request_sha256: string
  readonly reason: string
}

export type ProductionTechnicalRetryRequest = {
  readonly idempotency_key: string
  readonly expected_execution_sha256: string
  readonly reason: string
}

export type ProductionSteeredRerunRequest = {
  readonly idempotency_key: string
  readonly expected_execution_sha256: string
  readonly expected_artifact_sha256: string
  readonly expected_artifact_revision: number
  readonly findings: readonly string[]
  readonly affected_sections: readonly string[]
  readonly immutable_constraints: readonly string[]
  readonly instruction: string
  readonly confirmed: true
}

export type PlanningCapacityPreviewRequest = {
  readonly min_hours_per_week: number
  readonly max_hours_per_week: number
}

export type PlanningCapacityPreview = {
  readonly tenant_id: string
  readonly project_id: string
  readonly preview_hash: string
  readonly current_project_sha256: string
  readonly proposed_project_sha256: string
  readonly capacity: Readonly<{ min: number; max: number; source: "operator_confirmed"; provisional: false; confirmed_by: string; confirmed_at: string }>
  readonly run_id: string
  readonly deployment_id: string
  readonly changed: boolean
}

export type PlanningCapacityConfirmRequest = {
  readonly preview_hash: string
  readonly idempotency_key: string
  readonly confirmed: true
}

export type ProjectDeletionPreview = {
  readonly tenant_id: string
  readonly project_id: string
  readonly project_name: string
  readonly customer_name: string
  readonly current_step: string
  readonly file_count: number
  readonly total_bytes: number
  readonly run_count: number
  readonly artifact_count: number
  readonly release_count: number
  readonly active_run_ids: readonly string[]
  readonly active_execution_ids: readonly string[]
  readonly allowed: boolean
  readonly blockers: readonly ActionBlocker[]
  readonly preview_hash: string
  readonly workspace_sha256: string
  readonly previewed_at: string
}

export type ProjectDeletionConfirmRequest = {
  readonly preview_hash: string
  readonly idempotency_key: string
  readonly confirmed: true
  readonly confirmation_text: "LOESCHEN"
}

export type ProjectDeletionResult = {
  readonly tenant_id: string
  readonly project_id: string
  readonly project_name: string
  readonly deletion_id: string
  readonly deleted_at: string
  readonly deleted: true
  readonly replay: boolean
  readonly deleted_file_count: number
  readonly deleted_total_bytes: number
  readonly readback_urls: readonly string[]
}

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
  readonly getMarkdownIntake: (projectId: string, signal: AbortSignal) => Promise<AcceptedIntakeRead>
  readonly previewMarkdownIntake: (request: IntakePreviewRequest, signal: AbortSignal) => Promise<IntakePreviewRead>
  readonly acceptMarkdownIntake: (request: IntakeAcceptanceRequest, signal: AbortSignal) => Promise<IntakeAcceptanceRead>
  readonly previewPlanningCapacity: (projectId: string, request: PlanningCapacityPreviewRequest, signal: AbortSignal) => Promise<PlanningCapacityPreview>
  readonly confirmPlanningCapacity: (projectId: string, request: PlanningCapacityConfirmRequest, signal: AbortSignal) => Promise<PlanningCapacityPreview>
  readonly previewProjectDeletion: (projectId: string, signal: AbortSignal) => Promise<ProjectDeletionPreview>
  readonly confirmProjectDeletion: (projectId: string, request: ProjectDeletionConfirmRequest, signal: AbortSignal) => Promise<ProjectDeletionResult>
  readonly getArtifactContent: (projectId: string, artifactId: string, signal: AbortSignal) => Promise<ArtifactContentResponse>
  readonly saveArtifactRevision: (projectId: string, request: ArtifactCandidateSaveRequest, signal: AbortSignal) => Promise<DataEnvelope>
  readonly listArtifactRevisions: (projectId: string, runId: string, stepId: string, signal: AbortSignal) => Promise<ArtifactRevisionListResponse>
  readonly compareArtifactRevisions: (projectId: string, request: ArtifactDiffRequest, signal: AbortSignal) => Promise<ArtifactDiffResponse>
  readonly validateArtifactRevision: (projectId: string, artifactId: string, request: ArtifactValidationRequest, signal: AbortSignal) => Promise<ArtifactPreflightRead>
  readonly previewAdminAction: (projectId: string, verb: string, request: ActionIntent, signal: AbortSignal) => Promise<ActionPreview>
  readonly confirmAdminAction: (projectId: string, verb: string, request: ActionConfirmRequest, signal: AbortSignal) => Promise<ActionConfirmResult>
  readonly previewProductionRun: (projectId: string, request: ProductionIntent, signal: AbortSignal) => Promise<ProductionPreview>
  readonly confirmProductionRun: (projectId: string, request: ProductionConfirmRequest, signal: AbortSignal) => Promise<ProductionConfirmResult>
  readonly getProductionExecution: (projectId: string, executionId: string, signal: AbortSignal) => Promise<ProductionConfirmResult>
  readonly getActiveProductionExecution: (projectId: string, runId: string, signal: AbortSignal) => Promise<ProductionConfirmResult | null>
  readonly getLatestProductionExecution: (projectId: string, runId: string, signal: AbortSignal) => Promise<ProductionConfirmResult | null>
  readonly refreshProductionExecution: (projectId: string, executionId: string, signal: AbortSignal) => Promise<ProductionConfirmResult>
  readonly retryProductionExecutionTechnically: (projectId: string, executionId: string, request: ProductionTechnicalRetryRequest, signal: AbortSignal) => Promise<ProductionConfirmResult>
  readonly rerunProductionExecutionWithSteering: (projectId: string, executionId: string, request: ProductionSteeredRerunRequest, signal: AbortSignal) => Promise<ProductionConfirmResult>
  readonly decideProductionInteraction: (projectId: string, executionId: string, interactionId: string, request: ToolInteractionDecisionRequest, signal: AbortSignal) => Promise<ProductionConfirmResult>
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

function isProductionIntent(value: unknown): value is ProductionIntent {
  return isRecord(value) && ["tenant_id", "project_id", "run_id", "step_id"].every((key) => hasString(value, key)) && typeof value["expected_revision"] === "number"
}

function isProductionPreview(value: unknown): value is ProductionPreview {
  return isRecord(value) && isProductionIntent(value["intent"]) && typeof value["allowed"] === "boolean" && Array.isArray(value["blockers"]) && value["blockers"].every(isActionBlocker) && isRecord(value["consequence"]) && hasString(value, "preview_hash")
}

function isProductionConfirmResult(value: unknown): value is ProductionConfirmResult {
  return isRecord(value) && isRecord(value["canonical"]) && hasString(value, "execution_id") && ["prepared", "running", "interaction_required", "approval_required", "denied", "completed", "failed"].includes(String(value["status"])) && hasString(value, "preview_hash") && Array.isArray(value["readback_urls"]) && value["readback_urls"].every((url) => typeof url === "string") && typeof value["replay"] === "boolean"
}

function isPlanningCapacityPreview(value: unknown): value is PlanningCapacityPreview {
  if (!isRecord(value) || !isRecord(value["capacity"])) return false
  const capacity = value["capacity"]
  return ["tenant_id", "project_id", "preview_hash", "current_project_sha256", "proposed_project_sha256", "run_id", "deployment_id"].every((key) => hasString(value, key))
    && typeof value["changed"] === "boolean"
    && typeof capacity["min"] === "number"
    && typeof capacity["max"] === "number"
    && capacity["source"] === "operator_confirmed"
    && capacity["provisional"] === false
    && hasString(capacity, "confirmed_by")
    && hasString(capacity, "confirmed_at")
}

function parsePlanningCapacityEnvelope(value: unknown): PlanningCapacityPreview {
  if (isDataEnvelope(value) && isPlanningCapacityPreview(value.data)) return value.data
  throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Kapazitätsbestätigung ist nicht lesbar." })
}

function isProjectDeletionPreview(value: unknown): value is ProjectDeletionPreview {
  if (!isRecord(value)) return false
  const numericKeys = ["file_count", "total_bytes", "run_count", "artifact_count", "release_count"]
  const stringKeys = ["tenant_id", "project_id", "project_name", "customer_name", "current_step", "preview_hash", "workspace_sha256", "previewed_at"]
  return stringKeys.every((key) => hasString(value, key))
    && numericKeys.every((key) => typeof value[key] === "number" && Number(value[key]) >= 0)
    && Array.isArray(value["active_run_ids"])
    && value["active_run_ids"].every((item) => typeof item === "string")
    && Array.isArray(value["active_execution_ids"])
    && value["active_execution_ids"].every((item) => typeof item === "string")
    && Array.isArray(value["blockers"])
    && value["blockers"].every(isActionBlocker)
    && typeof value["allowed"] === "boolean"
}

function isProjectDeletionResult(value: unknown): value is ProjectDeletionResult {
  if (!isRecord(value)) return false
  return ["tenant_id", "project_id", "project_name", "deletion_id", "deleted_at"].every((key) => hasString(value, key))
    && value["deleted"] === true
    && typeof value["replay"] === "boolean"
    && typeof value["deleted_file_count"] === "number"
    && Number(value["deleted_file_count"]) >= 0
    && typeof value["deleted_total_bytes"] === "number"
    && Number(value["deleted_total_bytes"]) >= 0
    && Array.isArray(value["readback_urls"])
    && value["readback_urls"].every((url) => typeof url === "string")
}

function parseProjectDeletionPreviewEnvelope(value: unknown): ProjectDeletionPreview {
  if (isDataEnvelope(value) && isProjectDeletionPreview(value.data)) return value.data
  throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Projektlöschvorschau ist nicht lesbar." })
}

function parseProjectDeletionResultEnvelope(value: unknown): ProjectDeletionResult {
  if (isDataEnvelope(value) && isProjectDeletionResult(value.data)) return value.data
  throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Projektlöschbestätigung ist nicht lesbar." })
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
    if (error instanceof SyntaxError) {
      if (!response.ok) throw new OperatorApiError({ kind: "http", status: response.status, message: `Die lokale Operator-API ist mit HTTP ${response.status} fehlgeschlagen und hat keine lesbare Fehlerantwort geliefert.` })
      throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat ungueltiges JSON geliefert." })
    }
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
    getMarkdownIntake: (projectId, signal) => getRead(config.baseUrl, `${projectPath(config.tenantId, projectId)}/intake`, signal, (payload) => parseAcceptedIntake(payload, config.tenantId, projectId)),
    previewMarkdownIntake: async (body, signal) => parseIntakePreview(await postJson(config.baseUrl, `/v1/tenants/${encodeURIComponent(config.tenantId)}/intake/preview`, body, signal)),
    acceptMarkdownIntake: async (body, signal) => parseIntakeAcceptance(await envelopePost(`/v1/tenants/${encodeURIComponent(config.tenantId)}/intake/accept`, body, signal), config.tenantId),
    previewPlanningCapacity: async (projectId, body, signal) => parsePlanningCapacityEnvelope(
      await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/inputs/planning-capacity/preview`, body, signal),
    ),
    confirmPlanningCapacity: async (projectId, body, signal) => parsePlanningCapacityEnvelope(
      await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/inputs/planning-capacity/confirm`, body, signal),
    ),
    previewProjectDeletion: async (projectId, signal) => parseProjectDeletionPreviewEnvelope(
      await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/deletion/preview`, {}, signal),
    ),
    confirmProjectDeletion: async (projectId, body, signal) => parseProjectDeletionResultEnvelope(
      await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/deletion/confirm`, body, signal),
    ),
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
    previewProductionRun: async (projectId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/preview`, body, signal)
      if (isProductionPreview(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Produktionsvorschau ist nicht lesbar." })
    },
    confirmProductionRun: async (projectId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/confirm`, body, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Produktionsbestaetigung ist nicht lesbar." })
    },
    getProductionExecution: async (projectId, executionId, signal) => {
      const payload = await request(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/executions/${encodeURIComponent(executionId)}`, { method: "GET" }, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der Produktionsstatus ist nicht lesbar." })
    },
    getActiveProductionExecution: async (projectId, runId, signal) => {
      let payload: unknown
      try {
        payload = await request(config.baseUrl, `${projectPath(config.tenantId, projectId)}/runs/${encodeURIComponent(runId)}/production/execution`, { method: "GET" }, signal)
      } catch (error) {
        if (error instanceof OperatorApiError && error.status === 404) return null
        throw error
      }
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der aktive Produktionsstatus ist nicht lesbar." })
    },
    getLatestProductionExecution: async (projectId, runId, signal) => {
      let payload: unknown
      try {
        payload = await request(config.baseUrl, `${projectPath(config.tenantId, projectId)}/runs/${encodeURIComponent(runId)}/production/latest-execution`, { method: "GET" }, signal)
      } catch (error) {
        if (error instanceof OperatorApiError && error.status === 404) return null
        throw error
      }
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der letzte Produktionsstatus ist nicht lesbar." })
    },
    refreshProductionExecution: async (projectId, executionId, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/executions/${encodeURIComponent(executionId)}/refresh`, {}, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der Produktionsstatus ist nicht lesbar." })
    },
    retryProductionExecutionTechnically: async (projectId, executionId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/executions/${encodeURIComponent(executionId)}/technical-retry`, body, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der technische Retry ist nicht lesbar." })
    },
    rerunProductionExecutionWithSteering: async (projectId, executionId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/executions/${encodeURIComponent(executionId)}/steered-rerun`, body, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Der fachliche Rerun ist nicht lesbar." })
    },
    decideProductionInteraction: async (projectId, executionId, interactionId, body, signal) => {
      const payload = await postJson(config.baseUrl, `${projectPath(config.tenantId, projectId)}/production/executions/${encodeURIComponent(executionId)}/interactions/${encodeURIComponent(interactionId)}/decision`, body, signal)
      if (isProductionConfirmResult(payload)) return payload
      throw new OperatorApiError({ kind: "unparseable", status: 200, message: "Die Toolentscheidung ist nicht lesbar." })
    },
    previewDelivery: (projectId, scope, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/preview?${new URLSearchParams({ scope }).toString()}`, signal, (payload) => parseDeliveryPreview(payload, scope)),
    createDeliveryExport: async (projectId, body, signal) => parseDeliveryExportResult(await postJson(config.baseUrl, `${deliveryPath(projectId)}/exports`, body, signal), config.tenantId, projectId),
    listDeliveryExports: (projectId, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/exports`, signal, (payload) => parseDeliveryExportHistory(payload, config.tenantId, projectId)),
    getDeliveryExport: (projectId, exportId, signal) => getRead(config.baseUrl, `${deliveryPath(projectId)}/exports/${encodeURIComponent(exportId)}`, signal, (payload) => parseDeliveryPackageRecord(payload, config.tenantId, projectId, exportId)),
    downloadDeliveryExport: (projectId, exportId, signal) => requestDeliveryDownload(config.baseUrl, `${deliveryPath(projectId)}/exports/${encodeURIComponent(exportId)}/download`, signal),
  }
}
