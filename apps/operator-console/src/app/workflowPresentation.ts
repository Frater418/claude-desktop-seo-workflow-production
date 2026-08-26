export const workflowSteps = [
  {
    id: "0",
    label: "Projekt-Kickoff",
    result: "Projektmanifest",
    description: "Briefing und Projektgrundlage prüfen, das Projektmanifest erstellen und für die Themenstrategie freigeben.",
  },
  {
    id: "1",
    label: "Themenstrategie",
    result: "Themen- und Pillar-Struktur",
    description: "Relevante Themenfelder, Suchchancen und organische Wettbewerber bestimmen.",
  },
  {
    id: "1b",
    label: "Seitenarchitektur",
    result: "Seiten- und Navigationsstruktur",
    description: "Aus der Themenstrategie eine belastbare Seitenarchitektur entwickeln.",
  },
  {
    id: "1c",
    label: "Seitentemplates",
    result: "Verbindliche Seitenvorlagen",
    description: "Inhaltliche und technische Vorlagen für die geplanten Seitentypen definieren.",
  },
  {
    id: "2",
    label: "Keyword-Evidenz",
    result: "Verifizierte Keyword- und Wettbewerbsdaten",
    description: "Suchbegriffe und Kennzahlen über die freigegebenen Datenanbieter erheben und prüfen.",
  },
  {
    id: "3",
    label: "120-Tage-Plan",
    result: "Priorisierter Produktionsplan",
    description: "Strategie, Evidenz und Kapazität in eine umsetzbare Reihenfolge überführen.",
  },
  {
    id: "4a",
    label: "Copywriter-Briefings",
    result: "Professionelle Redaktionsbriefings",
    description: "Freigegebene Vorgaben und Nachweise für die menschliche Texterstellung aufbereiten.",
  },
  {
    id: "4b",
    label: "Developer-Paket",
    result: "Technische Spezifikationen und Übergabe",
    description: "Implementierungsvorgaben, Dateien und Aufgaben für die Übergabe zusammenstellen.",
  },
] as const

export type WorkflowStepId = (typeof workflowSteps)[number]["id"]
export type WorkflowStepDefinition = (typeof workflowSteps)[number]

export function workflowStep(stepId: string): WorkflowStepDefinition {
  return workflowSteps.find((step) => step.id === stepId) ?? workflowSteps[0]
}

export function workflowStepCode(stepId: string): string {
  return `Schritt ${stepId.toUpperCase()}`
}

export function workflowStepTitle(stepId: string): string {
  const step = workflowStep(stepId)
  return `${workflowStepCode(step.id)}: ${step.label}`
}

export function completedProgress(progress: string): string {
  const match = /^(\d+) von (\d+) Schritten$/.exec(progress)
  return match === null ? progress : `${match[1]} von ${match[2]} abgeschlossen`
}
