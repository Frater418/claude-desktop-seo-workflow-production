from __future__ import annotations

import json

from pydantic import JsonValue


def canonical_json_bytes(value: JsonValue) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
