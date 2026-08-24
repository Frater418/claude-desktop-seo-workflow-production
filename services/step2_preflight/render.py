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


FIELDNAMES = (
    "pillar",
    "evidence_id",
    "title",
    "keyword",
    "search_volume",
    "difficulty",
    "cpc_usd",
    "category",
    "content_type",
    "geo_type",
    "engine_target",
    "information_gain",
    "entity_density",
    "business_relevance",
    "mandatory_location_policy",
    "is_mandatory",
    "status",
    "provider",
    "raw_response_sha256",
)


def _validated(bundle: dict) -> list[dict]:
    result = validate_step2_preflight(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    candidate = bundle["candidate"]
    return [
        {"pillar": pillar["pillar_id"], **row}
        for pillar in candidate["pillars"]
        for row in pillar["rows"]
        if row["status"] == "verified"
    ]


def _project_row(row: dict) -> dict:
    return {
        "pillar": row["pillar"],
        "evidence_id": row["evidence_id"],
        "title": row["title"],
        "keyword": row["keyword"],
        "search_volume": row["search_volume"],
        "difficulty": row["difficulty"],
        "cpc_usd": json.dumps(row["cpc_usd"], ensure_ascii=True, separators=(",", ":"), sort_keys=True),
        "category": row["category"],
        "content_type": row["content_type"],
        "geo_type": row["geo_type"],
        "engine_target": json.dumps(row["engine_target"], ensure_ascii=True, separators=(",", ":"), sort_keys=True),
        "information_gain": row["information_gain"],
        "entity_density": row["entity_density"],
        "business_relevance": row["business_relevance"],
        "mandatory_location_policy": json.dumps(row["mandatory_location_policy"], ensure_ascii=True, separators=(",", ":"), sort_keys=True),
        "is_mandatory": str(row["mandatory_location_policy"]["state"] == "required").lower(),
        "status": row["status"],
        "provider": row["provider"],
        "raw_response_sha256": row["raw_response_sha256"],
    }


def render_step2(bundle: dict) -> str:
    rows = [_project_row(row) for row in _validated(bundle)]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: tuple(str(row[field]) for field in FIELDNAMES)))
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
