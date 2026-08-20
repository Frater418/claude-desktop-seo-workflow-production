from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from services.step4b_preflight.validator import page_content_sha256, validate_step4b_candidate
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> dict:
    result = validate_step4b_candidate(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    return bundle["page_spec"]


def render_step4b(bundle: dict) -> str:
    page = _validated(bundle)
    if page["content_sha256"] != page_content_sha256(page):
        raise RendererError("Page content hash does not bind the canonical page payload.")
    metadata = page["meta"]
    forms = "\n".join(f'<form id="{html.escape(form["form_id"], quote=True)}" data-consent-required="true"></form>' for form in page["forms"])
    areas = "\n".join(f"<li>{html.escape(area)}</li>" for area in sorted(page["service_area"]["areas"]))
    links = "\n".join(f'<li><a href="{html.escape(link, quote=True)}">{html.escape(link)}</a></li>' for link in sorted(page["sibling_links"]))
    tracking = "\n".join(f'<div data-tracking-slot="{html.escape(slot["slot_id"], quote=True)}" data-consent-category="{html.escape(slot["consent_category"], quote=True)}"></div>' for slot in sorted(page["tracking_slots"], key=lambda item: item["slot_id"]))
    jsonld = json.dumps(page["jsonld"]["graph"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "\n".join(
        [
            "<!doctype html>",
            f"<html lang=\"{html.escape(page['language'], quote=True)}\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            f"<title>{html.escape(metadata['title'])}</title>",
            f"<meta name=\"description\" content=\"{html.escape(metadata['description'], quote=True)}\">",
            f"<link rel=\"canonical\" href=\"{html.escape(page['canonical_url'], quote=True)}\">",
            "<style>body{margin:0;font-family:system-ui,sans-serif}.page{max-width:72rem;margin:auto;padding:1rem}form{display:grid;gap:1rem}@media (max-width:40rem){.page{padding:.75rem}}</style>",
            f"<script type=\"application/ld+json\">{jsonld}</script>",
            "</head>",
            "<body><main class=\"page\">",
            page["html"],
            f"<section><h2>Service areas</h2><ul>{areas}</ul></section>",
            forms,
            f"<section data-consent-policy=\"{html.escape(page['consent']['policy_id'], quote=True)}\" data-consent-required=\"true\"></section>",
            tracking,
            f"<nav aria-label=\"Related pages\"><ul>{links}</ul></nav>",
            "</main></body></html>\n",
        ]
    )


def write_step4b(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step4b(bundle)
    output = prepare_step_output(workspace_root, "4b", _validated(bundle)["artifact_id"])
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a canonical Step 4B page specification as HTML")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step4b(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
