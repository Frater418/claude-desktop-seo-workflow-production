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
GENERATOR_VERSION = "1.1.0"
ONBOARDING_SOURCE_PATHS = (
    "00_admin/PROJECT_STATE.md",
    "00_admin/DECISIONS.md",
    "00_admin/MASTER_TASK_MATRIX.md",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "standards/testing/PROTOTYPE_TEST_POLICY.md",
    "docs/00-current-production-architecture.md",
    "docs/09-extension-and-evolution-guide.md",
    "00_admin/DEFERRED_INTEGRATION_BACKLOG.md",
    "00_admin/POST_RELEASE_BACKLOG.md",
    ".hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md",
)
INITIAL_ROUTE_STEPS = ("0", "1", "1b", "1c", "2", "3", "4a", "4b")
CANONICAL_TEXT_SUFFIXES = {
    ".cjs", ".css", ".csv", ".html", ".js", ".json", ".jsonl", ".md", ".mjs",
    ".py", ".sh", ".svg", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
GENERATED_PATHS = {
    "00_admin/ONBOARDING_REFERENCE.md",
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
    head_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    head = head_result.stdout.strip()
    changed_result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    parents_result = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    changed = {line.strip().replace("\\", "/") for line in changed_result.stdout.splitlines() if line.strip()}
    parent_fields = parents_result.stdout.split()
    commit = parent_fields[1] if changed and changed.issubset(GENERATED_PATHS) and len(parent_fields) > 1 else head
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("ERROR_INDEX_SOURCE_COMMIT_INVALID")
    return commit


def _sanitize(value: str) -> str:
    value = value.translate(DASH_TRANSLATION)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _canonical_document_bytes(path: str | Path, data: bytes) -> bytes:
    if Path(path).suffix.casefold() not in CANONICAL_TEXT_SUFFIXES:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


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
        data = _canonical_document_bytes(relative, candidate.read_bytes())
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


def _md_cell(value: object) -> str:
    return _sanitize(str(value)).replace("|", "\\|")


def _source_fence(text: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    return "`" * max(4, longest + 1)


def _current_status_excerpt(root: Path) -> str:
    lines = (root / "00_admin/PROJECT_STATE.md").read_text(encoding="utf-8").splitlines()
    selected = [line for line in lines[:20] if line.startswith("**Status:**")]
    start = next((index for index, line in enumerate(lines) if line.startswith("### Aktueller Konsolidierungs- und Produktionscheckpoint")), None)
    if start is None:
        raise ValueError("ERROR_ONBOARDING_CURRENT_STATUS_MISSING")
    selected.extend(lines[start:])
    for index in range(2, len(selected)):
        if selected[index].startswith("### "):
            selected = selected[:index]
            break
    if not selected:
        raise ValueError("ERROR_ONBOARDING_CURRENT_STATUS_MISSING")
    return "\n".join(selected).strip()


def _prompt_version(path: Path) -> str:
    match = re.search(r"<version>([^<]+)</version>", path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"ERROR_ONBOARDING_PROMPT_VERSION_MISSING: {path.as_posix()}")
    return _sanitize(match.group(1))


def _prompt_classification(entry: dict[str, Any], active_registry_paths: set[str]) -> str:
    if entry["path"] in active_registry_paths:
        return "active_registry"
    if entry["path"] == "prompts/intake-project-v2-v1.3.0.xml.md":
        return "active_intake"
    if "compatibility-alias" in entry["tags"]:
        return "superseded_alias"
    if entry["lifecycle"] in {"historical", "superseded"}:
        return "historical_version"
    return "deferred_or_supporting"


def _onboarding_reference(
    root: Path,
    entries: list[dict[str, Any]],
    commit: str,
    policy: dict[str, Any],
) -> bytes:
    by_path = {entry["path"]: entry for entry in entries}
    sources: list[dict[str, Any]] = []
    for relative in ONBOARDING_SOURCE_PATHS:
        entry = by_path.get(relative)
        if entry is None:
            raise ValueError(f"ERROR_ONBOARDING_SOURCE_MISSING: {relative}")
        if not entry["default_retrieval"] or entry["lifecycle"] not in {
            "current_authority",
            "current_strategy",
            "active_plan",
        }:
            raise ValueError(f"ERROR_ONBOARDING_SOURCE_NOT_CURRENT: {relative}")
        data = _canonical_document_bytes(relative, (root / relative).read_bytes())
        if hashlib.sha256(data).hexdigest() != entry["content_sha256"]:
            raise ValueError(f"ERROR_ONBOARDING_SOURCE_HASH: {relative}")
        sources.append(entry)

    prompt_registry = _read_json(root / "standards/runtime/official-prompt-registry.json")
    official_prompts = [entry for entry in prompt_registry["entries"] if entry.get("active") is True]
    if len(official_prompts) != 9:
        raise ValueError("ERROR_ONBOARDING_PROMPT_REGISTRY_COUNT")
    active_prompt_paths = {str(entry["prompt_path"]) for entry in official_prompts}

    step_agent_registry = _read_json(root / "standards/runtime/step-agent-registry.json")
    step_agents = step_agent_registry.get("entries")
    if not isinstance(step_agents, list) or tuple(entry.get("step_id") for entry in step_agents) != INITIAL_ROUTE_STEPS:
        raise ValueError("ERROR_ONBOARDING_STEP_AGENT_ROUTE")

    status_excerpt = _current_status_excerpt(root)
    status_fence = _source_fence(status_excerpt)
    counts = Counter(entry["lifecycle"] for entry in entries)
    lines = [
        "# Heartweb onboarding reference",
        "",
        "**Author:** Raphael Rechberger",
        "**Lifecycle:** generated onboarding view",
        f"**Source commit:** `{commit}`",
        f"**Generator version:** `{GENERATOR_VERSION}`",
        f"**Registry version:** `{policy['registry_version']}`",
        f"**Inventory records:** {len(entries)}",
        "",
        "> This file is a deterministic generated onboarding view. It never overrides `00_admin/PROJECT_STATE.md`, active records in `00_admin/DECISIONS.md`, registered standards, contracts or Evidence. Every embedded source block identifies its canonical path, lifecycle, authority and raw SHA-256. Any drift makes `python scripts/build_repository_index.py --check` fail.",
        "",
        "## 1. Snapshot identity and authority order",
        "",
        "Authority is resolved before semantic similarity. Latest explicit Raphael instruction wins, followed by Project State, active Decisions and the ordered repository authorities below.",
        "",
    ]
    lines.extend(f"{index}. `{item}`" for index, item in enumerate(policy["authority_order"], start=1))
    lines.extend(
        [
            "",
            "Conflict rule: a lower authority never silently overwrites a higher authority. Historical, superseded and Evidence records are opt-in only.",
            "",
            "## 2. Product purpose and hard boundaries",
            "",
            "Heartweb is a client-neutral local SEO and GEO production system for one internal operator. It turns verified client inputs into strategy, architecture, keyword Evidence, roadmaps, professional Copywriter briefings, Developer specifications and deterministic handoff packages.",
            "",
            "- The system does not write final editorial copy. Human Heartweb Copywriters do.",
            "- The German Single-Admin Console is for the operator only.",
            "- Heartweb Core alone owns canonical workflow state, revisions, gates, approvals and releases.",
            "- External providers are reached only through versioned Provider Gateway operations. Missing data stops fail-closed.",
            "- Customer facts, claims, regions, Evidence and design stay in isolated customer workspaces, not shared framework logic.",
            "- Delivery is derived, deterministic and read-only. It cannot mutate workflow authority.",
            "- Repository consolidation into `master` is not Production Acceptance.",
            "",
            "## 3. Truthful current status and next gate",
            "",
            "The following excerpt is copied from the canonical Project State in this snapshot:",
            "",
            f"{status_fence}text",
            status_excerpt,
            status_fence,
            "",
            "The next Product gate remains M10: produce, review, approve and deliver the remaining real route without estimating missing provider data or implying unverified quality.",
            "",
            "## 4. Workflow and Step 3B boundary",
            "",
            "Initial production route:",
            "",
            "`0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery`",
            "",
            "Step 3B is not an initial-route Step agent. It runs only after publication at day 30, day 60 and day 90 when verified real performance data exists. It produces a versioned adjustment proposal and never mutates the released original plan.",
            "",
            "## 5. Architecture map",
            "",
            "| Component | Binding responsibility | Forbidden responsibility |",
            "|---|---|---|",
            "| Core | Canonical state, artifacts, revisions, Evidence, gates, approvals and releases | Provider calls and post-handoff staff management |",
            "| Operator Console | Typed commands and canonical German read models | Duplicating workflow rules or bypassing gates |",
            "| Provider Gateway | Versioned, geo-bound provider operations and persisted Evidence | Guessing missing values or exposing credentials |",
            "| Hermes Gateway | Isolated specialized Step-agent execution and controlled Heartweb tools | Canonical state mutation or credential ownership in prompts |",
            "| Delivery | Deterministic checkpoint and final packages, ZIP and manual Notion import | Approval, artifact mutation or workflow transition |",
            "| Notion | Human implementation tasks after approved Delivery | Calling back into Core for ordinary staff task changes |",
            "| n8n | Future orchestration, transport, Notion creation and scheduled Step 3B trigger | State authority or daily staff-task monitoring |",
            "",
            "## 6. Capability evidence levels",
            "",
            "| State | Capabilities |",
            "|---|---|",
            "| Implemented | V2 Core and Transition Service; revision, gate, approval and release services; Provider Gateway; specialized Hermes Step agents; German Console; deterministic Delivery and diagnostics |",
            "| Verified locally | Registry and hash bindings; focused Runtime and tool-scope closure; Step 0 release for the active controlled project; local Delivery and diagnostic contract evidence |",
            "| Unverified | Real Step 1 through Step 4B provider-backed output quality; complete active-project ZIP and Notion handoff; Production acceptance |",
            "| Planned before M10 closes | Produce, review, gate and deliver the remaining controlled route with no open P0/P1 |",
            "| Deferred after M10 | Live Notion adapter, n8n orchestration, Step 3B operations, public deployment, broad mobile polish and wider archetypes |",
            "| Absent | Production deployment, live Step-3B performance dataset and an approved complete real Golden Path |",
            "",
            "Evidence labels remain separate: unit or contract test, local service integration, deterministic fixture E2E, live-provider smoke, real-project Golden Path, external Notion or n8n E2E and Production acceptance.",
            "",
            "## 7. Git, authorship, safety, separation and testing rules",
            "",
            "- Raphael Rechberger is the sole author of project documents, deliverables and commits.",
            "- DEC-0031 authorizes this bounded repository consolidation, normal push, reachability-proven branch cleanup and fresh-clone continuation. No force-push is the default.",
            "- Released artifacts and accepted prompt meanings remain immutable. Edits create new versions or revisions.",
            "- Never commit customer workspaces, credentials, raw authorization headers, local `.env` files or sensitive recovery exports.",
            "- Never estimate missing provider metrics or fabricate claims, locations, approvals, Evidence, identities or completion state.",
            "- Run only the affected dependency closure required by `standards/testing/PROTOTYPE_TEST_POLICY.md`; do not restart broad matrices after a bounded failure.",
            "- Never use Em Dash or En Dash characters.",
            "",
            "## 8. Complete onboarding-critical source blocks",
            "",
            "Each block below contains the complete canonical source text with LF line endings and trailing line whitespace normalized for Git safety. The heading SHA-256 is calculated from these canonical text bytes; binary document bytes remain unchanged.",
            "",
        ]
    )
    for entry in sources:
        relative = entry["path"]
        raw_text = _canonical_document_bytes(relative, (root / relative).read_bytes()).decode("utf-8")
        text = "\n".join(line.rstrip(" \t") for line in raw_text.splitlines())
        fence = _source_fence(text)
        lines.extend(
            [
                f"### Source: [`{relative}`](../{relative})",
                "",
                f"- Lifecycle: `{entry['lifecycle']}`",
                f"- Authority: {entry['authority_level']}",
                f"- SHA-256: `{entry['content_sha256']}`",
                "",
                f"{fence}text",
                text.rstrip("\r\n"),
                fence,
                "",
            ]
        )

    prompt_entries = sorted((entry for entry in entries if entry["area"] == "prompts"), key=lambda entry: entry["path"])
    lines.extend(
        [
            "## 9. Complete prompt catalog",
            "",
            "| Classification | Prompt | Version | Lifecycle | SHA-256 |",
            "|---|---|---|---|---|",
        ]
    )
    for entry in prompt_entries:
        lines.append(
            f"| `{_prompt_classification(entry, active_prompt_paths)}` | [`{entry['path']}`](../{entry['path']}) | `{_prompt_version(root / entry['path'])}` | `{entry['lifecycle']}` | `{entry['content_sha256']}` |"
        )

    lines.extend(
        [
            "",
            "## 10. Active workflow prompt registry",
            "",
            "| Step | Prompt contract | Prompt path and hash | Output contracts |",
            "|---|---|---|---|",
        ]
    )
    for entry in official_prompts:
        outputs = "<br>".join(
            f"`{contract['contract_id']}@{contract['contract_version']}`: `{contract['contract_path']}` `{contract['contract_sha256']}`"
            for contract in entry["output_contracts"]
        )
        lines.append(
            f"| `{entry['step_id']}` | `{entry['prompt_id']}@{entry['prompt_version']}` | [`{entry['prompt_path']}`](../{entry['prompt_path']}) `{entry['prompt_sha256']}` | {outputs} |"
        )

    lines.extend(
        [
            "",
            "## 11. Initial-route Step agents, Worker Profiles and Tool Policies",
            "",
            "| Step | Agent contract | Worker Profile | Tool Policy | Required operations |",
            "|---|---|---|---|---|",
        ]
    )
    for entry in step_agents:
        policy_record = _read_json(root / entry["tool_policy_path"])
        operations = ", ".join(f"`{operation}`" for operation in policy_record["required_gateway_operations"])
        lines.append(
            f"| `{entry['step_id']}` | `{entry['agent_contract_id']}@{entry['agent_contract_version']}` | [`{entry['worker_profile_path']}`](../{entry['worker_profile_path']}) `{entry['worker_profile_version']}` `{entry['worker_profile_sha256']}` | [`{entry['tool_policy_path']}`](../{entry['tool_policy_path']}) `{entry['tool_policy_version']}` `{entry['tool_policy_sha256']}` | {operations} |"
        )

    lines.extend(
        [
            "",
            "## 12. Evolution rules",
            "",
            "A semantic prompt change requires coordinated review of prompt version, output schema version, validator, renderer, Quality Gate, positive and negative fixtures, Context Package, tool policy and migration or activation rule. Contracts stay strict on identity, lineage, Evidence and state while preserving strategic freedom inside accepted boundaries.",
            "",
            "New providers enter through the Provider Gateway. New agent tools require versioned operations and policies. New workflow Steps require Core graph, transitions, artifacts, gates, prompts, contracts, validators, renderers, tests and operator projection updates. The full authority is embedded above from `docs/09-extension-and-evolution-guide.md`.",
            "",
            "## 13. Local entry points",
            "",
            "```text",
            "python scripts/start_operator_console.py",
            "hermes -p heartweb-runtime gateway status",
            "curl http://127.0.0.1:8650/health",
            "curl http://127.0.0.1:8765/api/v2/readiness",
            "python scripts/smoke_operator_console.py",
            "python scripts/build_repository_index.py",
            "python scripts/build_repository_index.py --check",
            "python -m unittest tests.test_repository_index",
            "npm run build --prefix apps/operator-console",
            "hermes verify --json",
            "```",
            "",
            "Do not place credentials on a command line or in this repository. Use the isolated runtime profile and environment configuration. Shared diagnostics are under the local `var/operator-diagnostics/` contract and are not repository authority.",
            "",
            "## 14. Lifecycle counts",
            "",
        ]
    )
    for lifecycle in sorted(counts):
        lines.append(f"- `{lifecycle}`: {counts[lifecycle]}")

    lines.extend(
        [
            "",
            "## 15. Complete registry inventory",
            "",
            "Every registry source appears exactly once below. Evidence and audit bodies remain at their canonical paths and are not duplicated here.",
            "",
            "| # | Document | Lifecycle | Authority | Type | Summary | SHA-256 |",
            "|---:|---|---|---:|---|---|---|",
        ]
    )
    for index, entry in enumerate(entries, start=1):
        lines.append(
            f"| {index} | [`{entry['path']}`](../{entry['path']}) | `{entry['lifecycle']}` | {entry['authority_level']} | `{entry['document_type']}` | {_md_cell(entry['summary'])} | `{entry['content_sha256']}` |"
        )

    lines.extend(
        [
            "",
            "## 16. Branch and fresh-clone continuation",
            "",
            "- Canonical integration target: `master`.",
            "- Required continuation branch after remote and fresh-clone SHA verification: `feature/production-workflow-continuation`.",
            "- Exact live commit identity must be read from `git rev-parse master`, `git rev-parse origin/master` and the fresh clone. Do not infer it from prose.",
            "- Delete an old branch only after `git merge-base --is-ancestor <tip> master` succeeds or an explicit semantic-reconciliation record proves its content is represented and its tip is preserved in the final graph.",
            "- The external customer workspace is not inside the repository replacement and must remain unchanged.",
            "",
        ]
    )
    return "\n".join(lines).translate(DASH_TRANSLATION).encode("utf-8")


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
        "1. [`ONBOARDING_REFERENCE.md`](ONBOARDING_REFERENCE.md)",
        "2. [`SESSION_BOOTSTRAP.md`](SESSION_BOOTSTRAP.md)",
        "3. [`PROJECT_STATE.md`](PROJECT_STATE.md)",
        "4. [`DECISIONS.md`](DECISIONS.md)",
        "5. Select the active plan for the current task from [`.hermes/plans/INDEX.md`](../.hermes/plans/INDEX.md)",
        "6. Before test or review decisions, read [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md)",
        "7. Use `repository-index/DOCUMENT_REGISTRY.jsonl` for filtered RAG ingestion",
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

1. Read `00_admin/ONBOARDING_REFERENCE.md` for the generated complete snapshot.
2. Read `00_admin/PROJECT_STATE.md`.
3. Read active and superseding records in `00_admin/DECISIONS.md`.
4. Read `00_admin/REPOSITORY_INDEX.md`.
5. Select the active plan for the requested task from `.hermes/plans/INDEX.md`.
6. Before any test or review decision, read `standards/testing/PROTOTYPE_TEST_POLICY.md`.
7. Resolve exact standards, prompts and supporting Evidence through `00_admin/repository-index/DOCUMENT_REGISTRY.json`.
8. Read historical or audit material only when the task requires origin, rollback, prior decisions or failure reconstruction.

## Authority rule

Project State and active Decisions override entry documents, old plans, audit prose and semantic similarity. A search result is not an authority decision.

## Current snapshot warning

This generated view was built from source commit `{commit}`. Exact live branch and remote identity must be read from Git. Any record listed as `needs_reconciliation` in `00_admin/REPOSITORY_INDEX.md` is not current authority and blocks a clean integration.

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
        "00_admin/ONBOARDING_REFERENCE.md": _onboarding_reference(root, entries, commit, policy),
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
