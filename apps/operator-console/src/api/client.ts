import type { ApiOperationMap, DataEnvelope } from "../generated/api-types"

type ReadyResponse = ApiOperationMap["readyz"]["responses"]["200"]
type ProjectListResponse = ApiOperationMap["listProjects"]["responses"]["200"]

type OperatorApiClientConfig = {
  readonly baseUrl: string
  readonly tenantId: string
}

type OperatorApiErrorOptions = {
  readonly kind: "http" | "network" | "unparseable"
  readonly status: number
  readonly message: string
}

export class OperatorApiError extends Error {
  public readonly kind: OperatorApiErrorOptions["kind"]
  public readonly status: number

  public constructor(options: OperatorApiErrorOptions) {
    super(options.message)
    this.name = "OperatorApiError"
    this.kind = options.kind
    this.status = options.status
  }
}

export type OperatorApiClient = {
  readonly readyz: (signal: AbortSignal) => Promise<ReadyResponse>
  readonly listProjects: (signal: AbortSignal) => Promise<ProjectListResponse>
}

function isDataEnvelope(value: unknown): value is DataEnvelope {
  return typeof value === "object" && value !== null && "data" in value
}

function requestUrl(baseUrl: string, path: string): string {
  return baseUrl === "" ? path : `${baseUrl.replace(/\/$/, "")}${path}`
}

async function getEnvelope(baseUrl: string, path: string, signal: AbortSignal): Promise<DataEnvelope> {
  let response: Response

  try {
    response = await fetch(requestUrl(baseUrl, path), { method: "GET", signal })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new OperatorApiError({
        kind: "network",
        status: 0,
        message: "The local Operator API could not be reached.",
      })
    }
    throw error
  }

  if (!response.ok) {
    throw new OperatorApiError({
      kind: "http",
      status: response.status,
      message: `The local Operator API returned HTTP ${response.status}.`,
    })
  }

  try {
    const payload: unknown = await response.json()
    if (!isDataEnvelope(payload)) {
      throw new OperatorApiError({
        kind: "unparseable",
        status: response.status,
        message: "The local Operator API returned an unparseable response envelope.",
      })
    }
    return payload
  } catch (error) {
    if (error instanceof OperatorApiError) {
      throw error
    }
    if (error instanceof SyntaxError) {
      throw new OperatorApiError({
        kind: "unparseable",
        status: response.status,
        message: "The local Operator API returned invalid JSON.",
      })
    }
    throw error
  }
}

export function createOperatorApiClient(config: OperatorApiClientConfig): OperatorApiClient {
  const projectPath = `/v1/tenants/${encodeURIComponent(config.tenantId)}/projects`

  return {
    readyz: (signal) => getEnvelope(config.baseUrl, "/readyz", signal),
    listProjects: (signal) => getEnvelope(config.baseUrl, projectPath, signal),
  }
}
