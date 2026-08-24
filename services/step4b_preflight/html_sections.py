from __future__ import annotations

from services.step4b_preflight.html_values import attribute, classes, http_url, text


class SectionRenderError(ValueError):
    pass


def _section_open(section: dict, class_name: str, microdata: dict | None = None) -> str:
    attributes = (
        f'id="{attribute(section["section_id"])}" '
        f'data-section-role="{attribute(section["role"])}" '
        f'data-schema-node-id="{http_url(section["schema_node_id"])}" '
        f'class="{classes(class_name)}"'
    )
    if microdata is not None:
        attributes += f' itemscope itemtype="{http_url(microdata["itemtype"])}"'
    return f"<section {attributes}>"


def _paragraphs(values: list[str], itemprop: str | None = None) -> str:
    property_attribute = f' itemprop="{attribute(itemprop)}"' if itemprop else ""
    return "\n".join(f"<p{property_attribute}>{text(value)}</p>" for value in values)


def _table(table: dict, itemprop: str | None = None, class_name: str | None = None) -> str:
    property_attribute = f' itemprop="{attribute(itemprop)}"' if itemprop else ""
    class_attribute = f' class="{classes(class_name)}"' if class_name else ""
    headings = "".join(f'<th scope="col">{text(column)}</th>' for column in table["columns"])
    rows = "\n".join(f"<tr>{''.join(f'<td>{text(cell)}</td>' for cell in row)}</tr>" for row in table["rows"])
    return f"<table{class_attribute}{property_attribute}><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>"


def _cta(cta: dict) -> str:
    return f'<a class="btn btn-primary" href="#{attribute(cta["form_id"])}">{text(cta["label"])}</a>'


def _form(form: dict, consent: dict, cta: dict) -> str:
    form_id = attribute(form["form_id"])
    policy_id = attribute(consent["policy_id"])
    return "\n".join(
        (
            f'<form id="{form_id}" data-consent-required="true">',
            f'<label for="{form_id}-message">Ihre Nachricht</label>',
            f'<textarea class="form-control" id="{form_id}-message" name="message" required></textarea>',
            f'<div><input id="{form_id}-consent" name="consent" type="checkbox" required data-consent-policy="{policy_id}">',
            f'<label for="{form_id}-consent">Bitte stimmen Sie der Datenverarbeitung gemaess der Richtlinie zu.</label></div>',
            f'<button class="btn btn-primary" type="submit">{text(cta["label"])}</button>',
            "</form>",
        )
    )


def _service_area(page: dict, project: dict) -> str:
    service_area = page["service_area"]
    domain = project["entity_domain_gbp"]
    areas = {item["service_area_id"]: item for item in domain["service_areas"]}
    locations = {item["location_id"]: item for item in domain["physical_locations"]}
    match service_area["mode"]:
        case "service_area":
            items = []
            for area_id in sorted(service_area["service_area_ids"]):
                area = areas.get(area_id)
                name = area["name"] if area is not None else area_id
                items.append(f'<li data-service-area-id="{attribute(area_id)}">{text(name)}</li>')
            return f"<ul>{''.join(items)}</ul>"
        case "physical_location":
            items = []
            for location_id in sorted(service_area["physical_location_ids"]):
                location = locations.get(location_id)
                if location is None:
                    raise SectionRenderError("Physical location is not available in the validated project.")
                label = ", ".join((location["name"], location["locality"], location["country_code"]))
                items.append(f'<li data-physical-location-id="{attribute(location_id)}">{text(label)}</li>')
            return f"<ul>{''.join(items)}</ul>"
        case unexpected:
            raise SectionRenderError(f"Unsupported service-area mode: {unexpected}")


def _render_hero(section: dict, ctas: dict[str, dict]) -> str:
    content = section["content"]
    return "\n".join(
        (
            _section_open(section, "hero"),
            '<div class="container">',
            f"<h1>{text(section['heading'])}</h1>",
            f'<p class="lead">{text(content["summary"])}</p>',
            _cta(ctas[content["primary_cta_id"]]),
            "</div>",
            "</section>",
        )
    )


def _render_text(section: dict) -> str:
    return "\n".join((_section_open(section, "section"), '<div class="container">', f"<h2>{text(section['heading'])}</h2>", _paragraphs(section["content"]["paragraphs"]), "</div>", "</section>"))


def _render_definition(section: dict) -> str:
    microdata = section["microdata"]
    class_name = classes("definition-block", *section["component_classes"])
    return "\n".join((_section_open(section, "section", microdata), '<div class="container">', f'<div class="{class_name}">', f'<h2 itemprop="{attribute(microdata["heading_itemprop"])}">{text(section["heading"])}</h2>', _paragraphs(section["content"]["paragraphs"], microdata["body_itemprop"]), "</div>", "</div>", "</section>"))


def _render_evidence(section: dict) -> str:
    microdata = section["microdata"]
    content = section["content"]
    class_name = classes("evidence-container", *section["component_classes"])
    if "data_points" in content:
        details = "".join(f'<dt>{text(point["label"])}</dt><dd>{text(point["value"])}</dd>' for point in content["data_points"])
        evidence = f'<dl itemprop="{attribute(microdata["content_itemprop"])}">{details}</dl>'
    else:
        evidence = _table(content["table"], microdata["content_itemprop"])
    return "\n".join((_section_open(section, "section", microdata), '<div class="container">', f'<div class="{class_name}">', f'<h2 itemprop="{attribute(microdata["heading_itemprop"])}">{text(section["heading"])}</h2>', _paragraphs(content["paragraphs"], microdata["body_itemprop"]), evidence, "</div>", "</div>", "</section>"))


def _render_comparison(section: dict) -> str:
    microdata = section["microdata"]
    table = section["content"]["table"]
    wrapper_classes = classes("comparison-table-wrapper", *section["component_classes"])
    table_classes = classes("comparison-table", *table["component_classes"])
    return "\n".join((_section_open(section, "section", microdata), '<div class="container">', f'<h2 itemprop="{attribute(microdata["heading_itemprop"])}">{text(section["heading"])}</h2>', f'<div class="{wrapper_classes}">', _table(table, microdata["table_itemprop"], table_classes), "</div>", "</div>", "</section>"))


def _render_faq(section: dict) -> str:
    items = "\n".join(f'<article class="faq-item"><h3 class="faq-question">{text(item["question"])}</h3><p class="faq-answer">{text(item["answer"])}</p></article>' for item in section["content"]["items"])
    return "\n".join((_section_open(section, "section"), '<div class="container">', f"<h2>{text(section['heading'])}</h2>", f'<div class="faq-list">{items}</div>', "</div>", "</section>"))


def _render_conversion(section: dict, page: dict) -> str:
    content = section["content"]
    ctas = {item["cta_id"]: item for item in page["ctas"]}
    forms = {item["form_id"]: item for item in page["forms"]}
    trust = "".join(f'<li class="card card-trust" data-trust-signal-id="{attribute(signal["trust_signal_id"])}">{text(signal["label"])}</li>' for signal in page["conversion"]["trust_signals"])
    actions = "\n".join(_cta(ctas[cta_id]) for cta_id in content["cta_ids"])
    rendered_forms = "\n".join(_form(forms[form_id], page["consent"], next(cta for cta in ctas.values() if cta["form_id"] == form_id)) for form_id in content["form_ids"])
    return "\n".join((_section_open(section, "section"), '<div class="container">', f"<h2>{text(section['heading'])}</h2>", f'<ul class="grid grid-cols-3">{trust}</ul>', actions, rendered_forms, "</div>", "</section>"))


def _render_related(section: dict, links: dict[str, dict]) -> str:
    selected = sorted((links[link_id] for link_id in section["content"]["sibling_link_ids"]), key=lambda link: link["link_id"])
    items = "\n".join(f'<li><a href="{http_url(link["url"])}">{text(link["label"])}</a></li>' for link in selected)
    return "\n".join((_section_open(section, "section"), '<div class="container">', f"<h2>{text(section['heading'])}</h2>", f'<nav aria-label="{text(section["heading"])}"><ul>{items}</ul></nav>', "</div>", "</section>"))


def render_sections(page: dict, project: dict) -> str:
    ctas = {item["cta_id"]: item for item in page["ctas"]}
    forms = {item["form_id"]: item for item in page["forms"]}
    links = {item["link_id"]: item for item in page["sibling_links"]}
    rendered = []
    for section in page["sections"]:
        match section["role"]:
            case "hero":
                rendered.append(_render_hero(section, ctas))
            case "direct_answer":
                rendered.append(_render_text(section))
            case "definition":
                rendered.append(_render_definition(section))
            case "evidence":
                rendered.append(_render_evidence(section))
            case "comparison":
                rendered.append(_render_comparison(section))
            case "service_area":
                rendered.append("\n".join((_section_open(section, "section"), '<div class="container">', f"<h2>{text(section['heading'])}</h2>", _service_area(page, project), "</div>", "</section>")))
            case "faq":
                rendered.append(_render_faq(section))
            case "conversion":
                rendered.append(_render_conversion(section, page))
            case "related_links":
                rendered.append(_render_related(section, links))
            case unexpected:
                raise SectionRenderError(f"Unsupported section role: {unexpected}")
    return "\n".join(rendered)


def render_tracking_slots(page: dict) -> str:
    slots = sorted(page["tracking_slots"], key=lambda slot: slot["slot_id"])
    return "\n".join(f'<div data-tracking-slot="{attribute(slot["slot_id"])}" data-consent-category="{attribute(slot["consent_category"])}" aria-hidden="true"></div>' for slot in slots)
