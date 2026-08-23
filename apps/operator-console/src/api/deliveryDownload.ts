import type { ApiOperationMap } from "../generated/api-types"
import { OperatorApiError } from "./operatorApiError"

type DeliveryDownloadBlob = ApiOperationMap["downloadDeliveryExport"]["responses"]["200"]

export type DeliveryDownload = { readonly blob: DeliveryDownloadBlob; readonly filename: string; readonly etag: string }

function isErrorEnvelope(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function filenameFromDisposition(value: string, status: number): string {
  const extended = /(?:^|;)\s*filename\*=UTF-8''([^;]+)/i.exec(value)
  const regular = /(?:^|;)\s*filename=(?:"([^"]*)"|([^;\s]+))/i.exec(value)
  let filename: string | undefined
  if (extended !== null) {
    const encoded = extended[1]
    if (encoded === undefined) throw new OperatorApiError({ kind: "unparseable", status, message: "Die lokale Operator-API hat keinen sicheren ZIP-Dateinamen geliefert." })
    try { filename = decodeURIComponent(encoded) } catch (error) {
      if (error instanceof URIError) throw new OperatorApiError({ kind: "unparseable", status, message: "Die lokale Operator-API hat keinen sicheren ZIP-Dateinamen geliefert." })
      throw error
    }
  } else if (regular !== null) filename = regular[1] ?? regular[2]
  if (filename === undefined || !/^[A-Za-z0-9][A-Za-z0-9._-]*\.zip$/.test(filename)) throw new OperatorApiError({ kind: "unparseable", status, message: "Die lokale Operator-API hat keinen sicheren ZIP-Dateinamen geliefert." })
  return filename
}

export async function requestDeliveryDownload(baseUrl: string, path: string, signal: AbortSignal): Promise<DeliveryDownload> {
  const url = baseUrl === "" ? path : `${baseUrl.replace(/\/$/, "")}${path}`
  let response: Response
  try { response = await fetch(url, { method: "GET", signal }) } catch (error) {
    if (error instanceof TypeError) throw new OperatorApiError({ kind: "network", status: 0, message: "Die lokale Operator-API ist nicht erreichbar." })
    throw error
  }
  if (!response.ok) {
    let payload: unknown
    try { payload = await response.json() } catch (error) {
      if (error instanceof SyntaxError) throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat ungueltiges JSON geliefert." })
      throw error
    }
    const message = isErrorEnvelope(payload) && typeof payload["message"] === "string" ? payload["message"] : `Die lokale Operator-API hat HTTP ${response.status} geliefert.`
    throw new OperatorApiError({ kind: "http", status: response.status, message })
  }
  const contentDisposition = response.headers.get("Content-Disposition")
  const etag = response.headers.get("ETag")
  if (contentDisposition === null || contentDisposition === "" || etag === null || etag === "") throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat unvollstaendige ZIP-Metadaten geliefert." })
  let blob: DeliveryDownloadBlob
  try { blob = await response.blob() } catch (error) {
    if (error instanceof TypeError) throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat kein lesbares ZIP geliefert." })
    throw error
  }
  if (blob.size < 1) throw new OperatorApiError({ kind: "unparseable", status: response.status, message: "Die lokale Operator-API hat ein leeres ZIP geliefert." })
  return { blob, filename: filenameFromDisposition(contentDisposition, response.status), etag }
}
