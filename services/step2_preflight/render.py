from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

from services.step2_preflight.validator import validate_step2_preflight
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> list[dict]:
    result = validate_step2_preflight(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    candidate = bundle["candidate"]
    return [row for pillar in candidate["pillars"] for row in pillar["rows"] if row["status"] == "verified"]


def render_step2(bundle: dict) -> str:
    rows = _validated(bundle)
    fieldnames = sorted({field for row in rows for field in row})
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: tuple(str(row.get(field, "")) for field in fieldnames)))
    return stream.getvalue()


def write_step2(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step2(bundle)
    output = prepare_step_output(workspace_root, "2")
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render canonical Step 2 evidence as CSV")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step2(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
