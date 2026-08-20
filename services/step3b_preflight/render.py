from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.step3b_preflight.validator import validate_step3b_candidate
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> dict:
    result = validate_step3b_candidate(bundle["adjustment"])
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    return bundle["adjustment"]


def render_step3b(bundle: dict) -> str:
    adjustment = _validated(bundle)
    source = adjustment["source_plan"]
    proposed = adjustment["proposed_plan"]
    lines = [
        "# Step 3B Plan Adjustment",
        "",
        "## Immutable Source Plan",
        "",
        f"- Artifact: `{source['artifact_id']}`",
        f"- Revision: {source['revision']}",
        f"- Content SHA-256: `{source['content_sha256']}`",
        "",
        "## Proposed Plan",
        "",
        f"- Artifact: `{proposed['artifact_id']}`",
        f"- Revision: {proposed['revision']}",
        f"- Content SHA-256: `{proposed['content_sha256']}`",
        "",
        "## Evidence References",
        "",
    ]
    lines.extend(f"- `{evidence_id}`" for evidence_id in sorted(adjustment["evidence_ids"]))
    return "\n".join(lines) + "\n"


def write_step3b(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step3b(bundle)
    output = prepare_step_output(workspace_root, "3b", _validated(bundle)["proposed_plan"]["artifact_id"])
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a canonical Step 3B adjustment as Markdown")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step3b(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
