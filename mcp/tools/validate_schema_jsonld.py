#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


__author__ = "Raphael Rechberger"
TOOL_DIRECTORY = str(Path(__file__).resolve().parent)
if TOOL_DIRECTORY not in sys.path:
    sys.path.insert(0, TOOL_DIRECTORY)

from jsonld_validation_rules import validate_schema_object


def extract_json_ld(text: str) -> list:
    blocks = []
    matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', text, re.DOTALL | re.IGNORECASE)
    for match in matches:
        try:
            blocks.append(json.loads(match.strip()))
        except json.JSONDecodeError as exc:
            return [{"error": f"JSON Decode Error in script tag: {str(exc)}", "raw": match[:200]}]
    if not blocks:
        markdown_matches = re.findall(r'```(?:json)?\s*(\{[\s\S]*?"@context"[\s\S]*?\})\s*```', text, re.DOTALL)
        for match in markdown_matches:
            try:
                blocks.append(json.loads(match.strip()))
            except json.JSONDecodeError:
                pass
    if not blocks and text.strip().startswith("{"):
        try:
            blocks.append(json.loads(text.strip()))
        except json.JSONDecodeError as exc:
            blocks.append({"error": f"JSON Decode Error in raw text: {str(exc)}"})
    return blocks


def _issue(level: str, code: str, message: str, path: str = "") -> dict:
    return {"level": level, "code": code, "message": message, "path": path}


def validate_text(text: str, strict_geo: bool = False) -> dict:
    blocks = extract_json_ld(text)
    if not blocks:
        issue = _issue("parse", "ERROR_SCHEMA_JSONLD_MISSING", "No valid JSON-LD block was found in the supplied text.")
        return {"valid": False, "blocks_found": 0, "levels": {"parse": "failed", "contract": "not_run", "format": "not_run", "geo": "not_run", "claim_evidence": "not_assessed", "google_eligibility": "not_assessed"}, "issues": [issue], "errors": [issue["message"]]}
    issues = []
    for index, block in enumerate(blocks):
        if "error" in block:
            issues.append(_issue("parse", "ERROR_SCHEMA_JSON_PARSE", block["error"], f"/blocks/{index}"))
        else:
            issues.extend(validate_schema_object(block, strict_geo=strict_geo, path=f"/blocks/{index}"))
    levels = {
        "parse": "failed" if any(issue["level"] == "parse" for issue in issues) else "passed",
        "contract": "failed" if any(issue["level"] == "contract" for issue in issues) else "passed",
        "format": "failed" if any(issue["level"] == "format" for issue in issues) else "passed",
        "geo": ("failed" if any(issue["level"] == "geo" for issue in issues) else "passed") if strict_geo else "not_requested",
        "claim_evidence": "not_assessed",
        "google_eligibility": "not_assessed",
    }
    required_levels = ("parse", "contract", "format") + (("geo",) if strict_geo else ())
    return {"valid": all(levels[level] == "passed" for level in required_levels), "blocks_found": len(blocks), "levels": levels, "issues": issues, "errors": [issue["message"] for issue in issues]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Schema.org JSON-LD Validator CLI v1.2.0 (local contract and GEO levels)")
    parser.add_argument("--input", "-i", type=str, help="Pfad zur HTML-, Markdown- oder JSON-Datei")
    parser.add_argument("--strict", "-s", action="store_true", help="Aktiviert strikte GEO-Pruefung fuer Wikidata about/mentions")
    parser.add_argument("--json-out", action="store_true", help="Ergebnis als JSON ausgeben")
    arguments = parser.parse_args()
    if not arguments.input:
        print("Schema.org JSON-LD Validator v1.2.0 (Raphael Rechberger)")
        print("Nutzung: python validate_schema_jsonld.py --input <datei.html|datei.md|datei.json> [--strict]")
        sys.exit(0)
    input_path = Path(arguments.input)
    if not input_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {input_path}")
        sys.exit(1)
    result = validate_text(input_path.read_text(encoding="utf-8"), strict_geo=arguments.strict)
    if arguments.json_out:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif result["valid"]:
        print(f"[BESTANDEN] Lokale JSON-LD Vertragslevel in '{input_path.name}' bestanden. ({result['blocks_found']} Block/Bloecke geprueft)")
        print("[NICHT BEWERTET] Claim-Evidenz und Google Rich Result Eligibility erfordern separate Quality Gates.")
    else:
        print(f"[NICHT BESTANDEN] {len(result['issues'])} Validierungsfehler in '{input_path.name}':")
        for issue in result["issues"]:
            print(f"  - {issue['code']} [{issue['level']}]: {issue['message']}")
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
