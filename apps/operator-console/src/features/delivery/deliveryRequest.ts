import type { DeliveryCreateRequest, DeliveryDraftPolicy, DeliveryImplementationTask, DeliveryRole, DeliveryScope } from "../../generated/api-types"
import { PROJECT_ID, TENANT_ID } from "../../api/deliveryReadModelPrimitives"
import { parseDeliveryImplementationTasks } from "./deliveryTaskParser"

const CUSTOMER_EXTERNAL_ID = /^customer-[a-z0-9][a-z0-9-]{2,63}$/
const POSITIVE_INTEGER = /^[1-9]\d*$/
const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/

type DeliveryRequestRole = Extract<DeliveryRole, "copywriter" | "developer">

export type DeliveryCreateInput = {
  readonly tenantId: string
  readonly projectId: string
  readonly scope: string
  readonly exportSequence: string
  readonly sourceSnapshotRevision: string
  readonly packageRevision: string
  readonly draftInclusionPolicy: string
  readonly selectedRoles: readonly string[]
  readonly customerExternalId: string
  readonly publicationUrls: string
  readonly implementationTasksJson: string
  readonly createdAt: string
}

export type ValidatedDeliveryCreateInput = {
  readonly tenantId: string
  readonly projectId: string
  readonly scope: DeliveryScope
  readonly exportSequence: number
  readonly sourceSnapshotRevision: number
  readonly packageRevision: number
  readonly draftInclusionPolicy: DeliveryDraftPolicy
  readonly selectedRoles: readonly DeliveryRequestRole[]
  readonly customerExternalId: string
  readonly publicationUrls: readonly string[]
  readonly implementationTasks: readonly DeliveryImplementationTask[]
  readonly createdAt: string
}

export type DeliveryCreateInputValidation =
  | { readonly kind: "valid"; readonly input: ValidatedDeliveryCreateInput }
  | { readonly kind: "invalid"; readonly errors: readonly string[] }

export type DeliveryRequestBuildInput = {
  readonly input: ValidatedDeliveryCreateInput
  readonly crypto: Pick<Crypto, "subtle">
}

export type DeliveryRequestRetryInput = DeliveryRequestBuildInput & {
  readonly existingRequest: DeliveryCreateRequest | null
}

function identifier(value: string, pattern: RegExp, label: string, errors: string[]): string | null {
  if (pattern.test(value)) return value
  errors.push(`${label} ist ungueltig.`)
  return null
}

function positiveInteger(value: string, label: string, errors: string[]): number | null {
  if (!POSITIVE_INTEGER.test(value)) {
    errors.push(`${label} muss eine positive ganze Zahl sein.`)
    return null
  }
  const parsed = Number(value)
  if (Number.isSafeInteger(parsed)) return parsed
  errors.push(`${label} ist zu gross.`)
  return null
}

function scope(value: string, errors: string[]): DeliveryScope | null {
  switch (value) {
    case "checkpoint": return value
    case "final": return value
    default:
      errors.push("Der Exportumfang muss checkpoint oder final sein.")
      return null
  }
}

function draftPolicy(value: string, errors: string[]): DeliveryDraftPolicy | null {
  switch (value) {
    case "exclude_drafts": return value
    case "include_explicit_drafts": return value
    default:
      errors.push("Die Entwurfsrichtlinie ist ungueltig.")
      return null
  }
}

function selectedRoles(value: readonly string[], errors: string[]): readonly DeliveryRequestRole[] {
  const roles: DeliveryRequestRole[] = []
  if (value.length === 0) errors.push("Mindestens ein Rollenpaket muss ausgewaehlt sein.")
  for (const item of value) {
    switch (item) {
      case "copywriter":
      case "developer":
        roles.push(item)
        break
      default:
        errors.push("Rollenpakete duerfen nur copywriter oder developer enthalten.")
    }
  }
  if (new Set(roles).size !== roles.length) errors.push("Rollenpakete duerfen nicht doppelt ausgewaehlt werden.")
  return roles.sort()
}

function validTimestamp(value: string, errors: string[]): string | null {
  const calendar = new Date(`${value.slice(0, 10)}T00:00:00Z`)
  const hour = Number(value.slice(11, 13))
  const minute = Number(value.slice(14, 16))
  const second = Number(value.slice(17, 19))
  const offsetHour = value.endsWith("Z") ? 0 : Number(value.slice(-5, -3))
  const offsetMinute = value.endsWith("Z") ? 0 : Number(value.slice(-2))
  if (RFC3339.test(value) && !Number.isNaN(calendar.getTime()) && calendar.toISOString().slice(0, 10) === value.slice(0, 10) && hour <= 23 && minute <= 59 && second <= 59 && offsetHour <= 23 && offsetMinute <= 59) return value
  errors.push("Der Zeitstempel muss ein gueltiger RFC3339-Zeitstempel mit Zeitzone sein.")
  return null
}

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value).protocol === "https:"
  } catch (error) {
    if (error instanceof TypeError) return false
    throw error
  }
}

function publicationUrls(value: string, errors: string[]): readonly string[] {
  const urls = value.split(/\r?\n/).map((item) => item.trim())
  if (urls.length === 0 || urls.some((item) => item === "")) errors.push("Publikations-URLs muessen zeilenweise und nicht leer angegeben werden.")
  for (const url of urls) if (url !== "" && !isHttpsUrl(url)) errors.push("Publikations-URLs muessen gueltige HTTPS-URLs sein.")
  if (new Set(urls).size !== urls.length) errors.push("Publikations-URLs duerfen nicht doppelt vorkommen.")
  return urls
}

export function validateDeliveryCreateInput(value: DeliveryCreateInput): DeliveryCreateInputValidation {
  const errors: string[] = []
  const tenantId = identifier(value.tenantId, TENANT_ID, "Die Mandantenkennung", errors)
  const projectId = identifier(value.projectId, PROJECT_ID, "Die Projektkennung", errors)
  const selectedScope = scope(value.scope, errors)
  const exportSequence = positiveInteger(value.exportSequence, "Die Exportfolge", errors)
  const sourceSnapshotRevision = positiveInteger(value.sourceSnapshotRevision, "Die Quell-Snapshot-Revision", errors)
  const packageRevision = positiveInteger(value.packageRevision, "Die Paketrevision", errors)
  const selectedDraftPolicy = draftPolicy(value.draftInclusionPolicy, errors)
  const roles = selectedRoles(value.selectedRoles, errors)
  const customerExternalId = identifier(value.customerExternalId, CUSTOMER_EXTERNAL_ID, "Die externe Kundenkennung", errors)
  const urls = publicationUrls(value.publicationUrls, errors)
  const createdAt = validTimestamp(value.createdAt, errors)
  const parsedTasks = parseDeliveryImplementationTasks(value.implementationTasksJson)
  if (parsedTasks.kind === "invalid") errors.push(...parsedTasks.errors)
  if (selectedScope === "final" && selectedDraftPolicy !== "exclude_drafts") errors.push("Die Finale Uebergabe verlangt Entwuerfe ausschliessen.")
  if (selectedScope === "final" && (!roles.includes("copywriter") || !roles.includes("developer"))) errors.push("Die Finale Uebergabe verlangt Copywriter und Developer.")
  if (errors.length > 0 || tenantId === null || projectId === null || selectedScope === null || exportSequence === null || sourceSnapshotRevision === null || packageRevision === null || selectedDraftPolicy === null || customerExternalId === null || createdAt === null || parsedTasks.kind === "invalid") return { kind: "invalid", errors }
  return {
    kind: "valid",
    input: {
      tenantId,
      projectId,
      scope: selectedScope,
      exportSequence,
      sourceSnapshotRevision,
      packageRevision,
      draftInclusionPolicy: selectedDraftPolicy,
      selectedRoles: roles,
      customerExternalId,
      publicationUrls: urls,
      implementationTasks: parsedTasks.tasks,
      createdAt,
    },
  }
}

function canonicalSeed(input: ValidatedDeliveryCreateInput): string {
  return `${input.tenantId}\n${input.projectId}\n${input.scope}\n${input.exportSequence}`
}

function hex(value: ArrayBuffer): string {
  return Array.from(new Uint8Array(value), (byte) => byte.toString(16).padStart(2, "0")).join("")
}

async function suffix(seed: string, purpose: string, crypto: Pick<Crypto, "subtle">): Promise<string> {
  const value = new TextEncoder().encode(`${seed}\n${purpose}`)
  return hex(await crypto.subtle.digest("SHA-256", value)).slice(0, 32)
}

export async function buildDeliveryCreateRequest({ input, crypto }: DeliveryRequestBuildInput): Promise<DeliveryCreateRequest> {
  const seed = canonicalSeed(input)
  const [requestSuffix, exportSuffix, packageSuffix, resultSuffix, idempotencySuffix, notionSuffix, publicationSuffix] = await Promise.all([
    suffix(seed, "request", crypto),
    suffix(seed, "export", crypto),
    suffix(seed, "package", crypto),
    suffix(seed, "result", crypto),
    suffix(seed, "idempotency", crypto),
    suffix(seed, "notion", crypto),
    suffix(seed, "publication", crypto),
  ])
  const roles = [...input.selectedRoles].sort()
  const rolePackageRequests = await Promise.all(roles.map(async (role) => ({ role, role_handoff_manifest_id: `role-handoff-${await suffix(seed, `role:${role}`, crypto)}` })))
  return {
    delivery_export_result_id: `delivery-export-result-${resultSuffix}`,
    delivery_package_id: `delivery-package-${packageSuffix}`,
    export_id: `delivery-export-${exportSuffix}`,
    export_request: {
      created_at: input.createdAt,
      delivery_export_request_id: `delivery-export-request-${requestSuffix}`,
      draft_inclusion_policy: input.draftInclusionPolicy,
      idempotency_key: `idem-${idempotencySuffix}`,
      project_id: input.projectId,
      requested_role_packages: roles,
      schema_version: "1.0.0",
      scope: input.scope,
      source_snapshot_revision: input.sourceSnapshotRevision,
      tenant_id: input.tenantId,
    },
    notion_import_request: {
      customer_external_id: input.customerExternalId,
      implementation_tasks: input.implementationTasks,
      notion_import_manifest_id: `notion-import-${notionSuffix}`,
      publication_registry: {
        publication_registry_record_id: `publication-registry-${publicationSuffix}`,
        urls: input.publicationUrls,
      },
    },
    package_revision: input.packageRevision,
    role_package_requests: rolePackageRequests,
  }
}

export async function buildOrReuseDeliveryCreateRequest({ existingRequest, input, crypto }: DeliveryRequestRetryInput): Promise<DeliveryCreateRequest> {
  if (existingRequest !== null) return existingRequest
  return buildDeliveryCreateRequest({ input, crypto })
}
