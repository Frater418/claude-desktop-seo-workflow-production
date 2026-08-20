from __future__ import annotations

from html import escape

from services.step1b_preflight.validator import validate_step1b_candidate


def _ordered_decisions(architecture: dict) -> list[dict]:
    return sorted(architecture["content_decisions"], key=lambda item: item["content_id"])


def render_architecture_markdown(architecture: dict) -> str:
    result = validate_step1b_candidate(architecture, [item["content_id"] for item in architecture.get("content_decisions", []) if isinstance(item, dict) and isinstance(item.get("content_id"), str)])
    if not result["valid"]:
        raise ValueError(result["errors"])
    lines = ["# Step 1B Site Architecture", "", f"- Artifact: `{architecture['artifact_id']}`", f"- Deployment: `{architecture['deployment_id']}`", "", "| Content | Decision | URL | Canonical | Navigation |", "|---|---|---|---|---|"]
    lines.extend(f"| {item['content_id']} | {item['decision']} | {item['url']} | {item['canonical_url']} | {item['navigation']} |" for item in _ordered_decisions(architecture))
    lines.extend(["", "## Link Graph", ""])
    lines.extend(f"- `{item['from_content_id']}` -> `{item['to_content_id']}` ({item['relationship']})" for item in sorted(architecture["link_graph"], key=lambda item: (item["from_content_id"], item["to_content_id"], item["relationship"])))
    return "\n".join(lines) + "\n"


def render_architecture_html(architecture: dict) -> str:
    result = validate_step1b_candidate(architecture, [item["content_id"] for item in architecture.get("content_decisions", []) if isinstance(item, dict) and isinstance(item.get("content_id"), str)])
    if not result["valid"]:
        raise ValueError(result["errors"])
    rows = "".join(f"<tr><td>{escape(item['content_id'])}</td><td>{escape(item['decision'])}</td><td>{escape(item['url'])}</td><td>{escape(item['canonical_url'])}</td><td>{escape(item['navigation'])}</td></tr>" for item in _ordered_decisions(architecture))
    return f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Step 1B Architecture</title></head><body><main><h1>Step 1B Site Architecture</h1><p>Artifact: {escape(architecture['artifact_id'])}</p><table><thead><tr><th>Content</th><th>Decision</th><th>URL</th><th>Canonical</th><th>Navigation</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>"
