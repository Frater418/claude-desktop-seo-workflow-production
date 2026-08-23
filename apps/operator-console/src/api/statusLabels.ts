export type RunStatus = "pending" | "in_progress" | "awaiting_gate" | "approved" | "completed" | "failed" | "superseded"
export type StepStatus = RunStatus
export type GateStatus = "passed" | "failed" | "blocked"
export type TaskStatus = "open" | "in_progress" | "waiting_for_input" | "resolved" | "cancelled"
export type IntegrationMode = "simulated" | "live"

const runStatusLabels = {
  pending: "Ausstehend",
  in_progress: "In Bearbeitung",
  awaiting_gate: "Wartet auf Pruefung",
  approved: "Freigegeben",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
  superseded: "Ueberholt",
} as const satisfies Readonly<Record<RunStatus, string>>

const gateStatusLabels = {
  passed: "Bestanden",
  failed: "Fehlgeschlagen",
  blocked: "Blockiert",
} as const satisfies Readonly<Record<GateStatus, string>>

const taskStatusLabels = {
  open: "Offen",
  in_progress: "In Bearbeitung",
  waiting_for_input: "Wartet auf Eingabe",
  resolved: "Geloest",
  cancelled: "Abgebrochen",
} as const satisfies Readonly<Record<TaskStatus, string>>

const integrationModeLabels = {
  simulated: "Simulation",
  live: "Live",
} as const satisfies Readonly<Record<IntegrationMode, string>>

export function runStatusLabel(status: RunStatus): string {
  return runStatusLabels[status]
}

export function stepStatusLabel(status: StepStatus): string {
  return runStatusLabels[status]
}

export function gateStatusLabel(status: GateStatus): string {
  return gateStatusLabels[status]
}

export function taskStatusLabel(status: TaskStatus): string {
  return taskStatusLabels[status]
}

export function integrationModeLabel(mode: IntegrationMode): string {
  return integrationModeLabels[mode]
}

export function parseRunStatus(value: string): RunStatus | null {
  switch (value) { case "pending": return value; case "in_progress": return value; case "awaiting_gate": return value; case "approved": return value; case "completed": return value; case "failed": return value; case "superseded": return value; default: return null }
}

export function parseGateStatus(value: string): GateStatus | null {
  switch (value) { case "passed": return value; case "failed": return value; case "blocked": return value; default: return null }
}

export function parseTaskStatus(value: string): TaskStatus | null {
  switch (value) { case "open": return value; case "in_progress": return value; case "waiting_for_input": return value; case "resolved": return value; case "cancelled": return value; default: return null }
}

export function parseIntegrationMode(value: string): IntegrationMode | null {
  switch (value) { case "simulated": return value; case "live": return value; default: return null }
}
