import type { ApiOperationMap, ErrorEnvelope } from "../generated/api-types"
import { OperatorApiError } from "./operatorApiError"

type CreateDiagnosticTrace = ApiOperationMap["createDiagnosticTrace"]
type AppendDiagnosticTraceEntry = ApiOperationMap["appendDiagnosticTraceEntry"]
type CloseDiagnosticTrace = ApiOperationMap["closeDiagnosticTrace"]
type DiagnosticTraceStart = CreateDiagnosticTrace["request"]
type DiagnosticTraceStartResponse = CreateDiagnosticTrace["responses"]["200"]
type DiagnosticTraceOperation = AppendDiagnosticTraceEntry["request"]
type DiagnosticTraceEntryResponse = AppendDiagnosticTraceEntry["responses"]["200"]
type DiagnosticTraceCloseRequest = CloseDiagnosticTrace["request"]
type DiagnosticTraceCloseResponse = CloseDiagnosticTrace["responses"]["200"]

export type DiagnosticTrace = DiagnosticTraceStartResponse & Pick<DiagnosticTraceStart, "schema_version">

type DiagnosticTraceClientConfig = { readonly baseUrl: string }
type JsonObject = Readonly<Record<string, unknown>>
type JsonPostRequest = {
  readonly baseUrl: string
  readonly path: string
  readonly body: object
  readonly signal: AbortSignal
  readonly keepalive?: boolean
}
type JsonResponse = { readonly payload: unknown; readonly status: number }

const identifierPattern = /^[a-z][a-z0-9-]{2,127}$/
const traceIdPattern = /^trace-[a-f0-9]{32}$/

export type DiagnosticTraceClient = {
  readonly create: (input: { readonly start: DiagnosticTraceStart; readonly signal: AbortSignal }) => Promise<DiagnosticTrace>
  readonly append: (input: { readonly trace: DiagnosticTrace; readonly entry: DiagnosticTraceOperation; readonly signal: AbortSignal }) => Promise<DiagnosticTraceEntryResponse>
  readonly close: (input: { readonly trace: DiagnosticTrace; readonly request: DiagnosticTraceCloseRequest; readonly signal: AbortSignal; readonly keepalive: boolean }) => Promise<DiagnosticTraceCloseResponse>
}

function isRecord(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function record(value: unknown): JsonObject | null {
  return isRecord(value) ? value : null
}

function stringField(value: JsonObject, key: string): string | null {
  const field = value[key]
  return typeof field === "string" ? field : null
}

function identifierField(value: JsonObject, key: string): string | null {
  const field = stringField(value, key)
  return field !== null && identifierPattern.test(field) ? field : null
}

function traceIdField(value: JsonObject): string | null {
  const traceId = stringField(value, "trace_id")
  return traceId !== null && traceIdPattern.test(traceId) ? traceId : null
}

function isNullableIdentifier(value: unknown): value is string | null {
  return value === null || typeof value === "string" && identifierPattern.test(value)
}

function diagnosticSource(value: unknown): DiagnosticTraceStartResponse["source"] | null {
  switch (value) {
    case "automated":
      return value
    case "manual":
      return value
    default:
      return null
  }
}

function parseErrorEnvelope(value: unknown): ErrorEnvelope | null {
  const payload = record(value)
  if (payload === null) return null
  const code = stringField(payload, "code")
  const message = stringField(payload, "message")
  return code === null || message === null ? null : { code, message }
}

function parseStartResponse(value: unknown): DiagnosticTraceStartResponse | null {
  const payload = record(value)
  if (payload === null) return null
  const createdAt = stringField(payload, "created_at")
  const projectId = identifierField(payload, "project_id")
  const runId = identifierField(payload, "run_id")
  const scenarioId = identifierField(payload, "scenario_id")
  const source = diagnosticSource(payload["source"])
  const tenantId = identifierField(payload, "tenant_id")
  const traceId = traceIdField(payload)
  const replay = payload["replay"]
  if (createdAt === null || projectId === null || runId === null || scenarioId === null || source === null || tenantId === null || traceId === null || typeof replay !== "boolean" || payload["status"] !== "active") return null
  return { created_at: createdAt, project_id: projectId, replay, run_id: runId, scenario_id: scenarioId, source, status: "active", tenant_id: tenantId, trace_id: traceId }
}

function parseCreateResponse(value: unknown, start: DiagnosticTraceStart): DiagnosticTrace | null {
  const response = parseStartResponse(value)
  if (response === null) return null
  if (response.tenant_id !== start.tenant_id || response.project_id !== start.project_id || response.run_id !== start.run_id || response.scenario_id !== start.scenario_id || response.source !== start.source || response.created_at !== start.created_at) return null
  return { ...response, schema_version: start.schema_version }
}

function parseEntryResponse(value: unknown, trace: DiagnosticTrace, entry: DiagnosticTraceOperation): DiagnosticTraceEntryResponse | null {
  const payload = record(value)
  if (payload === null) return null
  const traceId = traceIdField(payload)
  const operationId = identifierField(payload, "operation_id")
  const sequence = payload["sequence"]
  const replay = payload["replay"]
  if (traceId === null || operationId === null || traceId !== trace.trace_id || operationId !== entry.operation_id || typeof replay !== "boolean" || typeof sequence !== "number" || !Number.isInteger(sequence) || sequence < 1) return null
  return { trace_id: traceId, operation_id: operationId, sequence, replay }
}

function parseCloseResponse(value: unknown, trace: DiagnosticTrace, request: DiagnosticTraceCloseRequest): DiagnosticTraceCloseResponse | null {
  const payload = record(value)
  if (payload === null) return null
  const closeId = identifierField(payload, "close_id")
  const closedAt = stringField(payload, "closed_at")
  const traceId = traceIdField(payload)
  const replay = payload["replay"]
  const lastSuccessfulOperationId = payload["last_successful_operation_id"]
  const firstFailingOperationId = payload["first_failing_operation_id"]
  if (closeId === null || closedAt === null || traceId === null || traceId !== trace.trace_id || closeId !== request.close_id || closedAt !== request.closed_at || typeof replay !== "boolean" || payload["status"] !== "closed" || !isNullableIdentifier(lastSuccessfulOperationId) || !isNullableIdentifier(firstFailingOperationId)) return null
  return { close_id: closeId, closed_at: closedAt, first_failing_operation_id: firstFailingOperationId, last_successful_operation_id: lastSuccessfulOperationId, replay, status: "closed", trace_id: traceId }
}

function requestUrl(baseUrl: string, path: string): string {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, "")
  return normalizedBaseUrl === "" ? path : `${normalizedBaseUrl}${path}`
}

function projectPath(tenantId: string, projectId: string): string {
  return `/v1/tenants/${encodeURIComponent(tenantId)}/projects/${encodeURIComponent(projectId)}`
}

function tracePath(trace: DiagnosticTrace): string {
  return `${projectPath(trace.tenant_id, trace.project_id)}/diagnostic-traces/${encodeURIComponent(trace.trace_id)}`
}

async function postJson(request: JsonPostRequest): Promise<JsonResponse> {
  const init: RequestInit = request.keepalive === undefined
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request.body), signal: request.signal }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request.body), signal: request.signal, keepalive: request.keepalive }
  let response: Response
  try {
    response = await fetch(requestUrl(request.baseUrl, request.path), init)
  } catch (error) {
    if (error instanceof TypeError) throw new OperatorApiError({ kind: "network", status: 0, message: "Die lokale Operator-API ist nicht erreichbar." })
    throw error
  }
  let payload: unknown
  try {
    payload = await response.json()
  } catch (error) {
    if (error instanceof SyntaxError || error instanceof TypeError) throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat ungueltiges JSON geliefert." })
    throw error
  }
  if (!response.ok) {
    const error = parseErrorEnvelope(payload)
    if (error !== null) throw new OperatorApiError({ kind: "http", status: response.status, code: error.code, message: error.message })
    throw new OperatorApiError({ kind: "http", status: response.status, message: `Die lokale Operator-API hat HTTP ${response.status} geliefert.` })
  }
  return { payload, status: response.status }
}

function parseSuccess<T>(response: JsonResponse, parser: (value: unknown) => T | null, message: string): T {
  const parsed = parser(response.payload)
  if (parsed !== null) return parsed
  throw new OperatorApiError({ kind: "unparseable", status: response.status, message })
}

export function createDiagnosticTraceClient({ baseUrl }: DiagnosticTraceClientConfig): DiagnosticTraceClient {
  return {
    create: async ({ start, signal }) => parseSuccess(await postJson({ baseUrl, path: `${projectPath(start.tenant_id, start.project_id)}/diagnostic-traces`, body: start, signal }), (value) => parseCreateResponse(value, start), "Die lokale Operator-API hat keine lesbare Diagnose-Trace geliefert."),
    append: async ({ trace, entry, signal }) => parseSuccess(await postJson({ baseUrl, path: `${tracePath(trace)}/entries`, body: entry, signal }), (value) => parseEntryResponse(value, trace, entry), "Die lokale Operator-API hat keinen lesbaren Diagnoseeintrag geliefert."),
    close: async ({ trace, request, signal, keepalive }) => parseSuccess(await postJson({ baseUrl, path: `${tracePath(trace)}/close`, body: request, signal, keepalive }), (value) => parseCloseResponse(value, trace, request), "Die lokale Operator-API hat keinen lesbaren Diagnoseabschluss geliefert."),
  }
}
