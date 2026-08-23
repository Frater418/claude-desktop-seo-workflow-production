from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
GENERATED_PATHS = {
    "00_admin/repository-index/DOCUMENT_REGISTRY.json",
    "00_admin/repository-index/DOCUMENT_REGISTRY.jsonl",
    "00_admin/REPOSITORY_INDEX.md",
    "00_admin/SESSION_BOOTSTRAP.md",
    "docs/INDEX.md",
    ".hermes/plans/INDEX.md",
    "00_admin/audits/INDEX.md",
    "03_research/INDEX.md",
}
TEXT_SUFFIXES = {".md", ".json", ".css", ".html"}
LIFECYCLES = {
    "current_authority",
    "current_strategy",
    "active_plan",
    "deferred_plan",
    "needs_reconciliation",
    "historical",
    "superseded",
    "evidence",
    "generated_view",
}
DASH_TRANSLATION = str.maketrans({"\u2014": "-", "\u2013": "-"})


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(path: Path, root: Path) -> str:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    return resolved.relative_to(root.resolve()).as_posix()


def _match(path: str, pattern: str) -> bool:
    expression = ""
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    expression += "(?:.*/)?"
                    index += 1
                else:
                    expression += ".*"
                continue
            expression += "[^/]*"
        elif character == "?":
            expression += "[^/]"
        else:
            expression += re.escape(character)
        index += 1
    return re.fullmatch(expression, path) is not None


def _excluded(path: str, patterns: list[str]) -> bool:
    return path in GENERATED_PATHS or any(_match(path, pattern) for pattern in patterns)


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    commit = result.stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("ERROR_INDEX_SOURCE_COMMIT_INVALID")
    return commit


def _sanitize(value: str) -> str:
    value = value.translate(DASH_TRANSLATION)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _extract_title(path: Path, data: bytes) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        text = data.decode("utf-8", errors="replace")
        for line in text.splitlines():
            if line.startswith("# "):
                return _sanitize(line[2:])
    if suffix == ".html":
        text = data.decode("utf-8", errors="replace")
        match = re.search(r"<(?:title|h1)[^>]*>(.*?)</(?:title|h1)>", text, flags=re.I | re.S)
        if match:
            return _sanitize(html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))))
    if suffix == ".json":
        try:
            payload = json.loads(data.decode("utf-8"))
            if isinstance(payload, dict):
                title = payload.get("title") or payload.get("name") or payload.get("$id")
                if isinstance(title, str) and title.strip():
                    return _sanitize(title)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    return _sanitize(path.stem.replace("_", " ").replace("-", " "))


def _extract_summary(path: Path, data: bytes, title: str) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return f"Indexed {path.suffix.lower().lstrip('.').upper()} document: {title}."
    text = data.decode("utf-8", errors="replace")
    in_frontmatter = False
    in_fence = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "---" and not in_fence:
            in_frontmatter = not in_frontmatter
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_frontmatter or in_fence or not line:
            continue
        if line.startswith(("#", "|", "<", "{", "[", "- ", "* ", ">")):
            continue
        cleaned = _sanitize(re.sub(r"[`*_]", "", line))
        if cleaned and cleaned.casefold() != title.casefold():
            return cleaned[:280]
    return f"Indexed repository document: {title}."


def _step_tags(path: str) -> list[str]:
    name = Path(path).name.lower()
    patterns = [
        ("4b", "4b"),
        ("4a", "4a"),
        ("3b", "3b"),
        ("1c", "1c"),
        ("1b", "1b"),
    ]
    for needle, step in patterns:
        if needle in name:
            return [step]
    match = re.match(r"(?:step-)?([0-3])(?:[-_.]|$)", name)
    return [match.group(1)] if match else []


def _base_rule(path: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    for rule in rules:
        if path.startswith(rule["prefix"]):
            return {key: value for key, value in rule.items() if key != "prefix"}
    raise ValueError(f"ERROR_INDEX_RULE_MISSING: {path}")


def _merge_metadata(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(override)
    for key in ("audiences", "workflow_steps", "tags", "supersedes", "related_paths"):
        values = merged.get(key, [])
        merged[key] = sorted(set(values))
    merged.setdefault("superseded_by", None)
    return merged


def _validate_entry(entry: dict[str, Any], root: Path) -> None:
    required = {
        "document_id",
        "path",
        "title",
        "summary",
        "document_type",
        "area",
        "lifecycle",
        "authority_level",
        "retrieval_priority",
        "default_retrieval",
        "audiences",
        "workflow_steps",
        "tags",
        "supersedes",
        "superseded_by",
        "related_paths",
        "format",
        "content_sha256",
        "size_bytes",
        "generated_source",
    }
    missing = sorted(required - entry.keys())
    if missing:
        raise ValueError(f"ERROR_INDEX_ENTRY_REQUIRED: {entry.get('path')}: {missing}")
    if entry["lifecycle"] not in LIFECYCLES:
        raise ValueError(f"ERROR_INDEX_LIFECYCLE: {entry['path']}")
    if entry["default_retrieval"] and entry["lifecycle"] in {"historical", "superseded", "evidence"}:
        raise ValueError(f"ERROR_INDEX_STALE_DEFAULT: {entry['path']}")
    if not re.fullmatch(r"[a-f0-9]{64}", entry["content_sha256"]):
        raise ValueError(f"ERROR_INDEX_HASH: {entry['path']}")
    for related in entry["related_paths"]:
        if not (root / related).exists():
            raise ValueError(f"ERROR_INDEX_RELATED_MISSING: {entry['path']}: {related}")
    target = entry["superseded_by"]
    if target is not None and not (root / target).exists():
        raise ValueError(f"ERROR_INDEX_SUPERSESSION_MISSING: {entry['path']}: {target}")


def collect_entries(root: Path, policy: dict[str, Any], overrides: dict[str, Any]) -> list[dict[str, Any]]:
    paths: dict[str, Path] = {}
    excluded = policy["exclude_globs"]
    for pattern in policy["include_globs"]:
        for candidate in root.glob(pattern):
            if not candidate.is_file():
                continue
            relative = _normalized(candidate, root)
            if _excluded(relative, excluded):
                continue
            lower = relative.casefold()
            if any(token in lower for token in ("/.env", "/credentials", "/secrets", "/tokens")):
                raise ValueError(f"ERROR_INDEX_SENSITIVE_PATH: {relative}")
            paths[relative] = candidate

    strict_patterns = policy["strict_override_globs"]
    for relative in sorted(paths):
        if any(_match(relative, pattern) for pattern in strict_patterns) and relative not in overrides:
            raise ValueError(f"ERROR_INDEX_OVERRIDE_REQUIRED: {relative}")

    entries: list[dict[str, Any]] = []
    for relative, candidate in sorted(paths.items()):
        data = candidate.read_bytes()
        title = _extract_title(candidate, data)
        base = _base_rule(relative, policy["auto_rules"])
        base.update(
            {
                "document_id": "doc-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16],
                "path": relative,
                "title": title,
                "summary": _extract_summary(candidate, data, title),
                "workflow_steps": _step_tags(relative),
                "supersedes": [],
                "superseded_by": None,
                "related_paths": [],
                "format": candidate.suffix.lower().lstrip(".") or "none",
                "content_sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "generated_source": False,
            }
        )
        entry = _merge_metadata(base, overrides.get(relative, {}))
        entry["title"] = _sanitize(entry["title"])
        entry["summary"] = _sanitize(entry["summary"])
        _validate_entry(entry, root)
        entries.append(entry)
    return entries


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(entries: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in entries) + "\n").encode("utf-8")


def _markdown_table(entries: list[dict[str, Any]]) -> str:
    lines = ["| Document | Lifecycle | Authority | Default |", "|---|---|---:|---|"]
    for entry in entries:
        lines.append(
            f"| [`{entry['path']}`](../{entry['path']}) | `{entry['lifecycle']}` | {entry['authority_level']} | {'yes' if entry['default_retrieval'] else 'no'} |"
        )
    return "\n".join(lines)


def _repository_index(entries: list[dict[str, Any]], commit: str) -> bytes:
    default = sorted((e for e in entries if e["default_retrieval"]), key=lambda e: (-e["authority_level"], e["path"]))
    warnings = sorted(
        (entry for entry in entries if entry["lifecycle"] == "needs_reconciliation"),
        key=lambda entry: entry["path"],
    )
    counts = Counter(e["lifecycle"] for e in entries)
    lines = [
        "# Repository authority index",
        "",
        "**Author:** Raphael Rechberger",
        f"**Indexed snapshot:** `{commit}`",
        "**Generated:** deterministic from repository sources",
        "",
        "## Start here",
        "",
        "1. [`SESSION_BOOTSTRAP.md`](SESSION_BOOTSTRAP.md)",
        "2. [`PROJECT_STATE.md`](PROJECT_STATE.md)",
        "3. [`DECISIONS.md`](DECISIONS.md)",
        "4. Select the active plan for the current task from [`.hermes/plans/INDEX.md`](../.hermes/plans/INDEX.md)",
        "5. Before test or review decisions, read [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md)",
        "6. Use `repository-index/DOCUMENT_REGISTRY.jsonl` for filtered RAG ingestion",
        "",
        "## Default retrieval set",
        "",
        _markdown_table(default),
        "",
        "## Lifecycle counts",
        "",
    ]
    for lifecycle in sorted(counts):
        lines.append(f"- `{lifecycle}`: {counts[lifecycle]}")
    lines.extend(["", "## Reconciliation warnings", ""])
    if warnings:
        for entry in warnings:
            lines.append(f"- `{entry['path']}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Retrieval rule",
            "",
            "Filter by lifecycle and authority before semantic ranking. Historical, superseded and evidence records are opt-in only.",
            "",
        ]
    )
    return "\n".join(lines).translate(DASH_TRANSLATION).encode("utf-8")


def _session_bootstrap(commit: str) -> bytes:
    text = f"""# Session bootstrap

**Author:** Raphael Rechberger
**Indexed snapshot:** `{commit}`

## Mandatory read order

1. Read `00_admin/PROJECT_STATE.md`.
2. Read active and superseding records in `00_admin/DECISIONS.md`.
3. Read `00_admin/REPOSITORY_INDEX.md`.
4. Select the active plan for the requested task from `.hermes/plans/INDEX.md`.
5. Before any test or review decision, read `standards/testing/PROTOTYPE_TEST_POLICY.md`.
6. Resolve exact standards, prompts and supporting evidence through `00_admin/repository-index/DOCUMENT_REGISTRY.json`.
7. Read historical or audit material only when the task requires origin, rollback, prior decisions or failure reconstruction.

## Authority rule

Project State and active Decisions override entry documents, old plans, audit prose and semantic similarity. A search result is not an authority decision.

## Current snapshot warning

This parallel index was generated from WIP commit `{commit}`. Any records listed as `needs_reconciliation` in `00_admin/REPOSITORY_INDEX.md` must not be treated as current authority. All volatile completion facts require one final refresh from the stable Feature commit before integration.

## RAG rule

A future semantic retriever must first exclude `historical`, `superseded` and `evidence` records from default retrieval. It may include them only for explicit historical or audit queries.
"""
    return text.translate(DASH_TRANSLATION).encode("utf-8")


def _area_index(title: str, entries: list[dict[str, Any]], relative_prefix: str) -> bytes:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[entry["lifecycle"]].append(entry)
    lines = [f"# {title}", "", "**Author:** Raphael Rechberger", "", "Generated from the canonical document registry.", ""]
    for lifecycle in sorted(grouped):
        lines.extend([f"## {lifecycle}", ""])
        for entry in sorted(grouped[lifecycle], key=lambda item: item["path"]):
            target = relative_prefix + entry["path"]
            lines.append(f"- [`{entry['path']}`]({target}): {entry['summary']}")
        lines.append("")
    return "\n".join(lines).translate(DASH_TRANSLATION).encode("utf-8")


def _audit_index(entries: list[dict[str, Any]]) -> bytes:
    packages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        parts = Path(entry["path"]).parts
        package = parts[2] if len(parts) > 2 else "unclassified"
        packages[package].append(entry)
    lines = [
        "# Audit evidence index",
        "",
        "**Author:** Raphael Rechberger",
        "",
        "Audit evidence is immutable and excluded from default retrieval. Select a package only for verification or reconstruction.",
        "",
        "| Package | Records | Entry point |",
        "|---|---:|---|",
    ]
    for package in sorted(packages):
        records = packages[package]
        readmes = [entry for entry in records if Path(entry["path"]).name.casefold() in {"readme.md", "00_master_audit.md", "current_point_of_work.md"}]
        entry = sorted(readmes or records, key=lambda item: item["path"])[0]
        target = "../../" + entry["path"]
        lines.append(f"| `{package}` | {len(records)} | [`{entry['path']}`]({target}) |")
    lines.append("")
    return "\n".join(lines).translate(DASH_TRANSLATION).encode("utf-8")


def generate_outputs(root: Path) -> dict[str, bytes]:
    policy = _read_json(root / "00_admin/repository-index/source-policy.json")
    override_payload = _read_json(root / "00_admin/repository-index/authority-overrides.json")
    if policy.get("schema_version") != SCHEMA_VERSION or override_payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("ERROR_INDEX_CONFIG_VERSION")
    commit = _git_commit(root)
    entries = collect_entries(root, policy, override_payload["overrides"])
    registry = {
        "schema_version": SCHEMA_VERSION,
        "registry_version": policy["registry_version"],
        "source_commit": commit,
        "authority_order": policy["authority_order"],
        "entries": entries,
    }
    docs_entries = [entry for entry in entries if entry["area"] == "docs"]
    plan_entries = [entry for entry in entries if entry["area"] == "plans"]
    audit_entries = [entry for entry in entries if entry["area"] == "audits"]
    research_entries = [entry for entry in entries if entry["area"] == "research"]
    return {
        "00_admin/repository-index/DOCUMENT_REGISTRY.json": _json_bytes(registry),
        "00_admin/repository-index/DOCUMENT_REGISTRY.jsonl": _jsonl_bytes(entries),
        "00_admin/REPOSITORY_INDEX.md": _repository_index(entries, commit),
        "00_admin/SESSION_BOOTSTRAP.md": _session_bootstrap(commit),
        "docs/INDEX.md": _area_index("Documentation index", docs_entries, "../"),
        ".hermes/plans/INDEX.md": _area_index("Plan lifecycle index", plan_entries, "../../"),
        "00_admin/audits/INDEX.md": _audit_index(audit_entries),
        "03_research/INDEX.md": _area_index("Research source index", research_entries, "../"),
    }


def write_or_check(root: Path, output_root: Path, check: bool) -> list[str]:
    outputs = generate_outputs(root)
    drift: list[str] = []
    for relative, expected in outputs.items():
        target = output_root / relative
        if check:
            if not target.exists() or target.read_bytes() != expected:
                drift.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
    return drift


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic Heartweb repository indexes")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    output_root = (args.output_root or root).resolve()
    drift = write_or_check(root, output_root, args.check)
    if drift:
        print(json.dumps({"status": "DRIFT", "paths": drift}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
