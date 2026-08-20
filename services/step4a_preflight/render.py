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


def render_step4a(bundle: dict) -> str:
    briefing, ledger = _validated(bundle)
    frontmatter = {
        "artifact_id": briefing["artifact_id"],
        "claim_ledger_artifact_id": briefing["claim_ledger_artifact_id"],
        "derived": briefing["notion_frontmatter"]["derived"],
        "project_id": briefing["project_id"],
        "projection_schema_version": briefing["notion_frontmatter"]["projection_schema_version"],
    }
    lines = ["---"]
    lines.extend(f"{key}: {json.dumps(value, ensure_ascii=True)}" for key, value in sorted(frontmatter.items()))
    lines.extend(["---", "", "# Content Briefing", "", "## Claim Ledger", ""])
    for claim in sorted(ledger["claims"], key=lambda item: item["claim_id"]):
        lines.extend([f"### {claim['claim_id']}", "", claim["text"], "", f"- Type: `{claim['claim_type']}`", f"- Review policy: `{claim['reviewer_policy']}`"])
        lines.extend(f"- Evidence: `{evidence_id}`" for evidence_id in sorted(claim["evidence_ids"]))
        lines.append("")
    lines.extend(["## SERP Evidence", ""])
    lines.extend(f"- `{item['evidence_id']}` via `{item['gateway_request_id']}`" for item in sorted(briefing["serp_evidence"], key=lambda item: item["evidence_id"]))
    lines.extend(["", "## JSON-LD", "", "```json", json.dumps(briefing["jsonld"]["graph"], ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
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
