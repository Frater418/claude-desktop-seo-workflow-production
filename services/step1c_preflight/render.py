from __future__ import annotations

import argparse
import json
from html import escape
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


def _escaped(value: str) -> str:
    return escape(value, quote=True)


def _evidence_attributes(evidence_ids: list[str]) -> str:
    return f' data-evidence-ids="{_escaped(" ".join(evidence_ids))}"'


def _cta(cta: dict, routes: dict[tuple[str, str], str]) -> str:
    return f'<a class="cta" href="{_escaped(routes[(cta["target_content_id"], "vertical")])}"{_evidence_attributes(cta["evidence_ids"])}>{_escaped(cta["label"])}</a>'


def _content_links(links: list[dict], routes: dict[tuple[str, str], str]) -> str:
    return "".join(f'<li><a href="{_escaped(routes[(link["target_content_id"], link["relationship"])])}">{_escaped(link["label"])}</a></li>' for link in links)


def _css(tokens: dict) -> str:
    return "\n".join(
        [
            ":root {",
            f"  --color-primary: {tokens['color_primary']};",
            f"  --color-surface: {tokens['color_surface']};",
            f"  --font-body: {tokens['font_body']};",
            f"  --radius-card: {tokens['radius_card']};",
            "}",
            "* { box-sizing: border-box; }",
            "body { margin: 0; background: var(--color-surface); color: var(--color-primary); font-family: var(--font-body); line-height: 1.6; }",
            "a { color: inherit; }",
            ".skip-link { position: absolute; inset-inline-start: 1rem; inset-block-start: -4rem; padding: .75rem 1rem; background: var(--color-primary); color: var(--color-surface); border-radius: var(--radius-card); }",
            ".skip-link:focus { inset-block-start: 1rem; }",
            ".page, .pillar-hero > div, .pillar-final-cta > div { max-width: 72rem; margin: auto; padding: 2rem 1rem; }",
            ".pillar-hero, .pillar-final-cta { background: var(--color-primary); color: var(--color-surface); }",
            ".pillar-hero h1, .pillar-final-cta h2 { margin: 0; max-width: 22ch; line-height: 1.15; }",
            ".pillar-hero p, .pillar-final-cta p { max-width: 65ch; }",
            ".cta { display: inline-block; padding: .7rem 1rem; border: 1px solid currentColor; border-radius: var(--radius-card); font-weight: 700; text-decoration: none; }",
            ".page > section, .page > article, .page > nav { margin-block: 2rem; padding: 1.25rem; border: 1px solid var(--color-primary); border-radius: var(--radius-card); }",
            ".facts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem; }",
            ".facts-grid dt { font-weight: 700; }",
            ".facts-grid dd { margin: .25rem 0 0; }",
            ".link-groups { display: grid; gap: 1rem; }",
            ".link-groups ul, .page > nav ul { margin: .5rem 0 0; padding-inline-start: 1.25rem; }",
            "blockquote { margin: 0; padding-inline-start: 1rem; border-inline-start: 4px solid var(--color-primary); }",
            "details + details { margin-top: .75rem; }",
        ]
    ) + "\n"


def _render_template(design: dict, template: dict, css: str) -> str:
    content = template["content"]
    routes = {(link["target_content_id"], link["relationship"]): link["href"] for link in template["links"]}
    grouped_links = "".join(
        f'<section><h3>{_escaped(group["label"])}</h3><ul>{_content_links(group["links"], routes)}</ul></section>'
        for group in content["grouped_cluster_links"]["groups"]
    )
    facts = "".join(
        f'<div{_evidence_attributes(fact["evidence_ids"])}><dt>{_escaped(fact["label"])}</dt><dd>{_escaped(fact["value"])}</dd></div>'
        for fact in content["quick_facts"]["facts"]
    )
    process_steps = "".join(
        f'<li{_evidence_attributes(step["evidence_ids"])}><h3>{_escaped(step["title"])}</h3><p>{_escaped(step["description"])}</p></li>'
        for step in content["process"]["steps"]
    )
    social_proof = "".join(
        f'<blockquote{_evidence_attributes(entry["evidence_ids"])}><p>{_escaped(entry["quote"])}</p><footer>{_escaped(entry["attribution"])}</footer></blockquote>'
        for entry in content["social_proof"]["entries"]
    )
    faq_items = "".join(
        f'<details open{_evidence_attributes(item["evidence_ids"])} data-jsonld-reference-id="{_escaped(item["jsonld_reference_id"])}"><summary>{_escaped(item["question"])}</summary><p>{_escaped(item["answer"])}</p></details>'
        for item in content["faq"]["items"]
    )
    jsonld = json.dumps(template["jsonld_references"], ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    brand = design["brand_consistency"]
    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="en" data-approved-brand="{_escaped(brand["approved_brand_name"])}" data-brand-evidence-ids="{_escaped(" ".join(brand["evidence_ids"]))}">',
            f'<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="heartweb-approved-brand-direction" content="{_escaped(brand["approved_direction"])}"><title>{_escaped(content["hero"]["heading"])}</title><style>{css}</style></head>',
        f'<body><a class="skip-link" href="#main">{_escaped(template["accessibility"]["skip_link_label"])}</a>',
        f'<header class="pillar-hero"><div><h1>{_escaped(content["hero"]["heading"])}</h1><p>{_escaped(content["hero"]["summary"])}</p>{_cta(content["hero"]["primary_cta"], routes)}</div></header>',
            f'<main id="main" class="page" data-content-id="{_escaped(template["content_id"])}"><section aria-labelledby="quick-facts-heading"><h2 id="quick-facts-heading">{_escaped(content["quick_facts"]["heading"])}</h2><dl class="facts-grid">{facts}</dl></section>',
            f'<article aria-labelledby="editorial-heading"{_evidence_attributes(content["editorial"]["evidence_ids"])}><h2 id="editorial-heading">{_escaped(content["editorial"]["heading"])}</h2>{"".join(f"<p>{_escaped(paragraph)}</p>" for paragraph in content["editorial"]["paragraphs"])}</article>',
            f'<section aria-labelledby="heartpiece-heading"{_evidence_attributes(content["heartpiece"]["evidence_ids"])}><h2 id="heartpiece-heading">{_escaped(content["heartpiece"]["heading"])}</h2><p>{_escaped(content["heartpiece"]["body"])}</p></section>',
            f'<nav aria-label="Related cluster guides"><h2>{_escaped(content["grouped_cluster_links"]["heading"])}</h2><div class="link-groups">{grouped_links}</div></nav>',
            f'<section aria-labelledby="process-heading"><h2 id="process-heading">{_escaped(content["process"]["heading"])}</h2><ol>{process_steps}</ol></section>',
            f'<section aria-labelledby="social-proof-heading"><h2 id="social-proof-heading">{_escaped(content["social_proof"]["heading"])}</h2>{social_proof}</section>',
        f'<section aria-labelledby="faq-heading"><h2 id="faq-heading">{_escaped(content["faq"]["heading"])}</h2>{faq_items}</section>',
        f'<nav aria-label="Related pillar pages"><h2>{_escaped(content["cross_pillar_links"]["heading"])}</h2><ul>{_content_links(content["cross_pillar_links"]["links"], routes)}</ul></nav></main>',
        f'<footer class="pillar-final-cta"><div><h2>{_escaped(content["final_cta"]["heading"])}</h2><p>{_escaped(content["final_cta"]["summary"])}</p>{_cta(content["final_cta"]["primary_cta"], routes)}</div></footer>',
            f'<script type="application/ld+json">{jsonld}</script></body></html>\n',
        ]
    )


def render_step1c(bundle: dict) -> dict[str, str]:
    design, templates = _validated(bundle)
    css = _css(design["tokens"])
    rendered_templates = {f"html/{template['template_id']}.html": _render_template(design, template, css) for template in templates}
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
