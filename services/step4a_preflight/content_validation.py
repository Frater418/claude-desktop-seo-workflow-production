from __future__ import annotations


def validate_content_semantics(briefing: dict[str, object], ledger: dict[str, object]) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    hero = briefing.get("hero_direct_answer")
    if isinstance(hero, dict) and isinstance(hero.get("text"), str) and not 50 <= _word_count(hero["text"]) <= 70:
        errors.append(_error("ERROR_STEP4A_HERO_WORD_COUNT_INVALID", "Hero Direct Answer must contain 50 to 70 normalized words.", ["briefing", "hero_direct_answer", "text"]))
    evidence_inventory = _evidence_inventory(briefing, ledger)
    _validate_triples(briefing.get("semantic_triples"), evidence_inventory, errors)
    _validate_evidence_containers(briefing.get("evidence_containers"), evidence_inventory, errors)
    if not _has_complete_briefing_guidance(briefing.get("briefing_sections")):
        errors.append(_error("ERROR_STEP4A_BRIEFING_GUIDANCE_INCOMPLETE", "Copywriter briefing sections and definitive language guidance must be complete.", ["briefing", "briefing_sections"]))
    return errors


def _validate_triples(triples: object, evidence_inventory: set[str], errors: list[dict[str, object]]) -> None:
    if not isinstance(triples, list):
        return
    if not 15 <= len(triples) <= 20:
        errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_CARDINALITY_INVALID", "Semantic triples must contain 15 to 20 entries.", ["briefing", "semantic_triples"]))
    triple_ids: set[str] = set()
    normalized_triples: set[tuple[str, str, str]] = set()
    for index, triple in enumerate(triples):
        if not isinstance(triple, dict):
            errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_TEXT_INVALID", "Semantic triple text must be non-whitespace.", ["briefing", "semantic_triples", index]))
            continue
        triple_id = triple.get("triple_id")
        if isinstance(triple_id, str):
            if triple_id in triple_ids:
                errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_ID_DUPLICATE", "Semantic triple IDs must be unique.", ["briefing", "semantic_triples", index, "triple_id"]))
            triple_ids.add(triple_id)
        normalized = _normalized_triple(triple)
        if normalized is None:
            errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_TEXT_INVALID", "Semantic triple text must be non-whitespace.", ["briefing", "semantic_triples", index]))
        elif normalized in normalized_triples:
            errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_DUPLICATE", "Semantic triples must be unique after whitespace normalization and case folding.", ["briefing", "semantic_triples", index]))
        else:
            normalized_triples.add(normalized)
        if _has_unresolved_ids(triple.get("evidence_ids"), evidence_inventory):
            errors.append(_error("ERROR_STEP4A_SEMANTIC_TRIPLE_EVIDENCE_UNRESOLVED", "Semantic triple evidence IDs must resolve to the declared Step 4A evidence inventory.", ["briefing", "semantic_triples", index, "evidence_ids"]))


def _validate_evidence_containers(containers: object, evidence_inventory: set[str], errors: list[dict[str, object]]) -> None:
    if not isinstance(containers, list):
        return
    section_ids: set[str] = set()
    for index, container in enumerate(containers):
        path = ["briefing", "evidence_containers", index]
        if not isinstance(container, dict):
            errors.append(_error("ERROR_STEP4A_EVIDENCE_FORM_INVALID", "Evidence containers require exactly one data-points or table form.", path))
            continue
        section_id = container.get("section_id")
        if isinstance(section_id, str):
            normalized_section_id = " ".join(section_id.split()).casefold()
            if normalized_section_id in section_ids:
                errors.append(_error("ERROR_STEP4A_EVIDENCE_SECTION_ID_DUPLICATE", "Evidence container section IDs must be unique after normalization.", [*path, "section_id"]))
            section_ids.add(normalized_section_id)
        body = container.get("body")
        if isinstance(body, str) and not 130 <= _word_count(body) <= 160:
            errors.append(_error("ERROR_STEP4A_EVIDENCE_BODY_WORD_COUNT_INVALID", "Evidence container bodies must contain 130 to 160 normalized words.", [*path, "body"]))
        container_evidence_ids = container.get("evidence_ids")
        if _has_unresolved_ids(container_evidence_ids, evidence_inventory):
            errors.append(_error("ERROR_STEP4A_EVIDENCE_UNRESOLVED", "Evidence container IDs must resolve to the declared Step 4A evidence inventory.", [*path, "evidence_ids"]))
        _validate_evidence_form(container, container_evidence_ids, evidence_inventory, path, errors)


def _validate_evidence_form(container: dict[str, object], container_evidence_ids: object, evidence_inventory: set[str], path: list[object], errors: list[dict[str, object]]) -> None:
    has_data_points = "data_points" in container
    has_table = "table" in container
    if has_data_points == has_table:
        errors.append(_error("ERROR_STEP4A_EVIDENCE_FORM_INVALID", "Evidence containers require exactly one data-points or table form.", path))
    data_points = container.get("data_points")
    if isinstance(data_points, list):
        declared_ids = {value for value in container_evidence_ids if isinstance(value, str)} if isinstance(container_evidence_ids, list) else set()
        for point_index, data_point in enumerate(data_points):
            if isinstance(data_point, dict) and _has_unresolved_ids(data_point.get("source_evidence_ids"), evidence_inventory | declared_ids, declared_ids):
                errors.append(_error("ERROR_STEP4A_EVIDENCE_UNRESOLVED", "Data-point source evidence IDs must resolve and belong to their evidence container.", [*path, "data_points", point_index, "source_evidence_ids"]))
    table = container.get("table")
    if isinstance(table, dict):
        columns = table.get("columns")
        rows = table.get("rows")
        if isinstance(columns, list) and isinstance(rows, list) and any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
            errors.append(_error("ERROR_STEP4A_EVIDENCE_TABLE_WIDTH_INVALID", "Each evidence table row must have the same width as its columns.", [*path, "table", "rows"]))


def _has_unresolved_ids(ids: object, evidence_inventory: set[str], allowed_ids: set[str] | None = None) -> bool:
    return isinstance(ids, list) and any(not isinstance(evidence_id, str) or evidence_id not in evidence_inventory or allowed_ids is not None and evidence_id not in allowed_ids for evidence_id in ids)


def _word_count(text: str) -> int:
    return len(" ".join(text.split()).split())


def _error(code: str, message: str, path: list[object]) -> dict[str, object]:
    return {"code": code, "message": message, "path": path}


def _evidence_inventory(briefing: dict[str, object], ledger: dict[str, object]) -> set[str]:
    return {evidence_id for evidence_ids in (briefing.get("evidence_ids"), ledger.get("evidence_ids")) if isinstance(evidence_ids, list) for evidence_id in evidence_ids if isinstance(evidence_id, str)}


def _normalized_triple(triple: dict[str, object]) -> tuple[str, str, str] | None:
    subject = triple.get("subject")
    predicate = triple.get("predicate")
    value = triple.get("object")
    if not isinstance(subject, str) or not subject.strip() or not isinstance(predicate, str) or not predicate.strip() or not isinstance(value, str) or not value.strip():
        return None
    return (" ".join(subject.split()).casefold(), " ".join(predicate.split()).casefold(), " ".join(value.split()).casefold())


def _has_complete_briefing_guidance(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    text_fields = ("audience", "search_intent", "primary_keyword", "content_goal", "tone", "cta_guidance", "internal_link_guidance", "copywriter_instructions")
    list_fields = ("secondary_keywords", "outline", "publication_checklist")
    guidance = value.get("definitive_language_guidance")
    return (
        all(isinstance(value.get(field), str) and value[field].strip() for field in text_fields)
        and all(isinstance(value.get(field), list) and value[field] and all(isinstance(item, str) and item.strip() for item in value[field]) and len(value[field]) == len(set(value[field])) for field in list_fields)
        and isinstance(guidance, dict)
        and guidance.get("required") is True
        and all(isinstance(guidance.get(field), list) and guidance[field] and all(isinstance(item, str) and item.strip() for item in guidance[field]) for field in ("preferred_patterns", "prohibited_patterns"))
        and isinstance(guidance.get("rationale"), str)
        and bool(guidance["rationale"].strip())
    )
