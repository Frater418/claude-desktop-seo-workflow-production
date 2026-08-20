from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.step1c_preflight.validator import validate_step1c_candidate
from services.preflight_common import prepare_step_output


class RendererError(ValueError):
    pass


def _validated(bundle: dict) -> tuple[dict, list[dict]]:
    result = validate_step1c_candidate(bundle["design"], bundle["templates"])
    if not result["valid"]:
        raise RendererError(json.dumps(result["errors"], ensure_ascii=True, sort_keys=True))
    return bundle["design"], bundle["templates"]


def render_step1c(bundle: dict) -> dict[str, str]:
    design, templates = _validated(bundle)
    tokens = design["tokens"]
    css = "\n".join(
        [
            ":root {",
            f"  --color-primary: {tokens['color_primary']};",
            f"  --color-surface: {tokens['color_surface']};",
            f"  --font-body: {tokens['font_body']};",
            f"  --radius-card: {tokens['radius_card']};",
            "}",
            "* { box-sizing: border-box; }",
            "body { margin: 0; background: var(--color-surface); color: var(--color-primary); font-family: var(--font-body); }",
            ".skip-link:focus { position: static; }",
            ".page { max-width: 72rem; margin: auto; padding: 1rem; }",
        ]
    ) + "\n"
    rendered_templates: dict[str, str] = {}
    for template in templates:
        links = "\n".join(f'<li><a href="#{link["target_content_id"]}">{link["target_content_id"]}</a></li>' for link in template["links"])
        jsonld = json.dumps(template["jsonld_references"], ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        html = "\n".join([
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>" + template["content_id"] + "</title><style>" + css + "</style></head>",
            "<body><a class=\"skip-link\" href=\"#main\">Skip to content</a><nav aria-label=\"Related content\"><ul>" + links + "</ul></nav>",
            "<main id=\"main\" class=\"page\"><h1>" + template["content_id"] + "</h1></main>",
            "<script type=\"application/ld+json\">" + jsonld + "</script></body></html>\n",
        ])
        rendered_templates[f"html/{template['template_id']}.html"] = html
    return {"css": css, "html": next(iter(rendered_templates.values())), **rendered_templates}


def write_step1c(bundle: dict, workspace_root: Path) -> tuple[Path, tuple[Path, ...]]:
    rendered = render_step1c(bundle)
    css_output = prepare_step_output(workspace_root, "1c_css")
    template_outputs = tuple(
        prepare_step_output(workspace_root, "1c_template", template["template_id"])
        for template in _validated(bundle)[1]
    )
    css_output.write_text(rendered["css"], encoding="utf-8", newline="\n")
    for output in template_outputs:
        template_id = output.name.removesuffix(".v1.html")
        output.write_text(rendered[f"html/{template_id}.html"], encoding="utf-8", newline="\n")
    return css_output, template_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Render canonical Step 1C design and template JSON")
    parser.add_argument("--input", required=True)
    parser.add_argument("--workspace-root", required=True)
    arguments = parser.parse_args()
    write_step1c(json.loads(Path(arguments.input).read_text(encoding="utf-8")), Path(arguments.workspace_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
