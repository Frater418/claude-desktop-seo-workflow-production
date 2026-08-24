from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse


__author__ = "Raphael Rechberger"


REQUIRED_FIELDS = {
    "LocalBusiness": ["@type", "name", "address"],
    "MedicalBusiness": ["@type", "name", "address"],
    "Article": ["@type", "headline", "author", "datePublished"],
    "BlogPosting": ["@type", "headline", "author", "datePublished"],
    "TechArticle": ["@type", "headline", "author", "datePublished"],
    "FAQPage": ["@type", "mainEntity"],
    "BreadcrumbList": ["@type", "itemListElement"],
    "HowTo": ["@type", "name", "step"],
    "Product": ["@type", "name"],
    "Person": ["@type", "name"],
    "VideoObject": ["@type", "name", "uploadDate"],
    "DefinedTerm": ["@type", "name", "description"],
    "Dataset": ["@type", "name", "description", "variableMeasured"],
    "ItemList": ["@type", "name", "itemListElement"],
}


def _issue(level: str, code: str, message: str, path: str = "") -> dict:
    return {"level": level, "code": code, "message": message, "path": path}


def _is_http_url(value: str) -> bool:
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _validate_url_field(obj: dict, field: str, path: str, issues: list) -> None:
    value = obj.get(field)
    if value is not None and (not isinstance(value, str) or not _is_http_url(value)):
        issues.append(_issue("format", "ERROR_SCHEMA_URL_INVALID", f"Field '{field}' must be an absolute HTTP or HTTPS URL.", f"{path}/{field}"))


def _validate_entity_reference(item, path: str, require_wikidata: bool) -> list:
    issues = []
    if not isinstance(item, dict) or not item.get("@type") or not item.get("name"):
        return [_issue("geo", "ERROR_SCHEMA_ABOUT_INVALID" if require_wikidata else "ERROR_SCHEMA_MENTION_INVALID", "Entity reference must be an object with non-empty '@type' and 'name'.", path)]
    same_as = item.get("sameAs")
    if not isinstance(same_as, str) or not _is_http_url(same_as):
        issues.append(_issue("geo", "ERROR_SCHEMA_ABOUT_INVALID" if require_wikidata else "ERROR_SCHEMA_MENTION_INVALID", "Entity reference requires an absolute HTTP or HTTPS 'sameAs' URL.", f"{path}/sameAs"))
    elif require_wikidata and not re.fullmatch(r"https://www\.wikidata\.org/wiki/Q[1-9][0-9]*", same_as):
        issues.append(_issue("geo", "ERROR_SCHEMA_WIKIDATA_INVALID", "Strict GEO mode requires a canonical Wikidata entity URI in 'about'.", f"{path}/sameAs"))
    return issues


def validate_schema_object(obj: dict, strict_geo: bool = False, path: str = "") -> list:
    issues = []
    if not isinstance(obj, dict):
        return [_issue("contract", "ERROR_SCHEMA_OBJECT_INVALID", "Schema node must be an object.", path)]
    if "@graph" in obj:
        graph_items = obj["@graph"]
        if not isinstance(graph_items, list) or not graph_items:
            return [_issue("contract", "ERROR_SCHEMA_GRAPH_INVALID", "'@graph' must be a non-empty list of schema objects.", f"{path}/@graph")]
        for index, sub in enumerate(graph_items):
            issues.extend(validate_schema_object(sub, strict_geo=strict_geo, path=f"{path}/@graph/{index}"))
        return issues
    schema_type = obj.get("@type")
    if not schema_type:
        return [_issue("contract", "ERROR_SCHEMA_TYPE_MISSING", "Schema object has no '@type'.", f"{path}/@type")]
    types = [schema_type] if isinstance(schema_type, str) else schema_type
    if not isinstance(types, list) or not types or not all(isinstance(value, str) for value in types):
        return [_issue("contract", "ERROR_SCHEMA_TYPE_INVALID", "'@type' must be a string or non-empty string list.", f"{path}/@type")]
    for schema_name in types:
        if schema_name not in REQUIRED_FIELDS:
            issues.append(_issue("contract", "ERROR_SCHEMA_TYPE_UNKNOWN", f"Unsupported schema type '{schema_name}'.", f"{path}/@type"))
            continue
        for required in REQUIRED_FIELDS[schema_name]:
            if required not in obj or obj[required] is None or str(obj[required]).strip() in {"", "[]", "{}"}:
                issues.append(_issue("contract", "ERROR_SCHEMA_REQUIRED_FIELD_MISSING", f"Type '{schema_name}' requires non-empty field '{required}'.", f"{path}/{required}"))
    for url_field in ("@id", "url"):
        _validate_url_field(obj, url_field, path, issues)
    for date_field in ("datePublished", "dateModified", "uploadDate"):
        if date_field in obj and (not isinstance(obj[date_field], str) or not _is_iso_datetime(obj[date_field])):
            issues.append(_issue("format", "ERROR_SCHEMA_DATE_INVALID", f"Field '{date_field}' must be an ISO 8601 date or datetime.", f"{path}/{date_field}"))
    if any(schema_name in {"Article", "BlogPosting", "TechArticle"} for schema_name in types):
        author = obj.get("author")
        if not isinstance(author, dict) or author.get("@type") not in {"Person", "Organization"} or not author.get("name"):
            issues.append(_issue("contract", "ERROR_SCHEMA_AUTHOR_INVALID", "Article author must be a Person or Organization object with a name.", f"{path}/author"))
    if any(schema_name in {"LocalBusiness", "MedicalBusiness"} for schema_name in types):
        address = obj.get("address")
        required_address = ("streetAddress", "addressLocality", "addressCountry")
        if not isinstance(address, dict) or address.get("@type") != "PostalAddress" or any(not address.get(field) for field in required_address):
            issues.append(_issue("contract", "ERROR_SCHEMA_ADDRESS_INVALID", "Business address must be a PostalAddress with streetAddress, addressLocality and addressCountry.", f"{path}/address"))
    if "FAQPage" in types:
        entities = obj.get("mainEntity", [])
        if not isinstance(entities, list) or not entities:
            issues.append(_issue("contract", "ERROR_SCHEMA_FAQ_INVALID", "FAQPage mainEntity must be a non-empty list.", f"{path}/mainEntity"))
        else:
            for index, question in enumerate(entities):
                question_path = f"{path}/mainEntity/{index}"
                if not isinstance(question, dict) or question.get("@type") != "Question" or not question.get("name"):
                    issues.append(_issue("contract", "ERROR_SCHEMA_FAQ_INVALID", "FAQ item must be a named Question.", question_path))
                    continue
                answer = question.get("acceptedAnswer")
                if not isinstance(answer, dict) or answer.get("@type") != "Answer" or not answer.get("text"):
                    issues.append(_issue("contract", "ERROR_SCHEMA_FAQ_INVALID", "FAQ Question requires a non-empty accepted Answer.", f"{question_path}/acceptedAnswer"))
    if "BreadcrumbList" in types:
        elements = obj.get("itemListElement", [])
        if not isinstance(elements, list) or not elements:
            issues.append(_issue("contract", "ERROR_SCHEMA_BREADCRUMB_INVALID", "BreadcrumbList requires non-empty itemListElement.", f"{path}/itemListElement"))
        else:
            for index, item in enumerate(elements):
                item_path = f"{path}/itemListElement/{index}"
                if not isinstance(item, dict) or item.get("@type") != "ListItem" or not isinstance(item.get("position"), int) or item["position"] < 1 or not item.get("name"):
                    issues.append(_issue("contract", "ERROR_SCHEMA_BREADCRUMB_INVALID", "Breadcrumb item requires ListItem type, positive integer position and name.", item_path))
                    continue
                if "item" in item and (not isinstance(item["item"], str) or not _is_http_url(item["item"])):
                    issues.append(_issue("format", "ERROR_SCHEMA_URL_INVALID", "Breadcrumb item URL must be absolute HTTP or HTTPS.", f"{item_path}/item"))
    if strict_geo and any(schema_name in {"Article", "BlogPosting", "TechArticle", "LocalBusiness", "MedicalBusiness"} for schema_name in types):
        about = obj.get("about")
        if any(schema_name in {"Article", "BlogPosting", "TechArticle"} for schema_name in types) and (not isinstance(about, list) or not about):
            issues.append(_issue("geo", "ERROR_SCHEMA_ABOUT_INVALID", "Strict GEO mode requires a non-empty 'about' list for article types.", f"{path}/about"))
        elif about is not None:
            about_items = about if isinstance(about, list) else [about]
            for index, item in enumerate(about_items):
                issues.extend(_validate_entity_reference(item, f"{path}/about/{index}", require_wikidata=True))
        mentions = obj.get("mentions")
        if mentions is not None:
            mention_items = mentions if isinstance(mentions, list) else [mentions]
            for index, item in enumerate(mention_items):
                issues.extend(_validate_entity_reference(item, f"{path}/mentions/{index}", require_wikidata=False))
    return issues
