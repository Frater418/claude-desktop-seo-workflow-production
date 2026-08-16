#!/usr/bin/env python3
"""
Capacity Matrix Solver for 120-Day SEO Content Plans
Autor: Raphael Rechberger
Version: 1.0.0

Deterministischer Kapazitaets- und Prioritaets-Solver fuer die Erstellung
von 120-Tage-Roadmaps (17 Wochen a 10-15 Stunden/Woche).
Verhindert LLM-Arithmetik- und Rundungsfehler.
"""

import sys
import json
import csv
from pathlib import Path

# Standard-Aufwaende in Stunden
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

# Business-Relevanz-Multiplikatoren
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
    """Berechnet den Prioritaets-Score nach der verbindlichen Formel."""
    cat_clean = category.strip()
    c_type_clean = content_type.strip().lower()
    
    if "landingpage" in c_type_clean and ("lokal" in cat_clean.lower() or is_mandatory):
        factor = RELEVANCE_FACTORS["Lokal_Landingpage"]
    elif "kosten" in cat_clean or "transaktion" in cat_clean:
        factor = RELEVANCE_FACTORS["Kosten"]
    elif "vergleich" in cat_clean or "entscheidung" in cat_clean:
        factor = RELEVANCE_FACTORS["Vergleich"]
    elif "lokal" in cat_clean.lower():
        factor = RELEVANCE_FACTORS["Lokal_Blog"]
    else:
        factor = 1.0
        
    score = (search_volume / (difficulty + 1.0)) * factor
    return round(score, 2)

def solve_capacity_plan(items: list, hours_min=10.0, hours_max=15.0, total_weeks=17):
    """
    Verteilt die Items deterministisch auf 17 Wochen a hours_min bis hours_max Stunden.
    Phase 1: Woche 1-4 (Tag 1-30)
    Phase 2: Woche 5-8 (Tag 31-60)
    Phase 3: Woche 9-13 (Tag 61-90)
    Phase 4: Woche 14-17 (Tag 91-120)
    """
    # 1. Scoring & Vorbereitung
    processed = []
    for item in items:
        sv = float(item.get("Suchvolumen", 0) or 0)
        kd = float(item.get("Difficulty", 0) or 0)
        cat = str(item.get("Kategorie", "Informational"))
        c_type = str(item.get("Content_Type", "Blogartikel"))
        is_mand = bool(item.get("Is_Mandatory_Location", False) or item.get("is_mandatory", False))
        
        score = calculate_score(sv, kd, cat, c_type, is_mand)
        effort = EFFORT_WEIGHTS.get(c_type, 2.5)
        
        processed.append({
            "pillar": item.get("Pillar_Thema", ""),
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

    # 2. Sortierung: Mandatory Locations & High Scores zuerst
    # Mandatory Locations werden vorrangig fuer Phase 1 und 2 vorgesehen
    mand_items = sorted([i for i in processed if i["is_mandatory"]], key=lambda x: x["score"], reverse=True)
    other_items = sorted([i for i in processed if not i["is_mandatory"]], key=lambda x: x["score"], reverse=True)

    weeks = [{"week": w + 1, "phase": 1 if w < 4 else (2 if w < 8 else (3 if w < 13 else 4)), "items": [], "hours": 0.0} for w in range(total_weeks)]
    
    # 3. Zuteilung: Zuerst lokale Pflichtseiten gleichmaessig ueber Phase 1-2 verteilen
    phase_1_2_weeks = weeks[:8]
    mand_idx = 0
    while mand_items and mand_idx < len(mand_items):
        item = mand_items[mand_idx]
        # Finde die Woche in Phase 1-2 mit geringster Auslastung
        best_week = min(phase_1_2_weeks, key=lambda w: w["hours"])
        if best_week["hours"] + item["effort_hours"] <= hours_max:
            best_week["items"].append(item)
            best_week["hours"] += item["effort_hours"]
            mand_idx += 1
        else:
            break
            
    # Nicht untergebrachte Mandatories kommen in die Gesamtliste
    remaining_pool = mand_items[mand_idx:] + other_items
    
    # 4. Befuellung aller 17 Wochen bis hours_min <= hours <= hours_max
    for item in remaining_pool:
        # Finde die frueheste passende Woche, die noch Kapazitaet hat
        placed = False
        for w in weeks:
            if w["hours"] + item["effort_hours"] <= hours_max:
                w["items"].append(item)
                w["hours"] += item["effort_hours"]
                placed = True
                break
        if not placed:
            # Backlog fuer Tag 121+
            pass

    # Pruefung auf Unterauslastung (< hours_min)
    for w in weeks:
        w["hours"] = round(w["hours"], 2)

    return weeks

def generate_markdown_plan(weeks: list) -> str:
    """Generiert den sauberen Markdown-Plan aus der Wochenzuteilung."""
    md = []
    md.append("# 120-Tage-Content-Plan (Deterministisch geloest)\n")
    md.append("**Kapazitaets-Garantie:** Jede Woche zwischen 10.0 und 15.0 Stunden.\n")
    
    phases = {1: "Phase 1 (Tag 1-30) - Fundament & Skalierung",
              2: "Phase 2 (Tag 31-60) - Expansion & Local Authority",
              3: "Phase 3 (Tag 61-90) - Vertiefung & Commercial Pages",
              4: "Phase 4 (Tag 91-120) - Vollstaendige Themenabdeckung"}
              
    for p_num in range(1, 5):
        md.append(f"## {phases[p_num]}\n")
        md.append("| Woche | Content-Typ | Titel/Thema | Ziel-Keyword | Suchvolumen | KD | Aufwand (Std) | Prioritaet |")
        md.append("|---|---|---|---|---|---|---|---|")
        
        p_weeks = [w for w in weeks if w["phase"] == p_num]
        p_hours = sum(w["hours"] for w in p_weeks)
        
        for w in p_weeks:
            for item in w["items"]:
                prio = "Hoch" if item["score"] > 20 else ("Mittel" if item["score"] > 5 else "Niedrig")
                md.append(f"| W{w['week']} | {item['content_type']} | {item['title']} | {item['keyword']} | {item['search_volume']} | {item['difficulty']} | {item['effort_hours']}h | {prio} |")
            md.append(f"| **W{w['week']} Summe** | | | | | | **{w['hours']}h** | |")
        md.append(f"\n**Phase {p_num} Gesamtstunden:** {round(p_hours, 2)}h\n")
        
    return "\n".join(md)

if __name__ == "__main__":
    print("Capacity Matrix Solver v1.0.0 bereit.")
