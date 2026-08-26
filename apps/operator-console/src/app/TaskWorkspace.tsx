import { useEffect, useMemo, useState } from "react"
import type { TaskRead } from "../api/readModels"
import { taskStatusLabel } from "../api/statusLabels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"
import { workflowStepTitle } from "./workflowPresentation"

type SortKey = "priority" | "deadline"
type SortDirection = "ascending" | "descending"
type TaskFilters = { readonly status: string; readonly owner: string; readonly priority: string; readonly deadline: string; readonly step: string }

const priorityRanks: Readonly<Record<string, number>> = { critical: 0, kritisch: 0, high: 1, hoch: 1, medium: 2, mittel: 2, normal: 2, low: 3, niedrig: 3 }
const priorityLabels: Readonly<Record<string, string>> = { critical: "Kritisch", kritisch: "Kritisch", high: "Hoch", hoch: "Hoch", medium: "Mittel", mittel: "Mittel", normal: "Mittel", low: "Niedrig", niedrig: "Niedrig" }

function options<T extends string>(tasks: readonly TaskRead[], value: (task: TaskRead) => T): readonly T[] {
  return [...new Set(tasks.map(value))].sort((left, right) => left.localeCompare(right, "de"))
}

function priorityRank(priority: string): number {
  return priorityRanks[priority] ?? 3
}

function priorityLabel(priority: string): string {
  return priorityLabels[priority] ?? priority
}

function deadlineFilter(value: string): string | null {
  if (value === "") return ""
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const parsed = new Date(`${value}T00:00:00Z`)
  return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value ? null : value
}

function sortedTasks(tasks: readonly TaskRead[], key: SortKey, direction: SortDirection): readonly TaskRead[] {
  const factor = direction === "ascending" ? 1 : -1
  return [...tasks].sort((left, right) => {
    const compared = key === "priority" ? priorityRank(left.priority) - priorityRank(right.priority) : left.deadline.localeCompare(right.deadline)
    return factor * (compared || left.title.localeCompare(right.title, "de"))
  })
}

export function TaskWorkspace({ data, onOpenWorkflow = () => undefined }: { readonly data: OperatorWorkspaceData; readonly onOpenWorkflow?: () => void }): JSX.Element {
  const [filters, setFilters] = useState<TaskFilters>({ status: "", owner: "", priority: "", deadline: "", step: "" })
  const [sortKey, setSortKey] = useState<SortKey>("priority")
  const [sortDirection, setSortDirection] = useState<SortDirection>("ascending")
  const [selectedId, setSelectedId] = useState("")
  const filterOptions = useMemo(() => ({ status: options(data.tasks, (task) => task.status), owner: options(data.tasks, (task) => task.owner), priority: options(data.tasks, (task) => task.priority), step: options(data.tasks, (task) => task.stepId) }), [data.tasks])
  const selectedDeadline = deadlineFilter(filters.deadline)
  const deadlineIsInvalid = filters.deadline !== "" && selectedDeadline === null
  const tasks = useMemo(() => sortedTasks(data.tasks.filter((task) => (filters.status === "" || task.status === filters.status) && (filters.owner === "" || task.owner === filters.owner) && (filters.priority === "" || task.priority === filters.priority) && (selectedDeadline === "" || selectedDeadline === null || task.deadline <= selectedDeadline) && (filters.step === "" || task.stepId === filters.step)), sortKey, sortDirection), [data.tasks, filters, selectedDeadline, sortDirection, sortKey])

  useEffect(() => {
    if (!tasks.some((task) => task.taskId === selectedId)) setSelectedId(tasks.at(0)?.taskId ?? "")
  }, [selectedId, tasks])

  const selected = tasks.find((task) => task.taskId === selectedId) ?? tasks.at(0)
  const updateFilter = (field: keyof TaskFilters, value: string): void => setFilters((current) => ({ ...current, [field]: value }))
  const toggleSort = (key: SortKey): void => {
    if (key === sortKey) setSortDirection((current) => current === "ascending" ? "descending" : "ascending")
    else {
      setSortKey(key)
      setSortDirection("ascending")
    }
  }
  const priorityDirection = sortKey === "priority" && sortDirection === "descending" ? "niedrigste zuerst" : "hoechste zuerst"
  const deadlineDirection = sortKey === "deadline" && sortDirection === "descending" ? "spaeteste zuerst" : "frueheste zuerst"
  const filtersActive = Object.values(filters).some((value) => value !== "")

  if (data.tasks.length === 0) return <section className="empty-workspace" aria-labelledby="empty-tasks-title">
    <p className="eyebrow">Projektaufgaben</p>
    <h2 id="empty-tasks-title">Aktuell ist keine Aufgabe offen</h2>
    <p>Aufgaben entstehen nur dann, wenn ein Produktionsschritt eine Eingabe, Korrektur oder Entscheidung von dir benötigt. Für dieses Projekt musst du hier im Moment nichts bearbeiten.</p>
    <button className="button-primary" type="button" onClick={onOpenWorkflow}>Zum aktuellen Projektschritt</button>
  </section>

  return <section className="task-page">
    <header className="section-heading">
      <div><p className="eyebrow">Projektaufgaben</p><h2>{data.tasks.length} {data.tasks.length === 1 ? "Aufgabe" : "Aufgaben"}</h2><p>Diese Warteschlange enthält ausschließlich konkrete Eingaben, Korrekturen und Entscheidungen für dieses Projekt.</p></div>
    </header>
    <details className="task-filters">
      <summary>Filter und Sortierung</summary>
      <div className="task-filter-grid">
        <label>Status<select aria-label="Status filtern" value={filters.status} onChange={(event) => updateFilter("status", event.currentTarget.value)}><option value="">Alle Status</option>{filterOptions.status.map((value) => <option key={value} value={value}>{taskStatusLabel(value)}</option>)}</select></label>
        <label>Verantwortung<select aria-label="Verantwortung filtern" value={filters.owner} onChange={(event) => updateFilter("owner", event.currentTarget.value)}><option value="">Alle Verantwortlichen</option>{filterOptions.owner.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label>Priorität<select aria-label="Prioritaet filtern" value={filters.priority} onChange={(event) => updateFilter("priority", event.currentTarget.value)}><option value="">Alle Prioritäten</option>{filterOptions.priority.map((value) => <option key={value} value={value}>{priorityLabel(value)}</option>)}</select></label>
        <label>Fällig bis<input aria-describedby={deadlineIsInvalid ? "deadline-filter-error" : undefined} aria-invalid={deadlineIsInvalid || undefined} aria-label="Faellig bis" inputMode="numeric" placeholder="JJJJ-MM-TT" type="text" value={filters.deadline} onChange={(event) => updateFilter("deadline", event.currentTarget.value)} />{deadlineIsInvalid ? <span className="input-error" id="deadline-filter-error">Bitte ein gültiges Datum im Format JJJJ-MM-TT eingeben.</span> : null}</label>
        <label>Produktionsschritt<select aria-label="Schritt filtern" value={filters.step} onChange={(event) => updateFilter("step", event.currentTarget.value)}><option value="">Alle Schritte</option>{filterOptions.step.map((value) => <option key={value} value={value}>{workflowStepTitle(value)}</option>)}</select></label>
      </div>
      <div className="action-row"><button type="button" aria-pressed={sortKey === "priority"} aria-label="Nach Prioritaet sortieren" aria-description={`Aktuell: ${priorityDirection}`} onClick={() => toggleSort("priority")}>Priorität: {priorityDirection}</button><button type="button" aria-pressed={sortKey === "deadline"} aria-label="Nach Faelligkeit sortieren" aria-description={`Aktuell: ${deadlineDirection}`} onClick={() => toggleSort("deadline")}>Fälligkeit: {deadlineDirection}</button></div>
    </details>
    {tasks.length === 0 && filtersActive ? <section className="filtered-empty"><p>Keine Aufgabe entspricht den aktuellen Filtern.</p></section> : <section className="task-layout">
      <section className="task-queue"><div className="task-list" role="list" aria-label="Gefilterte Aufgaben">{tasks.map((task) => <div key={task.taskId} role="listitem"><button className="task-row" type="button" aria-label={task.title} aria-pressed={selected?.taskId === task.taskId} onClick={() => setSelectedId(task.taskId)}><strong className="task-row-title">{task.title}</strong><span className="task-row-metadata"><span>{priorityLabel(task.priority)}</span><span>{workflowStepTitle(task.stepId)}</span><time className="task-row-date" dateTime={task.deadline}>{task.deadline}</time></span></button></div>)}</div></section>
      <section className="task-detail" aria-labelledby="task-detail-title"><p className="eyebrow">Ausgewählte Aufgabe</p><h2 id="task-detail-title">{selected?.title}</h2>{selected === undefined ? null : <><dl className="facts"><div><dt>Status</dt><dd>{taskStatusLabel(selected.status)}</dd></div><div><dt>Priorität</dt><dd>{priorityLabel(selected.priority)}</dd></div><div><dt>Erforderliche Lösung</dt><dd>{selected.resolution}</dd></div><div><dt>Abhängigkeit</dt><dd>{selected.dependency}</dd></div><div><dt>Verantwortung</dt><dd>{selected.owner}</dd></div><div><dt>Fälligkeit</dt><dd>{selected.deadline}</dd></div><div><dt>Produktionsschritt</dt><dd>{workflowStepTitle(selected.stepId)}</dd></div></dl><button className="button-secondary" type="button" onClick={onOpenWorkflow}>Im Projektablauf öffnen</button></>}</section>
    </section>}
  </section>
}
