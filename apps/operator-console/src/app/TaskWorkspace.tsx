import { useEffect, useMemo, useState } from "react"
import type { TaskRead } from "../api/readModels"
import { taskStatusLabel } from "../api/statusLabels"
import type { OperatorWorkspaceData } from "./useOperatorWorkspace"

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

export function TaskWorkspace({ data }: { readonly data: OperatorWorkspaceData }): JSX.Element {
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

  return <section className="task-layout">
    <section className="work-panel task-queue">
      <div className="work-heading"><div><p className="eyebrow">Aufgaben</p><h2>Aufgabenwarteschlange</h2></div><div className="action-row"><label>Status filtern<select aria-label="Status filtern" value={filters.status} onChange={(event) => updateFilter("status", event.currentTarget.value)}><option value="">Alle Status</option>{filterOptions.status.map((value) => <option key={value} value={value}>{taskStatusLabel(value)}</option>)}</select></label><label>Verantwortung filtern<select aria-label="Verantwortung filtern" value={filters.owner} onChange={(event) => updateFilter("owner", event.currentTarget.value)}><option value="">Alle Verantwortlichen</option>{filterOptions.owner.map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label>Prioritaet filtern<select aria-label="Prioritaet filtern" value={filters.priority} onChange={(event) => updateFilter("priority", event.currentTarget.value)}><option value="">Alle Prioritaeten</option>{filterOptions.priority.map((value) => <option key={value} value={value}>{priorityLabel(value)}</option>)}</select></label><label>Faellig bis<input aria-describedby={deadlineIsInvalid ? "deadline-filter-error" : undefined} aria-invalid={deadlineIsInvalid || undefined} aria-label="Faellig bis" inputMode="numeric" placeholder="JJJJ-MM-TT" type="text" value={filters.deadline} onChange={(event) => updateFilter("deadline", event.currentTarget.value)} />{deadlineIsInvalid ? <span className="input-error" id="deadline-filter-error">Bitte ein gueltiges Datum im Format JJJJ-MM-TT eingeben.</span> : null}</label><label>Schritt filtern<select aria-label="Schritt filtern" value={filters.step} onChange={(event) => updateFilter("step", event.currentTarget.value)}><option value="">Alle Schritte</option>{filterOptions.step.map((value) => <option key={value} value={value}>{value}</option>)}</select></label></div></div>
      <div className="action-row"><button type="button" aria-pressed={sortKey === "priority"} aria-label="Nach Prioritaet sortieren" aria-description={`Aktuell: ${priorityDirection}`} onClick={() => toggleSort("priority")}>Nach Prioritaet sortieren: {priorityDirection}</button><button type="button" aria-pressed={sortKey === "deadline"} aria-label="Nach Faelligkeit sortieren" aria-description={`Aktuell: ${deadlineDirection}`} onClick={() => toggleSort("deadline")}>Nach Faelligkeit sortieren: {deadlineDirection}</button></div>
      {tasks.length === 0 ? <p>{filtersActive ? "Keine Aufgaben entsprechen den aktuellen Filtern." : "Keine Aufgaben vorhanden."}</p> : <div className="task-list" role="list" aria-label="Gefilterte Aufgaben">{tasks.map((task) => <div key={task.taskId} role="listitem"><button className="task-row" type="button" aria-label={task.title} aria-pressed={selected?.taskId === task.taskId} onClick={() => setSelectedId(task.taskId)}><strong className="task-row-title">{task.title}</strong><span className="task-row-metadata"><span>{priorityLabel(task.priority)}</span><span>Schritt {task.stepId}</span><time className="task-row-date" dateTime={task.deadline}>{task.deadline}</time></span></button></div>)}</div>}
    </section>
    <section className="work-panel task-detail"><h2>Aufgabedetail</h2>{selected === undefined ? <p>Keine Aufgabendetails verfuegbar.</p> : <><h3>{selected.title}</h3><dl className="facts"><div><dt>Status</dt><dd>{taskStatusLabel(selected.status)}</dd></div><div><dt>Prioritaet</dt><dd>{priorityLabel(selected.priority)}</dd></div><div><dt>Erforderliche Loesung</dt><dd>{selected.resolution}</dd></div><div><dt>Abhaengigkeit</dt><dd>{selected.dependency}</dd></div><div><dt>Verantwortung</dt><dd>{selected.owner}</dd></div><div><dt>Faelligkeit</dt><dd>{selected.deadline}</dd></div><div><dt>Schritt</dt><dd>{selected.stepId}</dd></div></dl></>}</section>
  </section>
}
