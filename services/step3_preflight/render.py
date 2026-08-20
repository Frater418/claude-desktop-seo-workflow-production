from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.step3_preflight.validator import validate_step3_preflight
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> dict:
    result = validate_step3_preflight(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    return bundle["candidate"]


def render_step3(bundle: dict) -> str:
    plan = _validated(bundle)
    weeks = sorted(plan["weeks"], key=lambda week: week["week"])
    total_capacity = sum(week["capacity_hours"] for week in weeks)
    lines = ["# 17-Week Content Plan", "", "## Capacity Summary", "", f"- Weeks: {len(weeks)}", f"- Total capacity hours: {total_capacity}", ""]
    for week in weeks:
        lines.extend([f"## Week {week['week']}", "", f"- Capacity hours: {week['capacity_hours']}"])
        lines.extend(f"- Item: `{item_id}`" for item_id in sorted(week["item_ids"]))
        lines.append("")
    lines.extend(["## Backlog", ""])
    lines.extend(f"- `{item_id}`" for item_id in sorted(plan.get("backlog_item_ids", [])))
    lines.extend(["", "## Vertical Links", ""])
    lines.extend(f"- `{item['source_item_id']}` -> `{item['target_pillar_id']}`" for item in sorted(plan["vertical_links"], key=lambda item: (item["source_item_id"], item["target_pillar_id"])))
    lines.extend(["", "## Horizontal Links", ""])
    lines.extend(f"- `{item['source_item_id']}` -> `{item['target_item_id']}`" for item in sorted(plan["horizontal_links"], key=lambda item: (item["source_item_id"], item["target_item_id"])))
    return "\n".join(lines) + "\n"


def write_step3(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step3(bundle)
    output = prepare_step_output(workspace_root, "3")
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a canonical Step 3 plan as Markdown")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step3(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
