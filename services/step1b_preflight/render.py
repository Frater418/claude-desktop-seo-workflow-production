from __future__ import annotations

from html import escape

from services.step1b_preflight.validator import validate_step1b_candidate


def _validated(architecture: dict) -> None:
    approved_content_ids = [item["content_id"] for item in architecture.get("content_decisions", []) if isinstance(item, dict) and isinstance(item.get("content_id"), str)]
    result = validate_step1b_candidate(architecture, approved_content_ids)
    if not result["valid"]:
        raise ValueError(result["errors"])


def _ordered_decisions(architecture: dict) -> list[dict]:
    return sorted(architecture["content_decisions"], key=lambda item: item["content_id"])


def _tree(architecture: dict) -> list[tuple[dict, list[dict]]]:
    decisions = _ordered_decisions(architecture)
    children = {item["content_id"]: [] for item in decisions if item["page_type"] == "pillar_page"}
    for item in decisions:
        if item["page_type"] == "cluster_page":
            children[item["parent_content_id"]].append(item)
    return [(item, sorted(children[item["content_id"]], key=lambda child: child["content_id"])) for item in decisions if item["page_type"] == "pillar_page"]


def _markdown_decision(item: dict, indent: str = "") -> str:
    redirect = item.get("redirect_to_url", "")
    return f"{indent}- [{item['page_type']}] {item['display_label']} | Decision: {item['decision']} | URL: {item['url']} | Canonical: {item['canonical_url']} | Navigation: {item['navigation']} | Redirect: {redirect}"


def render_architecture_markdown(architecture: dict) -> str:
    _validated(architecture)
    lines = ["# Step 1B Site Architecture", "", f"- Artifact: `{architecture['artifact_id']}`", f"- Deployment: `{architecture['deployment_id']}`", "", "## Page Type Legend", ""]
    lines.extend(f"- [{item['code']}] {item['label']}: {item['description']}" for item in sorted(architecture["page_type_legend"], key=lambda item: item["code"]))
    lines.extend(["", "## Architecture Tree", ""])
    for parent, children in _tree(architecture):
        lines.append(_markdown_decision(parent))
        lines.extend(_markdown_decision(child, "  ") for child in children)
    lines.extend(["", "## Open Confirmations", ""])
    lines.extend(f"- [{item['status']}] {item['confirmation_id']}: {item['question']} ({', '.join(item['content_ids'])})" for item in sorted(architecture["open_confirmations"], key=lambda item: item["confirmation_id"]))
    lines.extend(["", "## Link Graph", ""])
    lines.extend(f"- `{item['from_content_id']}` -> `{item['to_content_id']}` ({item['relationship']})" for item in sorted(architecture["link_graph"], key=lambda item: (item["from_content_id"], item["to_content_id"], item["relationship"])))
    return "\n".join(lines) + "\n"


def _html_decision(item: dict) -> str:
    redirect = item.get("redirect_to_url", "")
    attributes = " ".join(
        (
            f'data-page-type="{escape(item["page_type"], quote=True)}"',
            f'data-canonical-url="{escape(item["canonical_url"], quote=True)}"',
            f'data-navigation="{escape(item["navigation"], quote=True)}"',
            f'data-redirect-to-url="{escape(redirect, quote=True)}"',
            f'data-presentation-status="{escape(item["presentation_status"], quote=True)}"',
        )
    )
    redirect_text = f"<span>Redirect: {escape(redirect)}</span>" if redirect else ""
    return f'<li class="architecture-node" {attributes}><span class="page-type-badge">{escape(item["page_type"])}</span><strong>{escape(item["display_label"])}</strong><span>Decision: {escape(item["decision"])}</span><span>URL: {escape(item["url"])}</span><span>Canonical: {escape(item["canonical_url"])}</span><span>Navigation: {escape(item["navigation"])}</span>{redirect_text}'


def _html_tree(architecture: dict) -> str:
    entries = []
    for parent, children in _tree(architecture):
        child_nodes = "".join(f"{_html_decision(child)}</li>" for child in children)
        child_tree = f'<ul class="architecture-children">{child_nodes}</ul>' if child_nodes else ""
        entries.append(f"{_html_decision(parent)}{child_tree}</li>")
    return "".join(entries)


def render_architecture_html(architecture: dict) -> str:
    _validated(architecture)
    legend = "".join(f'<li><span class="page-type-badge" data-page-type="{escape(item["code"], quote=True)}">{escape(item["label"])}</span><span>{escape(item["description"])}</span></li>' for item in sorted(architecture["page_type_legend"], key=lambda item: item["code"]))
    confirmations = "".join(f'<li data-confirmation-status="{escape(item["status"], quote=True)}"><strong>{escape(item["confirmation_id"])}</strong><span>{escape(item["question"])}</span><span>{escape(", ".join(item["content_ids"]))}</span></li>' for item in sorted(architecture["open_confirmations"], key=lambda item: item["confirmation_id"]))
    links = "".join(f"<li>{escape(item['from_content_id'])} -&gt; {escape(item['to_content_id'])} ({escape(item['relationship'])})</li>" for item in sorted(architecture["link_graph"], key=lambda item: (item["from_content_id"], item["to_content_id"], item["relationship"])))
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Step 1B Architecture</title><style>body{{font-family:system-ui,sans-serif;line-height:1.5;margin:2rem;max-width:72rem}}section{{margin-block:2rem}}ul{{padding-left:1.25rem}}.architecture-node{{display:grid;gap:.25rem;margin-block:1rem}}.architecture-children{{margin-top:.5rem}}.page-type-badge{{background:#e5f3f5;border-radius:.25rem;display:inline-block;font-size:.85rem;font-weight:700;padding:.15rem .4rem;width:max-content}}</style></head><body><main><h1>Step 1B Site Architecture</h1><p>Artifact: {escape(architecture["artifact_id"])}</p><p>Deployment: {escape(architecture["deployment_id"])}</p><section id="page-type-legend" aria-labelledby="page-type-legend-heading"><h2 id="page-type-legend-heading">Page Type Legend</h2><ul>{legend}</ul></section><section id="architecture-tree" aria-labelledby="architecture-tree-heading"><h2 id="architecture-tree-heading">Architecture Tree</h2><ul>{_html_tree(architecture)}</ul></section><section id="open-confirmations" aria-labelledby="open-confirmations-heading"><h2 id="open-confirmations-heading">Open Confirmations</h2><ul>{confirmations}</ul></section><section id="link-graph" aria-labelledby="link-graph-heading"><h2 id="link-graph-heading">Link Graph</h2><ul>{links}</ul></section></main></body></html>'
