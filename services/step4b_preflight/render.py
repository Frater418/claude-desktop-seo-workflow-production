from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.preflight_common import prepare_step_output
from services.step4b_preflight.html_sections import (
    SectionRenderError,
    render_sections,
    render_tracking_slots,
)
from services.step4b_preflight.html_values import HtmlValueError, attribute, http_url, jsonld, text
from services.step4b_preflight.validator import page_content_sha256, validate_step4b_candidate


class RendererError(ValueError):
    pass


ACCESSIBILITY_CSS = """
:focus-visible {
  outline: var(--spacing-1) solid var(--accent-secondary);
  outline-offset: var(--spacing-1);
}

form {
  display: grid;
  gap: var(--spacing-4);
}

.form-control {
  width: 100%;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
  color: var(--text-primary);
  background-color: var(--bg-primary);
  font: inherit;
}
""".strip()


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _design_system_css() -> str:
    return (_root() / "standards" / "design-system.css").read_text(encoding="utf-8")


def _validated(bundle: dict) -> tuple[dict, dict]:
    result = validate_step4b_candidate(bundle)
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    page = bundle["page_spec"]
    if page["content_sha256"] != page_content_sha256(page):
        raise RendererError("Page content hash does not bind the canonical page payload.")
    return page, bundle["project"]


def render_step4b(bundle: dict) -> str:
    page, project = _validated(bundle)
    try:
        sections = render_sections(page, project)
        tracking_slots = render_tracking_slots(page)
    except (HtmlValueError, SectionRenderError) as exc:
        raise RendererError(str(exc)) from exc
    metadata = page["meta"]
    return "\n".join(
        (
            "<!doctype html>",
            f'<html lang="{attribute(page["language"])}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{text(metadata['title'])}</title>",
            f'<meta name="description" content="{attribute(metadata["description"])}">',
            f'<link rel="canonical" href="{http_url(page["canonical_url"])}">',
            f"<style>\n{_design_system_css()}\n</style>",
            f"<style>\n{ACCESSIBILITY_CSS}\n</style>",
            f'<script type="application/ld+json">{jsonld(page["jsonld"]["graph"])}</script>',
            "</head>",
            "<body>",
            '<main id="main-content">',
            sections,
            "</main>",
            tracking_slots,
            f'<footer class="footer-disclaimer" data-consent-policy="{attribute(page["consent"]["policy_id"])}">',
            '<div class="container">Eine Einwilligung ist vor dem Absenden des Formulars erforderlich.</div>',
            "</footer>",
            "</body>",
            "</html>\n",
        )
    )


def write_step4b(bundle: dict, workspace_root: Path) -> Path:
    rendered = render_step4b(bundle)
    page, _ = _validated(bundle)
    output = prepare_step_output(workspace_root, "4b", page["artifact_id"])
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
