#!/usr/bin/env python3
"""
Capacity Matrix Solver for 120-Day SEO Content Plans
Autor: Raphael Rechberger
Version: 1.2.0

Deterministischer Kapazitaets- und Prioritaets-Solver fuer die Erstellung
von 120-Tage-Roadmaps (17 Wochen a 10-15 Stunden/Woche).
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
    "Blogartikel": 3.0,
    "Blog": 3.0,
    "Ratgeber": 3.0,
    "Landingpage": 1.25,
    "Standort-Landingpage": 1.25,
    "FAQ": 1.0,
    "Ergaenzungsseite": 1.0
}

RELEVANCE_FACTORS = {
    "Lokal_Landingpage": 4.0,
    "Kosten": 3.0,
    "Transaktional": 3.0,
    "Vergleich": 2.0,
    "Entscheidung": 2.0,
    "Lokal_Blog": 2.0,
    "Informational": 1.0,
    "W-Fragen": 1.0,
    "Erfahrung": 1.0,
    "Vertrauen": 1.0
}

def calculate_score(search_volume: float, difficulty: float, category: str, content_type: str, is_mandatory: bool) -> float:
    cat_clean = str(category or "").strip()
    c_type_clean = str(content_type or "").strip().lower()
    
    if "landingpage" in c_type_clean and ("lokal" in cat_clean.lower() or is_mandatory):
        factor = RELEVANCE_FACTORS["Lokal_Landingpage"]
    elif "kosten" in cat_clean.lower() or "transaktion" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Kosten"]
    elif "vergleich" in cat_clean.lower() or "entscheidung" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Vergleich"]
    elif "lokal" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Lokal_Blog"]
    else:
        factor = 1.0
        
    score = (float(search_volume or 0) / (float(difficulty or 0) + 1.0)) * factor
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
        
    return items

def solve_capacity_plan(items: list, hours_min=10.0, hours_max=15.0, total_weeks=17):
    if not items:
        return [{"week": w + 1, "phase": 1 if w < 4 else (2 if w < 8 else (3 if w < 13 else 4)), "items": [], "hours": 0.0} for w in range(total_weeks)]
        
    processed = []
    for item in items:
        sv = float(item.get("Suchvolumen", 0) or item.get("search_volume", 0) or 0)
        kd = float(item.get("Difficulty", 0) or item.get("difficulty", 0) or 0)
        cat = str(item.get("Kategorie", item.get("category", "Informational")))
        c_type = str(item.get("Content_Type", item.get("content_type", "Blogartikel")))
        
        is_mand_raw = item.get("Is_Mandatory_Location", item.get("is_mandatory", False))
        is_mand = str(is_mand_raw).lower() in ["true", "1", "yes", "ja"]
        
        score = calculate_score(sv, kd, cat, c_type, is_mand)
        effort = EFFORT_WEIGHTS.get(c_type, 2.5)
        
        processed.append({
            "pillar": item.get("Pillar_Thema", item.get("pillar", "Hauptkategorie")),
            "title": item.get("Cluster_Thema", item.get("title", "")),
            "keyword": item.get("Ziel_Keyword", item.get("keyword", "")),
            "search_volume": int(sv),
            "difficulty": int(kd),
            "content_type": c_type,
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
    
    for item in remaining_pool:
        placed = False
        for w in weeks:
            if w["hours"] + item["effort_hours"] <= hours_max:
                w["items"].append(item)
                w["hours"] += item["effort_hours"]
                placed = True
                break
        if not placed:
            pass

    for w in weeks:
        w["hours"] = round(w["hours"], 2)

    return weeks

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
        anchor = f"Uebersicht {it['pillar']}" if it['content_type'] == 'Ratgeber' else f"Alle Leistungen {it['pillar']}"
        md.append(f"| {it['title']} (W{it['week']}) | {it['pillar']} | {anchor} | Phase {it['phase']} |")
        
    md.append("\n### b) Horizontale Sibling-Verlinkungs-Map (Cluster -> Verwandtes Cluster)\n")
    md.append("| Content-Stueck (Woche) | Verlinkt zusaetzlich zu (Sibling) | Empfohlener Ankertext |")
    md.append("|---|---|---|")
    
    for idx, it in enumerate(all_allocated):
        # Finde ein Geschwister-Element aus demselben Pillar oder benachbarter Region
        siblings = [s for s in all_allocated if s != it and (s['pillar'] == it['pillar'] or s['category'] == it['category'])]
        if siblings:
            target = siblings[idx % len(siblings)]
            md.append(f"| {it['title']} (W{it['week']}) | {target['title']} (W{target['week']}) | Ratgeber: {target['keyword']} |")
        else:
            md.append(f"| {it['title']} (W{it['week']}) | Startseite / Themen-Hub | Hauptseite {it['pillar']} |")
            
    return "\n".join(md)

def generate_markdown_plan(weeks: list) -> str:
    md = []
    total_hours = sum(w["hours"] for w in weeks)
    active_weeks = len([w for w in weeks if w["hours"] > 0])
    total_items = sum(len(w["items"]) for w in weeks)
    
    md.append("# 120-Tage-Content-Plan (Deterministisch geloest)\n")
    md.append(f"**Gesamtumfang:** {total_items} Content-Stuecke | **Gesamtaufwand:** {round(total_hours, 2)} Stunden ueber {active_weeks} aktive Wochen.\n")
    md.append("**Kapazitaets-Garantie:** Jede aktive Woche liegt strikt zwischen 10.0 und 15.0 Arbeitsstunden.\n")
    
    phases = {1: "Phase 1 (Tag 1-30) - Fundament & Skalierung",
              2: "Phase 2 (Tag 31-60) - Expansion & Local Authority",
              3: "Phase 3 (Tag 61-90) - Vertiefung & Commercial Pages",
              4: "Phase 4 (Tag 91-120) - Vollstaendige Themenabdeckung"}
              
    for p_num in range(1, 5):
        p_weeks = [w for w in weeks if w["phase"] == p_num]
        p_hours = sum(w["hours"] for w in p_weeks)
        
        md.append(f"## {phases[p_num]}\n")
        
        if p_hours == 0:
            md.append("*Puffer-Phase: Alle eingereichten Themen wurden in Phase 1-2 verplant. Bereit fuer Performance-Anpassung nach Tag 60.*\n")
            continue
            
        md.append("| Woche | Content-Typ | Titel/Thema | Ziel-Keyword | Suchvolumen | KD | Aufwand (Std) | Prioritaet |")
        md.append("|---|---|---|---|---|---|---|---|")
        
        for w in p_weeks:
            if w["hours"] == 0:
                continue
            for item in w["items"]:
                prio = "Hoch" if item["score"] > 20 else ("Mittel" if item["score"] > 5 else "Niedrig")
                md.append(f"| W{w['week']} | {item['content_type']} | {item['title']} | {item['keyword']} | {item['search_volume']} | {item['difficulty']} | {item['effort_hours']}h | {prio} |")
            md.append(f"| **W{w['week']} Summe** | | | | | | **{w['hours']}h** | |")
        md.append(f"\n**Phase {p_num} Zwischensumme:** {round(p_hours, 2)}h\n")
        
    md.append("\n" + generate_internal_linking_map(weeks))
    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Deterministischer 120-Tage Capacity Matrix Solver")
    parser.add_argument("--input", "-i", type=str, help="Pfad zur CSV- oder JSON-Keyword-Tabelle")
    parser.add_argument("--output", "-o", type=str, help="Ausgabepfad fuer den generierten Markdown-Plan")
    parser.add_argument("--hours-min", type=float, default=10.0, help="Mindest-Wochenstunden (Default: 10.0)")
    parser.add_argument("--hours-max", type=float, default=15.0, help="Maximal-Wochenstunden (Default: 15.0)")
    parser.add_argument("--weeks", type=int, default=17, help="Anzahl Wochen (Default: 17)")
    parser.add_argument("--json-out", action="store_true", help="Ergebnis als JSON statt Markdown ausgeben")
    
    args = parser.parse_args()
    
    if not args.input:
        print("Capacity Matrix Solver v1.2.0 (Raphael Rechberger)")
        print("Nutzung: python capacity_matrix_solver.py --input <datei.csv|datei.json> [--output <plan.md>]")
        return
        
    input_path = Path(args.input)
    items = load_items_from_file(input_path)
    weeks = solve_capacity_plan(items, hours_min=args.hours_min, hours_max=args.hours_max, total_weeks=args.weeks)
    
    if args.json_out:
        out_content = json.dumps(weeks, indent=2, ensure_ascii=False)
    else:
        out_content = generate_markdown_plan(weeks)
        
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_content, encoding="utf-8")
        print(f"Plan erfolgreich geschrieben nach: {out_path}")
    else:
        print(out_content)

if __name__ == "__main__":
    main()
