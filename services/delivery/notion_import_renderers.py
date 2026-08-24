from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Final


PACK_ROOT: Final = "notion-import"


@dataclass(frozen=True, slots=True)
class NotionImportColumn:
    name: str
    property_type: str
    authority: str


@dataclass(frozen=True, slots=True)
class NotionImportCsvContract:
    file_name: str
    collection: str | None
    columns: tuple[NotionImportColumn, ...]


def _columns(*values: tuple[str, str, str]) -> tuple[NotionImportColumn, ...]:
    return tuple(NotionImportColumn(*value) for value in values)


CSV_CONTRACTS: Final = (
    NotionImportCsvContract("projects.csv", "project_rows", _columns(("record_type", "Select", "Core import classification, read-only"), ("customer_external_id", "Text", "Core customer binding, read-only"), ("external_id", "Text", "Core stable ID, read-only"), ("tenant_id", "Text", "Core scope, read-only"), ("project_id", "Text", "Core scope, read-only"), ("source_sha256", "Text", "Core provenance, read-only"))),
    NotionImportCsvContract("tasks.csv", "task_rows", _columns(("external_id", "Text", "Core stable ID, read-only"), ("tenant_id", "Text", "Core scope, read-only"), ("project_id", "Text", "Core scope, read-only"), ("task_class", "Select", "Core classification, read-only"), ("title", "Title", "Core history read-only; Notion implementation editable"), ("history_only", "Checkbox", "Core history marker, read-only"), ("status", "Status", "Notion implementation editable"), ("comments", "Rich text", "Notion implementation editable"), ("assignee", "Person", "Notion implementation editable"), ("priority", "Select", "Notion implementation editable"), ("deadline", "Date", "Notion implementation editable"), ("core_effect", "Select", "Core boundary marker, read-only"))),
    NotionImportCsvContract("assignments.csv", "assignment_rows", _columns(("external_id", "Text", "Core stable ID, read-only"), ("task_external_id", "Relation to Tasks", "Core task binding, read-only"), ("assignee", "Person", "Notion implementation editable"))),
    NotionImportCsvContract("artifacts.csv", "artifact_rows", _columns(("external_id", "Text", "Core stable ID, read-only"), ("project_external_id", "Relation to Projects", "Core project binding, read-only"), ("tenant_id", "Text", "Core scope, read-only"), ("project_id", "Text", "Core scope, read-only"), ("content_sha256", "Text", "Core content provenance, read-only"), ("revision", "Number", "Core revision, read-only"), ("relative_path", "Text", "Core artifact location, read-only"), ("role", "Select", "Core deliverable role, read-only"), ("read_only", "Checkbox", "Core authority marker, read-only"))),
    NotionImportCsvContract("reviews.csv", "review_rows", _columns(("external_id", "Text", "Core stable ID, read-only"), ("project_external_id", "Relation to Projects", "Core project binding, read-only"), ("artifact_external_id", "Relation to Artifacts", "Core artifact binding, read-only"), ("source_sha256", "Text", "Core provenance, read-only"), ("read_only", "Checkbox", "Core authority marker, read-only"))),
    NotionImportCsvContract("approvals.csv", "approval_rows", _columns(("external_id", "Text", "Core canonical approval ID, read-only"), ("project_external_id", "Relation to Projects", "Core project binding, read-only"), ("artifact_external_id", "Relation to Artifacts", "Core release binding, read-only"), ("source_sha256", "Text", "Core provenance, read-only"), ("read_only", "Checkbox", "Core authority marker, read-only"))),
    NotionImportCsvContract("blockers.csv", "blocker_rows", _columns(("external_id", "Text", "Core stable ID, read-only"), ("project_external_id", "Relation to Projects", "Core project binding, read-only"), ("artifact_external_id", "Relation to Artifacts", "Core artifact binding, read-only"), ("source_sha256", "Text", "Core provenance, read-only"), ("read_only", "Checkbox", "Core authority marker, read-only"))),
    NotionImportCsvContract("priorities.csv", "priority_rows", _columns(("task_external_id", "Relation to Tasks", "Core task binding, read-only"), ("value", "Select", "Notion implementation editable"))),
    NotionImportCsvContract("deadlines.csv", "deadline_rows", _columns(("task_external_id", "Relation to Tasks", "Core task binding, read-only"), ("value", "Date", "Notion implementation editable"))),
    NotionImportCsvContract("relations.csv", "relations", _columns(("from_record_id", "Relation", "Core relation endpoint, read-only"), ("to_record_id", "Relation", "Core relation endpoint, read-only"), ("relation_type", "Select", "Core relation type, read-only"))),
    NotionImportCsvContract("performance-checkpoints.csv", "performance_checkpoint_rows", _columns(("day_after_publication", "Number", "Core schedule, read-only"), ("released_strategy_artifact_id", "Relation to Artifacts", "Core released strategy binding, read-only"), ("released_plan_artifact_id", "Relation to Artifacts", "Core released plan binding, read-only"), ("publication_registry_record_id", "Text", "Core publication binding, read-only"), ("performance_data_status", "Select", "Core verified-data gate, read-only"))),
    NotionImportCsvContract("USER_MAPPING_TEMPLATE.csv", None, _columns(("assignment_external_id", "Relation to Assignments", "Core assignment binding, read-only"), ("source_assignee", "Rich text", "Core source provenance, read-only"), ("notion_user_id", "Person", "Manual Notion setup"))),
)
CSV_HEADERS: Final = {contract.file_name: (contract.collection, tuple(column.name for column in contract.columns)) for contract in CSV_CONTRACTS if contract.collection is not None}
USER_MAPPING_COLUMNS: Final = tuple(column.name for column in CSV_CONTRACTS[-1].columns)


@dataclass(frozen=True, slots=True)
class RenderedNotionImportFile:
    path: str
    content: bytes
    row_count: int


def render_csv(name: str, headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> RenderedNotionImportFile:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return RenderedNotionImportFile(f"{PACK_ROOT}/{name}", output.getvalue().encode("utf-8"), len(rows))


def render_markdown(name: str, content: str) -> RenderedNotionImportFile:
    text = f"{content.rstrip()}\n"
    return RenderedNotionImportFile(f"{PACK_ROOT}/{name}", text.encode("utf-8"), text.count("\n"))


def import_order() -> RenderedNotionImportFile:
    return render_markdown("IMPORT_ORDER.md", """# Manual Import Order

## Contract Resolution

`projects.csv` imports the customer row before the project row.

The approved Task 4 closed 14-file contract has no separate run, step, escalation, or command files. These remain Core-only in Sprint 5E.

## Import Sequence

1. `projects.csv`
2. `artifacts.csv`
3. `tasks.csv`
4. `assignments.csv`
5. `priorities.csv`
6. `deadlines.csv`
7. `reviews.csv`
8. `approvals.csv`
9. `blockers.csv`
10. `relations.csv`
11. `USER_MAPPING_TEMPLATE.csv`
12. `performance-checkpoints.csv`
13. `PROPERTY_MAPPING.md`
14. `IMPORT_ORDER.md`

""")


def property_mapping(delivery_safe: bool = False) -> RenderedNotionImportFile:
    mapping_rows = "\n".join(f"| {contract.file_name} | {column.name} | {column.property_type} | {column.authority} |" for contract in CSV_CONTRACTS for column in contract.columns)
    return render_markdown("PROPERTY_MAPPING.md", f"""# Manual Import Mode

## Ownership Table

| Surface | Authority | Editable |
| --- | --- | --- |
| Core history and concept provenance | Core | no |
| Notion implementation task fields | Notion | yes |
| Step 3B scheduled checkpoints | Core after verified data | no |

## CSV Property Mappings

| CSV | Column | Notion property type | Authority/editability |
| --- | --- | --- | --- |
{mapping_rows}

## Scheduled Performance Re-entry

{_reentry_notice(delivery_safe)}
""")


def _reentry_notice(delivery_safe: bool) -> str:
    if delivery_safe:
        return "Daily task completion cannot invoke Core. Only future scheduled Step 3B at days 30, 60, and 90 may re-enter Core with released strategy, released plan, publication registry, and verified performance data."
    return "Daily task completion has no Core callback. Only future scheduled Step 3B at days 30, 60, and 90 may re-enter Core with released strategy, released plan, publication registry, and verified performance data."


def user_mapping(rows: tuple[tuple[str, str, str], ...]) -> RenderedNotionImportFile:
    return render_csv("USER_MAPPING_TEMPLATE.csv", USER_MAPPING_COLUMNS, rows)
