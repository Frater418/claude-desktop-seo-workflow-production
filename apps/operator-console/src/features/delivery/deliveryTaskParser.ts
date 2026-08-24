import type { DeliveryImplementationTask, DeliveryRole } from "../../generated/api-types"
import { ARTIFACT_ID } from "../../api/deliveryReadModelPrimitives"

const TASK_ID = /^task-[a-z0-9][a-z0-9-]{7,63}$/
const ASSIGNMENT_ID = /^assignment-[a-z0-9][a-z0-9-]{7,63}$/
const NOTION_USER_ID = /^notion-user-[a-z0-9][a-z0-9-]{7,63}$/
const DATE = /^\d{4}-\d{2}-\d{2}$/
const requiredKeys = ["task_id", "assignment_id", "title", "status", "comments", "source_assignee", "priority", "deadline", "role", "dependencies", "artifact_relations"] as const
const knownKeys = new Set([...requiredKeys, "notion_user_id"])

type JsonObject = Readonly<Record<string, unknown>>
type TaskStatus = DeliveryImplementationTask["status"]
type TaskPriority = DeliveryImplementationTask["priority"]

export type DeliveryTaskParseResult =
  | { readonly kind: "valid"; readonly tasks: readonly DeliveryImplementationTask[] }
  | { readonly kind: "invalid"; readonly errors: readonly string[] }

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function taskError(errors: string[], position: number, message: string): void {
  errors.push(`Aufgabe ${position}: ${message}`)
}

function text(record: JsonObject, key: string, position: number, errors: string[]): string | null {
  const value = record[key]
  if (typeof value === "string") return value
  taskError(errors, position, `Das Feld ${key} muss Text enthalten.`)
  return null
}

function identifier(record: JsonObject, key: string, pattern: RegExp, position: number, errors: string[]): string | null {
  const value = text(record, key, position, errors)
  if (value === null) return null
  if (pattern.test(value)) return value
  taskError(errors, position, `Das Feld ${key} enthaelt keine gueltige Kennung.`)
  return null
}

function status(record: JsonObject, position: number, errors: string[]): TaskStatus | null {
  const value = text(record, "status", position, errors)
  switch (value) {
    case "not_started": return value
    case "in_progress": return value
    case "blocked": return value
    case "done": return value
    default:
      taskError(errors, position, "Der Status ist ungueltig.")
      return null
  }
}

function priority(record: JsonObject, position: number, errors: string[]): TaskPriority | null {
  const value = text(record, "priority", position, errors)
  switch (value) {
    case "low": return value
    case "medium": return value
    case "high": return value
    default:
      taskError(errors, position, "Die Prioritaet ist ungueltig.")
      return null
  }
}

function role(record: JsonObject, position: number, errors: string[]): DeliveryRole | null {
  const value = text(record, "role", position, errors)
  switch (value) {
    case "copywriter": return value
    case "developer": return value
    default:
      taskError(errors, position, "Die Rolle muss copywriter oder developer sein.")
      return null
  }
}

function deadline(record: JsonObject, position: number, errors: string[]): string | null {
  const value = text(record, "deadline", position, errors)
  if (value === null) return null
  const date = new Date(`${value}T00:00:00Z`)
  if (DATE.test(value) && !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value) return value
  taskError(errors, position, "Die Frist muss ein gueltiges RFC3339-Datum sein.")
  return null
}

function relations(record: JsonObject, key: "dependencies" | "artifact_relations", pattern: RegExp, label: string, position: number, errors: string[]): readonly string[] {
  const value = record[key]
  if (!Array.isArray(value)) {
    taskError(errors, position, `Das Feld ${key} muss eine Liste sein.`)
    return []
  }
  const identifiers: string[] = []
  for (const item of value) {
    if (typeof item === "string" && pattern.test(item)) identifiers.push(item)
    else taskError(errors, position, `Das Feld ${key} enthaelt keine gueltige Kennung.`)
  }
  if (new Set(identifiers).size !== identifiers.length) taskError(errors, position, `Das Feld ${key} enthaelt doppelte ${label}.`)
  return identifiers
}

function notionUser(record: JsonObject, position: number, errors: string[]): string | null | undefined {
  const value = record["notion_user_id"]
  if (value === undefined || value === null) return value
  if (typeof value === "string" && NOTION_USER_ID.test(value)) return value
  taskError(errors, position, "Das Feld notion_user_id enthaelt keine gueltige Notion-Benutzerkennung.")
  return undefined
}

function hasClosedFields(record: JsonObject, position: number, errors: string[]): void {
  for (const key of Object.keys(record)) if (!knownKeys.has(key)) taskError(errors, position, `Das JSON enthaelt ein unbekanntes Feld ${key}.`)
  for (const key of requiredKeys) if (!(key in record)) taskError(errors, position, `Das Pflichtfeld ${key} fehlt.`)
}

function task(value: unknown, position: number, errors: string[]): DeliveryImplementationTask | null {
  if (!isObject(value)) {
    taskError(errors, position, "Der Eintrag muss ein JSON-Objekt sein.")
    return null
  }
  const before = errors.length
  hasClosedFields(value, position, errors)
  const taskId = identifier(value, "task_id", TASK_ID, position, errors)
  const assignmentId = identifier(value, "assignment_id", ASSIGNMENT_ID, position, errors)
  const title = text(value, "title", position, errors)
  if (title !== null && title.trim() === "") taskError(errors, position, "Der Titel darf nicht leer sein.")
  const taskStatus = status(value, position, errors)
  const comments = text(value, "comments", position, errors)
  const sourceAssignee = text(value, "source_assignee", position, errors)
  const taskPriority = priority(value, position, errors)
  const taskDeadline = deadline(value, position, errors)
  const taskRole = role(value, position, errors)
  const dependencies = relations(value, "dependencies", TASK_ID, "Abhaengigkeiten", position, errors)
  const artifactRelations = relations(value, "artifact_relations", ARTIFACT_ID, "Artefaktbeziehungen", position, errors)
  const notionUserId = notionUser(value, position, errors)
  if (errors.length !== before || taskId === null || assignmentId === null || title === null || taskStatus === null || comments === null || sourceAssignee === null || taskPriority === null || taskDeadline === null || taskRole === null) return null
  if (notionUserId === undefined) return { task_id: taskId, assignment_id: assignmentId, title, status: taskStatus, comments, source_assignee: sourceAssignee, priority: taskPriority, deadline: taskDeadline, role: taskRole, dependencies, artifact_relations: artifactRelations }
  return { task_id: taskId, assignment_id: assignmentId, title, status: taskStatus, comments, source_assignee: sourceAssignee, priority: taskPriority, deadline: taskDeadline, role: taskRole, dependencies, artifact_relations: artifactRelations, notion_user_id: notionUserId }
}

export function parseDeliveryImplementationTasks(value: string): DeliveryTaskParseResult {
  let parsed: unknown
  try {
    parsed = JSON.parse(value)
  } catch (error) {
    if (error instanceof SyntaxError) return { kind: "invalid", errors: ["Die Notion-Implementierungsaufgaben enthalten kein gueltiges JSON."] }
    throw error
  }
  if (!Array.isArray(parsed) || parsed.length === 0) return { kind: "invalid", errors: ["Die Notion-Implementierungsaufgaben muessen eine nicht leere JSON-Liste sein."] }
  const errors: string[] = []
  const tasks = parsed.map((item, index) => task(item, index + 1, errors)).filter((item): item is DeliveryImplementationTask => item !== null)
  const identifiers = tasks.flatMap((item) => [item.task_id, item.assignment_id])
  if (new Set(identifiers).size !== identifiers.length) errors.push("Aufgaben- oder Zuordnungskennungen muessen ueber alle Implementierungsaufgaben eindeutig sein.")
  if (errors.length > 0) return { kind: "invalid", errors }
  return { kind: "valid", tasks }
}
