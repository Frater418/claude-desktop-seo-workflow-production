"""Deterministic Markdown renderer for Step 1 topic inventories.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_topic_inventory(inventory: dict) -> str:
    lines = [
        "# Step 1 Topic Inventory",
        "",
        f"- Project: `{inventory['project_id']}`",
        f"- Deployment: `{inventory['deployment_id']}`",
        f"- Run: `{inventory['run_id']}`",
        f"- Artifact: `{inventory['artifact_id']}`",
        f"- Schema: `{inventory['schema_version']}`",
        f"- Site status: `{inventory['site_applicability']['site_status']}`",
        "",
        "## Pillars and Cluster Hypotheses",
        "",
    ]
    for pillar in inventory["pillars"]:
        lines.extend(
            [
                f"### {pillar['name']}",
                "",
                f"Pillar ID: `{pillar['pillar_id']}`",
                "",
                "| Cluster ID | Cluster hypothesis | Content type | Intent hypothesis | Information gain | Region | GEO engines | Conversational query | Status |",
                "|---|---|---|---|---:|---|---|---|---|",
            ]
        )
        for cluster in pillar["cluster_candidates"]:
            lines.append(
                "| {cluster_id} | {name} | {content_type} | {intent} | {gain} | {region} | {engines} | {query} | {status} |".format(
                    cluster_id=cluster["cluster_id"],
                    name=cluster["name"],
                    content_type=cluster["content_type"],
                    intent=cluster["hypothesized_intent"],
                    gain=cluster["information_gain_score"],
                    region=cluster["regional_scope"],
                    engines=", ".join(cluster["geo_engine_targets"]),
                    query="; ".join(cluster["conversational_query_patterns"]),
                    status=cluster["status"],
                )
            )
        lines.append("")

    lines.extend(["## Explicit Hypotheses", ""])
    for item in inventory["hypotheses"]:
        lines.append(f"- `{item['hypothesis_id']}`: {item['statement']} - Status: `{item['status']}`")

    lines.extend(["", "## Evidence-Based Gaps", ""])
    for item in inventory["gaps"]:
        lines.append(f"- `{item['gap_id']}`: {item['statement']}")

    lines.extend(["", "## Decision Records", ""])
    for item in inventory["decision_records"]:
        lines.extend(
            [
                f"### {item['decision_id']}",
                "",
                f"Question: {item['question']}",
                "",
                f"Outcome: {item['outcome']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Evidence References",
            "",
            f"- Sources: {', '.join(f'`{value}`' for value in inventory['source_evidence_ids'])}",
            f"- Competitors: {', '.join(f'`{value}`' for value in inventory['competitor_evidence_ids'])}",
            f"- Existing URLs: {', '.join(f'`{value}`' for value in inventory['existing_url_evidence_ids'])}",
            f"- Crawl snapshots: {', '.join(f'`{value}`' for value in inventory['crawl_snapshot_evidence_ids'])}",
            "",
            "## Gate Status",
            "",
            "The canonical JSON passed the Step 1 submission preflight and is awaiting external GATE-1 review. No following workflow step is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Step 1 canonical inventory as Markdown")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    inventory = json.loads(Path(args.input).read_text(encoding="ascii"))
    output = render_topic_inventory(inventory)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(f"Rendered Step 1 Markdown: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
