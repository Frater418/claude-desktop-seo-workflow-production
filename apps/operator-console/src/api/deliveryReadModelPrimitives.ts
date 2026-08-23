import { OperatorReadModelError } from "./readModels"

export type JsonObject = Readonly<Record<string, unknown>>

export const TENANT_ID = /^tenant-[a-z0-9][a-z0-9-]{2,63}$/
export const PROJECT_ID = /^project-[a-z0-9][a-z0-9-]{2,63}$/
export const EXPORT_ID = /^delivery-export-[a-z0-9][a-z0-9-]{7,63}$/
export const REQUEST_ID = /^delivery-export-request-[a-z0-9][a-z0-9-]{7,63}$/
export const RESULT_ID = /^delivery-export-result-[a-z0-9][a-z0-9-]{7,63}$/
export const PACKAGE_ID = /^delivery-package-[a-z0-9][a-z0-9-]{7,63}$/
export const ROLE_MANIFEST_ID = /^role-handoff-[a-z0-9][a-z0-9-]{7,63}$/
export const NOTION_MANIFEST_ID = /^notion-import-[a-z0-9][a-z0-9-]{7,63}$/
export const ARTIFACT_ID = /^artifact-[a-z0-9][a-z0-9-]{7,63}$/
export const SOURCE_RECORD_ID = /^(?:project|run|artifact|release|task|assignment|review|approval|blocker|report)-[a-z0-9][a-z0-9-]{2,63}$/

const MANIFEST_ID = /^(?:role-handoff|notion-import|delivery-package)-[a-z0-9][a-z0-9-]{7,63}$/
const SHA256 = /^[a-f0-9]{64}$/
const SAFE_RELATIVE_PATH = /^[A-Za-z0-9][A-Za-z0-9._/-]*$/
const RFC3339 = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$/

export function fail(message: string): never {
  throw new OperatorReadModelError(`Die lokale Operator-API hat ${message} geliefert.`)
}

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function object(value: unknown, subject: string): JsonObject {
  if (isJsonObject(value)) return value
  return fail(`kein lesbares ${subject}`)
}

export function exactKeys(value: JsonObject, allowed: readonly string[], subject: string): void {
  const allowedKeys = new Set(allowed)
  for (const key of Object.keys(value)) if (!allowedKeys.has(key)) fail(`ein unbekanntes Feld ${key} in ${subject}`)
}

export function stringAt(value: JsonObject, key: string, subject: string): string {
  const field = value[key]
  if (typeof field === "string" && field !== "") return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

export function identifierAt(value: JsonObject, key: string, pattern: RegExp, subject: string): string {
  const identifier = stringAt(value, key, subject)
  if (pattern.test(identifier)) return identifier
  return fail(`keine gueltige Kennung ${key} in ${subject}`)
}

export function booleanAt(value: JsonObject, key: string, subject: string): boolean {
  const field = value[key]
  if (typeof field === "boolean") return field
  return fail(`kein lesbares Feld ${key} in ${subject}`)
}

export function positiveIntegerAt(value: JsonObject, key: string, subject: string): number {
  const field = value[key]
  if (typeof field === "number" && Number.isInteger(field) && field >= 1) return field
  return fail(`kein positiver ganzzahliger Wert ${key} in ${subject}`)
}

export function list(value: unknown, subject: string): readonly unknown[] {
  if (Array.isArray(value)) return value
  return fail(`keine lesbare Liste fuer ${subject}`)
}

export function sha256At(value: JsonObject, key: string, subject: string): string {
  const hash = stringAt(value, key, subject)
  if (SHA256.test(hash)) return hash
  return fail(`kein gueltiges SHA-256-Feld ${key} in ${subject}`)
}

export function nullableSha256At(value: JsonObject, key: string, subject: string): string | null {
  const field = value[key]
  if (field === null) return null
  if (typeof field === "string" && SHA256.test(field)) return field
  return fail(`kein gueltiges SHA-256-Feld ${key} in ${subject}`)
}

function capture(match: RegExpExecArray, index: number, subject: string): number {
  const value = match[index]
  if (value === undefined) return fail(`keinen RFC3339-Wert in ${subject}`)
  return Number(value)
}

export function rfc3339At(value: JsonObject, key: string, subject: string): string {
  const timestamp = stringAt(value, key, subject)
  const match = RFC3339.exec(timestamp)
  if (match === null) return fail(`keinen RFC3339-Zeitstempel ${key} in ${subject}`)
  const year = capture(match, 1, subject)
  const month = capture(match, 2, subject)
  const day = capture(match, 3, subject)
  const hour = capture(match, 4, subject)
  const minute = capture(match, 5, subject)
  const second = capture(match, 6, subject)
  const calendar = new Date(Date.UTC(year, month - 1, day))
  if (year < 1 || month < 1 || month > 12 || day < 1 || calendar.getUTCFullYear() !== year || calendar.getUTCMonth() !== month - 1 || calendar.getUTCDate() !== day || hour > 23 || minute > 59 || second > 59) return fail(`keinen RFC3339-Zeitstempel ${key} in ${subject}`)
  if (match[7] !== undefined && (capture(match, 8, subject) > 23 || capture(match, 9, subject) > 59)) return fail(`keinen RFC3339-Zeitstempel ${key} in ${subject}`)
  return timestamp
}

export function safeRelativePathAt(value: JsonObject, key: string, subject: string): string {
  const path = stringAt(value, key, subject)
  if (SAFE_RELATIVE_PATH.test(path) && !path.includes("//") && !path.split("/").some((part) => part === "." || part === "..")) return path
  return fail(`keinen sicheren relativen Pfad ${key} in ${subject}`)
}

export function nullableSafeRelativePathAt(value: JsonObject, key: string, subject: string): string | null {
  const field = value[key]
  if (field === null) return null
  if (typeof field === "string") return safeRelativePathAt(value, key, subject)
  return fail(`keinen sicheren relativen Pfad ${key} in ${subject}`)
}

export function optionalNullableSafeRelativePathAt(value: JsonObject, key: string, subject: string): string | null | undefined {
  const field = value[key]
  if (field === undefined || field === null) return field
  if (typeof field === "string") return safeRelativePathAt(value, key, subject)
  return fail(`keinen sicheren relativen Pfad ${key} in ${subject}`)
}

export function routeIdentity(value: JsonObject, subject: string, tenantId: string, projectId: string): { readonly tenantId: string; readonly projectId: string } {
  const actualTenantId = identifierAt(value, "tenant_id", TENANT_ID, subject)
  const actualProjectId = identifierAt(value, "project_id", PROJECT_ID, subject)
  if (actualTenantId !== tenantId || actualProjectId !== projectId) return fail(`eine ungueltige Routenbindung in ${subject}`)
  return { tenantId: actualTenantId, projectId: actualProjectId }
}

export function manifestIdentifierAt(value: JsonObject, key: string, subject: string): string {
  return identifierAt(value, key, MANIFEST_ID, subject)
}

export function requireUnique(values: readonly string[], subject: string): void {
  if (new Set(values).size !== values.length) fail(`doppelte Werte in ${subject}`)
}
