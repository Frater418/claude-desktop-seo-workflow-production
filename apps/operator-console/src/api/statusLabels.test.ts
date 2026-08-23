import { describe, expect, it } from "vitest"
import { gateStatusLabel, integrationModeLabel, runStatusLabel, stepStatusLabel, taskStatusLabel } from "./statusLabels"

describe("canonical status labels", () => {
  it("Given every closed run and step status, when a primary label is requested, then it is German", () => {
    expect(Object.fromEntries((["pending", "in_progress", "awaiting_gate", "approved", "completed", "failed", "superseded"] as const).map((status) => [status, runStatusLabel(status)]))).toEqual({ pending: "Ausstehend", in_progress: "In Bearbeitung", awaiting_gate: "Wartet auf Pruefung", approved: "Freigegeben", completed: "Abgeschlossen", failed: "Fehlgeschlagen", superseded: "Ueberholt" })
    expect(Object.fromEntries((["pending", "in_progress", "awaiting_gate", "approved", "completed", "failed", "superseded"] as const).map((status) => [status, stepStatusLabel(status)]))).toEqual({ pending: "Ausstehend", in_progress: "In Bearbeitung", awaiting_gate: "Wartet auf Pruefung", approved: "Freigegeben", completed: "Abgeschlossen", failed: "Fehlgeschlagen", superseded: "Ueberholt" })
  })

  it("Given every closed gate, task, and integration status, when a primary label is requested, then it is German", () => {
    expect(Object.fromEntries((["passed", "failed", "blocked"] as const).map((status) => [status, gateStatusLabel(status)]))).toEqual({ passed: "Bestanden", failed: "Fehlgeschlagen", blocked: "Blockiert" })
    expect(Object.fromEntries((["open", "in_progress", "waiting_for_input", "resolved", "cancelled"] as const).map((status) => [status, taskStatusLabel(status)]))).toEqual({ open: "Offen", in_progress: "In Bearbeitung", waiting_for_input: "Wartet auf Eingabe", resolved: "Geloest", cancelled: "Abgebrochen" })
    expect(Object.fromEntries((["simulated", "live"] as const).map((status) => [status, integrationModeLabel(status)]))).toEqual({ simulated: "Simulation", live: "Live" })
  })
})
