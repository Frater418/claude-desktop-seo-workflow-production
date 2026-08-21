# Heartweb Admin Operator Console Design System

## 1. Atmosphere and Identity

The console is a quiet, precise local work surface for one Heartweb Admin Operator. It must make the active project, legal next action, blocker, and current evidence legible before secondary detail. Its signature is functional depth: a dark workspace with compact teal guidance, structured reading areas, and no presentation-only dashboard surface. Linear is referenced only for dense task and status handling. Notion and CMS patterns are referenced only for readable structured content and editing. Their branding, typography, colors, and marketing patterns are not copied.

## 2. Color

| Role | Token | Value | Usage |
| --- | --- | --- | --- |
| Primary surface | `--color-background` | `#10161d` | App background and recessed work areas |
| Panel surface | `--color-panel` | `#17212a` | Navigation, header, work panels, drawers |
| Selected surface | `--color-selected` | `#1f3840` | Active task, row, or navigation state |
| Primary text | `--color-text` | `#e8edf2` | Headings and primary operator information |
| Secondary text | `--color-copy` | `#c9d4dc` | Body content and structured reading |
| Muted text | `--color-muted` | `#9baab7` | Metadata and secondary labels |
| Border | `--color-border` | `#31404c` | Quiet structural separators |
| Strong border | `--color-border-strong` | `#41515d` | Active and durable boundaries |
| Action accent | `--color-accent` | `#65d5ba` | Legal actions, focus, selected navigation |
| Accent text | `--color-accent-soft` | `#82d8c4` | Links and secondary active guidance |
| Warning | `--color-warning` | `#f2ce7f` | Review waits, due attention, and blockers |
| Warning surface | `--color-warning-surface` | `#3d3218` | Blocker and confirmation context |
| Error | `--color-error` | `#df7f72` | Illegal actions and failed validation |
| Sideflow | `--color-sideflow` | `#b7a1e8` | The separate 3b not-due workflow sideflow |

Only these semantic colors may appear in application CSS. Accent color communicates action and selection, never decoration.

## 3. Typography

- Primary stack: `"Segoe UI", Aptos, ui-sans-serif, system-ui, sans-serif`.
- Technical stack: `ui-monospace, SFMono-Regular, Menlo, monospace`, only inside the technical-details disclosure.
- Page title: `clamp(1.55rem, 2.5vw, 2.25rem)`, weight 700, tight tracking.
- Section title: `1.15rem`, weight 700.
- Detail title: `0.92rem`, weight 700.
- Body copy: `0.84rem`, line height `1.45`.
- Metadata: `0.82rem`; compact labels: `0.76rem`.
- Data values use `font-variant-numeric: tabular-nums` where comparison matters.
- Visible copy is plain German. IDs, hashes, raw JSON, routes, providers, model data, and context internals are technical details only.

## 4. Spacing and Layout

- Base unit: 4px. Tokens: `--space-1` 4px, `--space-2` 8px, `--space-3` 12px, `--space-4` 16px, `--space-5` 20px, and `--space-6` 24px.
- Functional radii: `--radius-sm` 4px and `--radius-panel` 6px. No decorative pill or large-card radius scale.
- Desktop is primary: a `fixed-sidenav-shell` has left navigation, a header and scrollable task workspace, collapsible evidence aside, and persistent action footer.
- Scroll ownership: the shell body owns document-level work scrolling. The task queue may own its own named list scroll on desktop. No unnamed nested scrolling.
- Main work uses a `list-detail` or `sidebar` primitive with `min-block-size: 0`; content grids use `minmax(min(..., 100%), 1fr)` to avoid mobile overflow.
- At 850px the evidence panel moves below work or becomes a disclosure. At 520px and 390px, the left navigation becomes an accessible horizontal command row, the project header becomes a stack, and review, status, and persistent actions remain available. Dense editors become one readable column.

## 5. Components

### Application shell
- **Structure**: `header`, `nav`, `main`, optional `aside`, persistent `footer` action bar.
- **Variants**: project workspace, intake workspace, unavailable API state.
- **States**: loading, empty, API error, selected navigation, collapsed evidence.
- **Accessibility**: German landmark labels, skip link, current navigation with `aria-current`, keyboard-reachable controls, visible focus.
- **Layout**: `fixed-sidenav-shell`; main workspace is the scroll owner.

### Project header and status strip
- **Structure**: project name, customer, active step, progress, blocker count, owner, next action.
- **States**: current, blocked, waiting for review, not due.
- **Accessibility**: status is text as well as color; long names wrap safely.

### Compact task queue
- **Structure**: filter controls, sortable column headers, task rows, selected detail.
- **States**: loading, empty, selected, overdue, blocked.
- **Accessibility**: buttons describe sort direction; selected task uses `aria-current` or `aria-pressed`; filters have visible labels.
- **Layout**: `list-detail`, retaining the queue when detail changes. This is the only Linear-inspired density pattern.

### Structured artifact editor
- **Structure**: artifact selector, readable content, labelled editor, revision history, diff, validation result.
- **States**: loading, editable draft, saving, immutable saved revision, validation error.
- **Accessibility**: native labelled textarea, explicit immutable-save explanation, technical content only on disclosure.
- **Layout**: readable measure for document content, with the editor as the active work surface. This is the only Notion/CMS-inspired reading and editing pattern.

### Review confirmation
- **Structure**: selected action, consequence preview, blocker and remediation, confirmation control, canonical readback state.
- **States**: previewing, disallowed, awaiting explicit confirmation, accepted, replayed, readback failure.
- **Accessibility**: consequence uses a polite live region; confirmation is a separate deliberate button; disabled actions include exact German remediation text.

### Evidence panel and technical details
- **Structure**: evidence, findings, dependencies, revision lineage, integration labels, closed technical disclosure.
- **States**: expanded, collapsed, empty.
- **Accessibility**: native `details` for technical data; no raw JSON on the primary surface.

### Persistent action area
- **Structure**: legal next action first, followed by context-sensitive secondary actions.
- **States**: enabled, loading, blocked with exact remediation, readback pending.
- **Accessibility**: actions remain keyboard reachable and do not claim success before canonical GET readback.

## 6. Motion and Interaction

- Interaction feedback is limited to 120ms to 200ms color, opacity, and transform transitions for buttons, selected rows, and the evidence panel.
- The active state may use `translateY(1px)` only as press feedback.
- No decorative animation, auto-playing status motion, or animated layout dimensions.
- `prefers-reduced-motion: reduce` disables nonessential transitions.

## 7. Depth and Surface

The depth strategy is borders plus tonal shift. Primary work is separated by the existing background and panel colors with 1px borders. Only modal-like confirmation contexts may use the existing subtle layered shadow. Generic card grids are not a layout primitive. A panel exists only for a workspace, editor, evidence group, or action consequence that needs an independent task boundary.

## 8. Accessibility Constraints and Accepted Debt

### Constraints

- Target: WCAG 2.2 AA. Text contrast, visible focus, semantic landmarks, native form labels, keyboard operation, and text alternatives are required.
- Plain German labels must describe the next action, blocker, and remediation without relying on color or technical vocabulary.
- A 390px viewport must support project status, task detail, review confirmation, and persistent actions without horizontal scrolling of primary content.
- Touch targets remain at least 40px high where the available layout allows it.
- Simulation is labelled honestly when returned by the Local Operator API. No demo or fabricated fallback appears.

### Accepted Debt

| Item | Location | Why accepted | Owner and exit |
| --- | --- | --- | --- |
| React dev-tooling packages | Project tooling | The task requires preserving the lockfile and existing package stack. `react-grab`, `react-scan`, and `react-doctor` are not present and will not be added. | Reconsider in a dedicated tooling package with approved dependency update. |
| Delivery Center | Navigation destination | Sprint 5E delivery APIs are explicitly out of scope for this package. | Enable only when Sprint 5E contracts and APIs are approved. |
