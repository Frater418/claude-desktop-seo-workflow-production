#!/usr/bin/env python3
"""
Capacity Matrix Solver for 120-Day SEO & GEO Content Plans
Autor: Raphael Rechberger
Version: 1.3.0

Deterministischer Kapazitaets- und Prioritaets-Solver fuer die Erstellung
von 120-Tage-Roadmaps mit nativer Generative Engine Optimization (GEO) Unterstuetzung.
Horizont 17 Wochen, Obergrenze 15 Stunden pro Woche.
Die gemessene Spanne steht im Plankopf.
Verhindert LLM-Arithmetik- und Rundungsfehler und generiert automatische Verlinkungs-Maps.
"""

import sys
import os
import json
import csv
import argparse
from pathlib import Path

EFFORT_WEIGHTS = {
    "Pillar-Page": 8.0,
    "Pillar": 8.0,
    "Data-Hub": 5.0,
    "Entity-Anchor": 4.0,
    "FAQ-Hub": 3.0,
    "Blogartikel": 3.0,
    "Blog": 3.0,
    "Ratgeber": 3.0,
    "Comparison-Table": 2.0,
    "Vergleichstabelle": 2.0,
    "Landingpage": 1.25,
    "Standort-Landingpage": 1.25,
    "FAQ": 1.0,
    "Ergaenzungsseite": 1.0
}

RELEVANCE_FACTORS = {
    "Lokal_Landingpage": 4.0,
    "Data-Hub": 3.5,
    "Kosten": 3.0,
    "Transaktional": 3.0,
    "Entity-Anchor": 3.0,
    "Vergleich": 2.5,
    "Comparison-Table": 2.5,
    "FAQ-Hub": 2.5,
    "Entscheidung": 2.0,
    "Lokal_Blog": 2.0,
    "Informational": 1.0,
    "W-Fragen": 1.0,
    "Erfahrung": 1.0,
    "Vertrauen": 1.0
}


class CapacityValidationError(ValueError):
    """Structured fail-fast error for invalid solver inputs."""

    def __init__(self, code: str, message: str, item_index: int | None = None, field: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.item_index = item_index
        self.field = field

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "item_index": self.item_index,
            "field": self.field,
        }


def _required_value(item: dict, aliases: tuple[str, ...], canonical: str, item_index: int):
    for key in aliases:
        if key in item and item[key] is not None and str(item[key]).strip() != "":
            return item[key]
    raise CapacityValidationError(
        "ERROR_SOLVER_REQUIRED_FIELD_MISSING",
        f"Item #{item_index} is missing required field '{canonical}'.",
        item_index=item_index,
        field=canonical,
    )


def _non_negative_float(value, canonical: str, item_index: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CapacityValidationError(
            "ERROR_SOLVER_METRIC_INVALID",
            f"Item #{item_index} field '{canonical}' must be numeric.",
            item_index=item_index,
            field=canonical,
        ) from exc
    if parsed < 0:
        raise CapacityValidationError(
            "ERROR_SOLVER_METRIC_INVALID",
            f"Item #{item_index} field '{canonical}' must be non-negative.",
            item_index=item_index,
            field=canonical,
        )
    return parsed


def _explicit_bool(value, canonical: str, item_index: int) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "ja"}:
        return True
    if normalized in {"false", "0", "no", "nein"}:
        return False
    raise CapacityValidationError(
        "ERROR_SOLVER_BOOLEAN_INVALID",
        f"Item #{item_index} field '{canonical}' must be an explicit boolean.",
        item_index=item_index,
        field=canonical,
    )

def calculate_score(search_volume: float, difficulty: float, category: str, content_type: str, is_mandatory: bool, info_gain: float = 0.0, entity_density: float = 0.0) -> float:
    cat_clean = str(category or "").strip()
    c_type_clean = str(content_type or "").strip()
    
    if "landingpage" in c_type_clean.lower() and ("lokal" in cat_clean.lower() or is_mandatory):
        factor = RELEVANCE_FACTORS["Lokal_Landingpage"]
    elif "data-hub" in c_type_clean.lower():
        factor = RELEVANCE_FACTORS["Data-Hub"]
    elif "entity-anchor" in c_type_clean.lower():
        factor = RELEVANCE_FACTORS["Entity-Anchor"]
    elif "comparison" in c_type_clean.lower() or "vergleich" in c_type_clean.lower() or "vergleich" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Comparison-Table"]
    elif "faq-hub" in c_type_clean.lower() or "faq_hub" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["FAQ-Hub"]
    elif "kosten" in cat_clean.lower() or "transaktion" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Kosten"]
    elif "lokal" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Lokal_Blog"]
    else:
        factor = 1.0
        
    base_score = (float(search_volume or 0) / (float(difficulty or 0) + 1.0)) * factor
    
    # GEO-Multiplikatoren fuer Information Gain und Entitaetsdichte
    gain_bonus = 1.0 + (max(0.0, float(info_gain or 0) - 1.0) * 0.08)
    entity_bonus = 1.0 + (min(20.0, float(entity_density or 0)) * 0.02)
    
    score = base_score * gain_bonus * entity_bonus
    return round(score, 2)

def load_items_from_file(file_path: Path) -> list:
    if not file_path.exists():
        raise FileNotFoundError(f"Input-Datei nicht gefunden: {file_path}")
        
    ext = file_path.suffix.lower()
    items = []
    
    if ext == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "items" in data:
            items = data["items"]
    elif ext == ".csv":
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(row)
    else:
        raise ValueError(f"Nicht unterstuetztes Format: {ext}. Bitte .json oder .csv verwenden.")
        
    if not isinstance(items, list):
        raise CapacityValidationError(
            "ERROR_SOLVER_INPUT_SHAPE_INVALID",
            "Input must be a JSON array, a JSON object with an 'items' array, or a CSV table.",
        )
    return items

def solve_capacity_plan(items: list, hours_min=10.0, hours_max=15.0, total_weeks=17):
    if not isinstance(items, list) or not items:
        raise CapacityValidationError(
            "ERROR_SOLVER_EMPTY_INPUT",
            "At least one validated content item is required to create a capacity plan.",
        )
    if not isinstance(total_weeks, int) or total_weeks < 1:
        raise CapacityValidationError(
            "ERROR_SOLVER_CAPACITY_INVALID",
            "The planning horizon must be a positive integer number of weeks.",
            field="total_weeks",
        )
    if hours_min <= 0 or hours_max <= 0 or hours_min > hours_max:
        raise CapacityValidationError(
            "ERROR_SOLVER_CAPACITY_INVALID",
            "Capacity requires positive values and hours_min must not exceed hours_max.",
            field="hours_min/hours_max",
        )
        
    processed = []
    for item_index, item in enumerate(items):
        if not isinstance(item, dict):
            raise CapacityValidationError(
                "ERROR_SOLVER_ITEM_INVALID",
                f"Item #{item_index} must be an object.",
                item_index=item_index,
            )
        pillar = str(_required_value(item, ("Pillar_Thema", "pillar"), "pillar", item_index)).strip()
        title = str(_required_value(item, ("Cluster_Thema", "title"), "title", item_index)).strip()
        keyword = str(_required_value(item, ("Ziel_Keyword", "keyword"), "keyword", item_index)).strip()
        cat = str(_required_value(item, ("Kategorie", "category"), "category", item_index)).strip()
        c_type = str(_required_value(item, ("Content_Type", "content_type"), "content_type", item_index)).strip()
        sv = _non_negative_float(
            _required_value(item, ("Suchvolumen", "search_volume"), "search_volume", item_index),
            "search_volume",
            item_index,
        )
        kd = _non_negative_float(
            _required_value(item, ("Difficulty", "difficulty"), "difficulty", item_index),
            "difficulty",
            item_index,
        )
        if c_type not in EFFORT_WEIGHTS:
            raise CapacityValidationError(
                "ERROR_SOLVER_CONTENT_TYPE_UNKNOWN",
                f"Item #{item_index} uses unknown content type '{c_type}'.",
                item_index=item_index,
                field="content_type",
            )
        
        info_gain = float(item.get("Information_Gain_Score", item.get("information_gain", item.get("info_gain", 0))) or 0)
        entity_density = float(item.get("Entity_Density_Score", item.get("entity_density", 0)) or 0)
        geo_type = str(item.get("GEO_Typ", item.get("geo_type", "Standard-SEO")))
        engine_target = str(item.get("Engine_Ziel", item.get("engine_target", "Google AI Overviews / Search")))
        
        is_mand_raw = _required_value(
            item,
            ("Is_Mandatory_Location", "is_mandatory"),
            "is_mandatory",
            item_index,
        )
        is_mand = _explicit_bool(is_mand_raw, "is_mandatory", item_index)
        
        score = calculate_score(sv, kd, cat, c_type, is_mand, info_gain, entity_density)
        effort = EFFORT_WEIGHTS[c_type]
        
        processed.append({
            "pillar": pillar,
            "title": title,
            "keyword": keyword,
            "search_volume": int(sv),
            "difficulty": int(kd),
            "content_type": c_type,
            "geo_type": geo_type,
            "engine_target": engine_target,
            "category": cat,
            "is_mandatory": is_mand,
            "score": score,
            "effort_hours": effort,
            "word_count": 1500 if "blog" in c_type.lower() or "ratgeber" in c_type.lower() else (800 if "landing" in c_type.lower() else 2500)
        })

    mand_items = sorted([i for i in processed if i["is_mandatory"]], key=lambda x: x["score"], reverse=True)
    other_items = sorted([i for i in processed if not i["is_mandatory"]], key=lambda x: x["score"], reverse=True)

    weeks = [{"week": w + 1, "phase": 1 if w < 4 else (2 if w < 8 else (3 if w < 13 else 4)), "items": [], "hours": 0.0} for w in range(total_weeks)]
    
    # Lokale Pflichtseiten auf Phase 1 & 2 verteilen
    phase_1_2_weeks = weeks[:8]
    mand_idx = 0
    while mand_items and mand_idx < len(mand_items):
        item = mand_items[mand_idx]
        best_week = min(phase_1_2_weeks, key=lambda w: w["hours"])
        if best_week["hours"] + item["effort_hours"] <= hours_max:
            best_week["items"].append(item)
            best_week["hours"] += item["effort_hours"]
            mand_idx += 1
        else:
            break
            
    remaining_pool = mand_items[mand_idx:] + other_items
    unplaced = []
    
    for item in remaining_pool:
        placed = False
        for w in weeks:
            if w["hours"] + item["effort_hours"] <= hours_max:
                w["items"].append(item)
                w["hours"] += item["effort_hours"]
                placed = True
                break
        if not placed:
            unplaced.append(item)

    for w in weeks:
        w["hours"] = round(w["hours"], 2)

    return {"weeks": weeks, "unplaced": unplaced}

def generate_internal_linking_map(weeks: list) -> str:
    all_allocated = []
    for w in weeks:
        for it in w["items"]:
            all_allocated.append({**it, "week": w["week"], "phase": w["phase"]})
            
    if not all_allocated:
        return ""
        
    md = []
    md.append("## Interne Verlinkungs-Map (Deterministisch verknuepft)\n")
    
    # 1. Vertikale Verlinkung (Cluster -> Pillar)
    md.append("### a) Vertikale Verlinkungs-Map (Cluster -> Pillar)\n")
    md.append("| Content-Stueck (Woche) | Verlinkt zu (Pillar/Money Page) | Empfohlener Ankertext | Phase |")
    md.append("|---|---|---|---|")
    for it in all_allocated:
        anchor = f"Uebersicht {it['pillar']}" if it['content_type'] in ['Ratgeber', 'Blogartikel'] else f"Alle Leistungen {it['pillar']}"
        md.append(f"| {it['title']} (W{it['week']}) | {it['pillar']} | {anchor} | Phase {it['phase']} |")
        
    md.append("\n### b) Horizontale Sibling- & GEO-Verlinkungs-Map (Cluster -> Verwandtes Cluster / Data-Hub)\n")
    md.append("| Content-Stueck (Woche) | Verlinkt zusaetzlich zu (Sibling / Hub) | Empfohlener Ankertext | GEO-Zweck |")
    md.append("|---|---|---|---|")
    
    for idx, it in enumerate(all_allocated):
        # Finde ein Geschwister-Element aus demselben Pillar oder benachbarter Region
        siblings = [s for s in all_allocated if s != it and (s['pillar'] == it['pillar'] or s['category'] == it['category'])]
        if siblings:
            target = siblings[idx % len(siblings)]
            geo_purpose = "Entity-Kanonisierung" if target['content_type'] == "Entity-Anchor" else "Passagen-Zitation"
            md.append(f"| {it['title']} (W{it['week']}) | {target['title']} (W{target['week']}) | Ratgeber: {target['keyword']} | {geo_purpose} |")
        else:
            md.append(f"| {it['title']} (W{it['week']}) | Startseite / Themen-Hub | Hauptseite {it['pillar']} | Pillar-Autoritaet |")
            
    return "\n".join(md)

def generate_markdown_plan(plan_result, hours_min: float = 10.0, hours_max: float = 15.0) -> str:
    if isinstance(plan_result, dict):
        weeks = plan_result["weeks"]
        unplaced = plan_result.get("unplaced", [])
    else:
        weeks = plan_result
        unplaced = []

    md = []
    total_hours = sum(w["hours"] for w in weeks)
    active_weeks = len([w for w in weeks if w["hours"] > 0])
    total_items = sum(len(w["items"]) for w in weeks)
    
    md.append("# 120-Tage-Content-Plan (Deterministisch geloest inkl. GEO)\n")
    md.append(f"**Gesamtumfang:** {total_items} verplante Content-Stuecke | **Gesamtaufwand:** {round(total_hours, 2)} Stunden ueber {active_weeks} aktive Wochen.\n")
    active = [w for w in weeks if w["hours"] > 0]
    if active:
        lo = min(w["hours"] for w in active)
        hi = max(w["hours"] for w in active)
        ok = lo >= hours_min and hi <= hours_max
        md.append(
            f"**Kapazitaets-Messung:** {len(active)} aktive Wochen, gemessen {lo:.2f}h bis {hi:.2f}h "
            f"(Zielband {hours_min:.1f}h bis {hours_max:.1f}h). "
            + ("Zielband eingehalten." if ok else "ACHTUNG: Zielband verlassen, siehe Gate 3.") + "\n"
        )
    else:
        md.append("**Kapazitaets-Messung:** keine aktive Woche, es wurden keine Items verplant.\n")
    
    phases = {1: "Phase 1 (Tag 1-30) - Fundament, Core Entities & Local Authority",
              2: "Phase 2 (Tag 31-60) - Expansion, Data-Hubs & Standorte",
              3: "Phase 3 (Tag 61-90) - Vertiefung, Vergleiche & Commercial Pages",
              4: "Phase 4 (Tag 91-120) - Vollstaendige Themen- & GEO-Abdeckung"}
              
    for p_num in range(1, 5):
        p_weeks = [w for w in weeks if w["phase"] == p_num]
        p_hours = sum(w["hours"] for w in p_weeks)
        
        md.append(f"## {phases[p_num]}\n")
        
        if p_hours == 0:
            belegt = sorted({w["phase"] for w in weeks if w["hours"] > 0})
            belegt_txt = ", ".join(f"Phase {b}" for b in belegt) if belegt else "keiner Phase"
            md.append(f"*Puffer-Phase: alle eingereichten Themen wurden in {belegt_txt} verplant. Reserve fuer die Performance-Anpassung aus Schritt 3b.*\n")
            continue
            
        md.append("| Woche | Content-Typ | GEO-Typ | Titel/Thema | Ziel-Keyword | Suchvolumen | KD | Aufwand (Std) | Prioritaet |")
        md.append("|---|---|---|---|---|---|---|---|---|")
        
        for w in p_weeks:
            if w["hours"] == 0:
                continue
            for item in w["items"]:
                prio = "Hoch" if item["score"] > 20 else ("Mittel" if item["score"] > 5 else "Niedrig")
                geo_label = item.get("geo_type", "Standard-SEO")
                md.append(f"| W{w['week']} | {item['content_type']} | {geo_label} | {item['title']} | {item['keyword']} | {item['search_volume']} | {item['difficulty']} | {item['effort_hours']}h | {prio} |")
            md.append(f"| **W{w['week']} Summe** | | | | | | | **{w['hours']}h** | |")
        md.append(f"\n**Phase {p_num} Zwischensumme:** {round(p_hours, 2)}h\n")
        
    md.append("\n" + generate_internal_linking_map(weeks))

    # Backlog Section fuer nicht verplante Items
    md.append("\n## Backlog / Unverplante Opportunitaeten\n")
    if unplaced:
        md.append(f"Folgende {len(unplaced)} Items konnten im aktuellen 120-Tage-Kapazitaetsfenster ({hours_max}h/Woche Max) nicht platziert werden und bilden das Backlog fuer Folge-Phasen:\n")
        md.append("| Titel/Thema | Content-Typ | GEO-Typ | Ziel-Keyword | Suchvolumen | KD | Aufwand (Std) | Score |")
        md.append("|---|---|---|---|---|---|---|---|")
        for up in unplaced:
            md.append(f"| {up['title']} | {up['content_type']} | {up.get('geo_type', 'Standard-SEO')} | {up['keyword']} | {up['search_volume']} | {up['difficulty']} | {up['effort_hours']}h | {up['score']} |")
    else:
        md.append("*Alle eingereichten Themen wurden vollstaendig verplant (0 unverplante Items im Backlog).*\n")

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Deterministischer 120-Tage Capacity Matrix Solver v1.3.0 (GEO-Ready)")
    parser.add_argument("--input", "-i", type=str, help="Pfad zur CSV- oder JSON-Keyword-Tabelle")
    parser.add_argument("--output", "-o", type=str, help="Ausgabepfad fuer den generierten Markdown-Plan")
    parser.add_argument("--hours-min", type=float, default=10.0, help="Mindest-Wochenstunden (Default: 10.0)")
    parser.add_argument("--hours-max", type=float, default=15.0, help="Maximal-Wochenstunden (Default: 15.0)")
    parser.add_argument("--weeks", type=int, default=17, help="Anzahl Wochen (Default: 17)")
    parser.add_argument("--json-out", action="store_true", help="Ergebnis als JSON statt Markdown ausgeben")
    
    args = parser.parse_args()
    
    if not args.input:
        print("Capacity Matrix Solver v1.3.0 (Raphael Rechberger)")
        print("Nutzung: python capacity_matrix_solver.py --input <datei.csv|datei.json> [--output <plan.md>]")
        return
        
    input_path = Path(args.input)
    try:
        items = load_items_from_file(input_path)
        plan_result = solve_capacity_plan(items, hours_min=args.hours_min, hours_max=args.hours_max, total_weeks=args.weeks)
    except (CapacityValidationError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, CapacityValidationError):
            error = exc.to_dict()
        else:
            error = {
                "code": "ERROR_SOLVER_INPUT_INVALID",
                "message": str(exc),
                "item_index": None,
                "field": None,
            }
        if args.json_out:
            print(json.dumps({"status": "failed", "error": error}, indent=2, ensure_ascii=False))
        else:
            print(f"[NICHT BESTANDEN] {error['code']}: {error['message']}", file=sys.stderr)
        sys.exit(1)
    
    if args.json_out:
        out_content = json.dumps(plan_result, indent=2, ensure_ascii=False)
    else:
        out_content = generate_markdown_plan(plan_result, hours_min=args.hours_min, hours_max=args.hours_max)
        
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_content, encoding="utf-8")
        print(f"Plan erfolgreich geschrieben nach: {out_path}")
    else:
        print(out_content)

if __name__ == "__main__":
    main()
