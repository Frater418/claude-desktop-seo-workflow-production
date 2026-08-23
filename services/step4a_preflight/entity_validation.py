from __future__ import annotations

import re


_WIKIDATA_URI = re.compile(r"https://www\.wikidata\.org/wiki/Q[1-9][0-9]*\Z")


def validate_entity_bindings(briefing: dict[str, object]) -> list[dict[str, object]]:
    """Validate the typed entity ledger against its enhanced JSON-LD projection."""
    bindings = briefing.get("entity_bindings")
    if not isinstance(bindings, dict):
        return []
    about = bindings.get("about")
    mentions = bindings.get("mentions")
    errors = _binding_errors(about, mentions)
    jsonld = briefing.get("jsonld")
    if not isinstance(jsonld, dict) or jsonld.get("level") != "enhanced":
        return errors
    if not isinstance(about, list) or not isinstance(mentions, list) or not about or not mentions:
        errors.append(_error("ERROR_STEP4A_ENTITY_BINDINGS_ENHANCED_REQUIRED", "Enhanced GEO requires non-empty about and mentions entity bindings.", ["briefing", "entity_bindings"]))
        return errors
    graph = jsonld.get("graph")
    if not isinstance(graph, dict):
        return errors
    nodes = graph.get("@graph")
    if not isinstance(nodes, list):
        return errors
    node_by_id = _nodes_by_id(nodes)
    expected = _expected_bindings(about, mentions)
    for binding in expected:
        graph_node_id = binding.get("graph_node_id")
        wikidata_uri = binding.get("wikidata_uri")
        if not isinstance(graph_node_id, str) or len(node_by_id.get(graph_node_id, [])) != 1:
            errors.append(_error("ERROR_STEP4A_ENTITY_NODE_UNRESOLVED", "Each enhanced entity binding must resolve exactly once in @graph.", ["briefing", "entity_bindings"]))
        elif node_by_id[graph_node_id][0].get("sameAs") != wikidata_uri:
            errors.append(_error("ERROR_STEP4A_JSONLD_CORRESPONDENCE_MISMATCH", "Bound JSON-LD entity nodes must expose the matching canonical Wikidata sameAs URI.", ["briefing", "entity_bindings"]))
    main_nodes = [node for node in nodes if isinstance(node, dict) and "about" in node and "mentions" in node]
    if len(main_nodes) != 1 or not _matches_projection(main_nodes[0], about, mentions):
        errors.append(_error("ERROR_STEP4A_JSONLD_CORRESPONDENCE_MISMATCH", "Enhanced entity bindings must exactly match the main JSON-LD entity about and mentions projections.", ["briefing", "jsonld", "graph"]))
    return errors


def _binding_errors(about: object, mentions: object) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    if not isinstance(about, list) or not isinstance(mentions, list):
        return errors
    about_uris, about_nodes = _identifiers(about)
    mention_uris, mention_nodes = _identifiers(mentions)
    if any(not isinstance(item, dict) or not isinstance(item.get("wikidata_uri"), str) or _WIKIDATA_URI.fullmatch(item["wikidata_uri"]) is None for item in [*about, *mentions]):
        errors.append(_error("ERROR_STEP4A_WIKIDATA_URI_INVALID", "Entity bindings require canonical https://www.wikidata.org/wiki/Q<digits> URIs.", ["briefing", "entity_bindings"]))
    if len(about_uris) != len(about) or len(mention_uris) != len(mentions) or len(about_nodes) != len(about) or len(mention_nodes) != len(mentions) or about_uris & mention_uris or about_nodes & mention_nodes:
        errors.append(_error("ERROR_STEP4A_ENTITY_OVERLAP_OR_DUPLICATE", "Entity binding URIs and graph node IDs must be unique and non-overlapping across about and mentions.", ["briefing", "entity_bindings"]))
    return errors


def _identifiers(bindings: list[object]) -> tuple[set[str], set[str]]:
    uris = {binding.get("wikidata_uri") for binding in bindings if isinstance(binding, dict) and isinstance(binding.get("wikidata_uri"), str)}
    nodes = {binding.get("graph_node_id") for binding in bindings if isinstance(binding, dict) and isinstance(binding.get("graph_node_id"), str)}
    return uris, nodes


def _nodes_by_id(nodes: list[object]) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for node in nodes:
        if isinstance(node, dict) and isinstance(node.get("@id"), str):
            result.setdefault(node["@id"], []).append(node)
    return result


def _expected_bindings(about: list[object], mentions: list[object]) -> list[dict[str, object]]:
    return [binding for binding in [*about, *mentions] if isinstance(binding, dict)]


def _matches_projection(main: dict[str, object], about: list[object], mentions: list[object]) -> bool:
    return _same_references(_references(main.get("about")), _references(about)) and _same_references(_references(main.get("mentions")), _references(mentions))


def _references(values: object) -> list[tuple[str, str]] | None:
    if not isinstance(values, list):
        return None
    references: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, dict):
            return None
        node_id = value.get("@id", value.get("graph_node_id"))
        wikidata_uri = value.get("sameAs", value.get("wikidata_uri"))
        if not isinstance(node_id, str) or not isinstance(wikidata_uri, str):
            return None
        references.append((node_id, wikidata_uri))
    return references


def _same_references(actual: list[tuple[str, str]] | None, expected: list[tuple[str, str]] | None) -> bool:
    return actual is not None and expected is not None and len(actual) == len(expected) and set(actual) == set(expected)


def _error(code: str, message: str, path: list[object]) -> dict[str, object]:
    return {"code": code, "message": message, "path": path}
