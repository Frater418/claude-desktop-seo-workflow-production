from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.step4a_preflight.validator import validate_step4a_candidate
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> tuple[dict, dict]:
    result = validate_step4a_candidate(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    return bundle["briefing"], bundle["claim_ledger"]


def _evidence_ids(evidence_ids: list[str]) -> str:
    return ", ".join(f"`{evidence_id}`" for evidence_id in sorted(evidence_ids))


def _table_cell(value: str | int | float | bool | None) -> str:
    if value is None:
        rendered = ""
    elif isinstance(value, bool):
        rendered = json.dumps(value)
    else:
        rendered = str(value)
    return rendered.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def _render_table(table: dict) -> list[str]:
    columns = table["columns"]
    lines = [f"**{table['caption']}**", "", f"| {' | '.join(_table_cell(column) for column in columns)} |", f"| {' | '.join('---' for _ in columns)} |"]
    lines.extend(f"| {' | '.join(_table_cell(cell) for cell in row)} |" for row in table["rows"])
    return lines


def _render_entity_table(entities: list[dict]) -> list[str]:
    lines = ["| Name | Wikidata URI | Graph Node ID |", "| --- | --- | --- |"]
    lines.extend(
        f"| {_table_cell(entity['name'])} | {_table_cell(entity['wikidata_uri'])} | {_table_cell(entity['graph_node_id'])} |"
        for entity in sorted(entities, key=lambda entity: (entity["name"], entity["wikidata_uri"], entity["graph_node_id"]))
    )
    return lines


def render_step4a(bundle: dict) -> str:
    briefing, ledger = _validated(bundle)
    frontmatter = {
        "artifact_id": briefing["artifact_id"],
        "claim_ledger_artifact_id": briefing["claim_ledger_artifact_id"],
        "derived": briefing["notion_frontmatter"]["derived"],
        "project_id": briefing["project_id"],
        "projection_schema_version": briefing["notion_frontmatter"]["projection_schema_version"],
    }
    sections = briefing["briefing_sections"]
    language_guidance = sections["definitive_language_guidance"]
    claim_bindings = {binding["claim_id"]: binding for binding in briefing["claim_bindings"]}
    lines = ["---"]
    lines.extend(f"{key}: {json.dumps(value, ensure_ascii=True)}" for key, value in sorted(frontmatter.items()))
    lines.extend(
        [
            "---",
            "",
            "# Content Briefing",
            "",
            "## Briefing Overview",
            "",
            f"- Artifact ID: `{briefing['artifact_id']}`",
            f"- Run ID: `{briefing['run_id']}`",
            f"- Project ID: `{briefing['project_id']}`",
            f"- Deployment ID: `{briefing['deployment_id']}`",
            f"- Step ID: `{briefing['step_id']}`",
            f"- Schema Version: `{briefing['schema_version']}`",
            f"- Revision: {briefing['revision']}",
            f"- Candidate Status: `{briefing['candidate_status']}`",
            f"- Claim Ledger Artifact ID: `{briefing['claim_ledger_artifact_id']}`",
            f"- Source Artifact IDs: {', '.join(f'`{artifact_id}`' for artifact_id in briefing['source_artifact_ids'])}",
            f"- Evidence IDs: {_evidence_ids(briefing['evidence_ids'])}",
            f"- Audience: {sections['audience']}",
            f"- Search Intent: {sections['search_intent']}",
            f"- Primary Keyword: {sections['primary_keyword']}",
            f"- Secondary Keywords: {', '.join(sections['secondary_keywords'])}",
            f"- Content Goal: {sections['content_goal']}",
            f"- Tone: {sections['tone']}",
            "",
            "## Hero Direct Answer",
            "",
            briefing["hero_direct_answer"]["text"],
            "",
            "## Editorial Outline",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in sections["outline"])
    lines.extend(["", "## Semantic Triples", ""])
    for triple in briefing["semantic_triples"]:
        lines.extend(
            [
                f"### `{triple['triple_id']}`",
                "",
                f"- Subject: {triple['subject']}",
                f"- Predicate: {triple['predicate']}",
                f"- Object: {triple['object']}",
                f"- Evidence IDs: {_evidence_ids(triple['evidence_ids'])}",
                "",
            ]
        )
    for container in briefing["evidence_containers"]:
        lines.extend([f"## {container['heading']}", "", f"- Section ID: `{container['section_id']}`", f"- Evidence IDs: {_evidence_ids(container['evidence_ids'])}", "", container["body"], ""])
        if "data_points" in container:
            lines.extend(["### Data Points", ""])
            for data_point in container["data_points"]:
                unit = f" {data_point['unit']}" if "unit" in data_point else ""
                lines.extend([f"- {data_point['label']}: {_table_cell(data_point['value'])}{unit}", f"  - Evidence IDs: {_evidence_ids(data_point['source_evidence_ids'])}"])
        else:
            lines.extend(_render_table(container["table"]))
        lines.append("")
    lines.extend(
        [
            "## Copywriter Guidance",
            "",
            f"- CTA: {sections['cta_guidance']}",
            f"- Internal Links: {sections['internal_link_guidance']}",
            f"- Instructions: {sections['copywriter_instructions']}",
            "",
            "## Definitive Language Guidance",
            "",
            f"- Required: `{json.dumps(language_guidance['required'])}`",
        ]
    )
    lines.extend(f"- Preferred: {pattern}" for pattern in language_guidance["preferred_patterns"])
    lines.extend(f"- Prohibited: {pattern}" for pattern in language_guidance["prohibited_patterns"])
    lines.extend([f"- Rationale: {language_guidance['rationale']}", "", "### Publication Checklist", ""])
    lines.extend(f"- [ ] {item}" for item in sections["publication_checklist"])
    lines.extend(["", "## Entity Bindings", "", "### About", ""])
    lines.extend(_render_entity_table(briefing["entity_bindings"]["about"]))
    lines.extend(["", "### Mentions", ""])
    lines.extend(_render_entity_table(briefing["entity_bindings"]["mentions"]))
    lines.extend(["", "## Claim Ledger", ""])
    for claim in ledger["claims"]:
        lines.extend(
            [
                f"### `{claim['claim_id']}`",
                "",
                claim["text"],
                "",
                f"- Type: `{claim['claim_type']}`",
                f"- Review Status: `{claim['review_status']}`",
                f"- Review Policy: `{claim['reviewer_policy']}`",
                f"- Evidence IDs: {_evidence_ids(claim['evidence_ids'])}",
            ]
        )
        binding = claim_bindings[claim["claim_id"]]
        lines.append(f"- JSON-LD Node: `{binding['graph_node_id']}`")
        if "property_path" in binding:
            lines.append(f"- JSON-LD Property Path: `{binding['property_path']}`")
        lines.append("")
    lines.extend(["## SERP Evidence", ""])
    lines.extend(
        f"- Evidence ID: `{item['evidence_id']}` | Gateway Request ID: `{item['gateway_request_id']}` | Source: `{item['source']}`"
        for item in sorted(briefing["serp_evidence"], key=lambda item: item["evidence_id"])
    )
    lines.extend(
        [
            "",
            "## JSON-LD",
            "",
            f"- Level: `{briefing['jsonld']['level']}`",
            f"- Graph SHA-256: `{briefing['jsonld']['graph_hash']}`",
            "",
            "```json",
            json.dumps(briefing["jsonld"]["graph"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_step4a(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step4a(bundle)
    output = prepare_step_output(workspace_root, "4a", _validated(bundle)[0]["artifact_id"])
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a canonical Step 4A briefing as Notion Markdown")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step4a(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
