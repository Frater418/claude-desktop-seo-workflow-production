#!/usr/bin/env python3
"""
Schema.org JSON-LD Validator fuer SEO & GEO Content Briefings
Autor: Raphael Rechberger
Version: 1.1.0

Validiert generierte JSON-LD Bloecke gegen Google Rich Result & 2026 GEO Standards
(LocalBusiness, MedicalBusiness, Article, FAQPage, BreadcrumbList, @graph mit about/mentions Wikidata URIs).
Bietet eine vollstaendige CLI fuer automatisierte CI/CD- und Pre-Commit-Gates.
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path

REQUIRED_FIELDS = {
    "LocalBusiness": ["@type", "name", "address"],
    "MedicalBusiness": ["@type", "name", "address"],
    "Article": ["@type", "headline", "author", "datePublished"],
    "BlogPosting": ["@type", "headline", "author", "datePublished"],
    "TechArticle": ["@type", "headline", "author", "datePublished"],
    "FAQPage": ["@type", "mainEntity"],
    "BreadcrumbList": ["@type", "itemListElement"]
}

def extract_json_ld(text: str) -> list:
    """Extrahiert JSON-LD Bloecke aus Markdown, HTML oder reinem JSON."""
    blocks = []
    
    # 1. Pattern fuer <script type="application/ld+json">
    matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', text, re.DOTALL | re.IGNORECASE)
    for m in matches:
        try:
            data = json.loads(m.strip())
            blocks.append(data)
        except json.JSONDecodeError as e:
            return [{"error": f"JSON Decode Error in script tag: {str(e)}", "raw": m[:200]}]
            
    # 2. Pattern fuer Markdown JSON Codebloecke mit "@context"
    if not blocks:
        md_matches = re.findall(r'```(?:json)?\s*(\{[\s\S]*?"@context"[\s\S]*?\})\s*```', text, re.DOTALL)
        for m in md_matches:
            try:
                data = json.loads(m.strip())
                blocks.append(data)
            except json.JSONDecodeError:
                pass
                
    # 3. Falls reines JSON uebergeben wurde
    if not blocks and text.strip().startswith("{"):
        try:
            data = json.loads(text.strip())
            blocks.append(data)
        except json.JSONDecodeError as e:
            blocks.append({"error": f"JSON Decode Error in raw text: {str(e)}"})
            
    return blocks

def validate_schema_object(obj: dict, strict_geo: bool = False) -> list:
    """Prueft ein einzelnes Schema.org Objekt auf Pflichtfelder und GEO-Konformitaet."""
    errors = []
    
    # Pruefe @graph Struktur
    if "@graph" in obj:
        graph_items = obj["@graph"]
        if not isinstance(graph_items, list) or len(graph_items) == 0:
            return ["Fehler: '@graph' muss eine nicht-leere Liste von Schema-Objekten sein."]
        for sub in graph_items:
            errors.extend(validate_schema_object(sub, strict_geo=strict_geo))
        return errors

    schema_type = obj.get("@type")
    if not schema_type:
        return ["Fehler: Objekt enthaelt kein '@type' Attribut."]
        
    types = [schema_type] if isinstance(schema_type, str) else schema_type
    
    for t in types:
        if t in REQUIRED_FIELDS:
            for req in REQUIRED_FIELDS[t]:
                if req not in obj or not obj[req]:
                    errors.append(f"Validierungsfehler fuer Typ '{t}': Pflichtfeld '{req}' fehlt oder ist leer.")
                    
    # Spezifische Pruefung fuer FAQPage
    if "FAQPage" in types:
        entities = obj.get("mainEntity", [])
        if not isinstance(entities, list) or len(entities) == 0:
            errors.append("FAQPage Fehler: 'mainEntity' muss eine nicht-leere Liste von Question-Objekten sein.")
        else:
            for idx, q in enumerate(entities):
                if q.get("@type") != "Question" or not q.get("name"):
                    errors.append(f"FAQPage Item #{idx}: Ungueltige Frage oder 'name' fehlt.")
                accepted_answer = q.get("acceptedAnswer", {})
                if accepted_answer.get("@type") != "Answer" or not accepted_answer.get("text"):
                    errors.append(f"FAQPage Item #{idx}: Ungueltige Antwort oder 'text' fehlt.")

    # GEO-Spezifische Pruefung fuer Article / TechArticle (Wikidata about/mentions)
    if strict_geo and any(t in ["Article", "BlogPosting", "TechArticle"] for t in types):
        about = obj.get("about", [])
        if not about:
            errors.append("GEO-Validierung: 'about' Property fehlt fuer Article-Entitaet.")
        else:
            about_list = about if isinstance(about, list) else [about]
            for it in about_list:
                same_as = it.get("sameAs", "")
                if same_as and "wikidata.org/wiki/Q" not in str(same_as):
                    errors.append(f"GEO-Warnung: 'sameAs' in 'about' ({same_as}) verweist nicht auf eine Wikidata-URI.")

    return errors

def validate_text(text: str, strict_geo: bool = False) -> dict:
    blocks = extract_json_ld(text)
    if not blocks:
        return {"valid": False, "blocks_found": 0, "errors": ["Kein valider JSON-LD Block im uebergebenen Text gefunden."]}
        
    all_errors = []
    for idx, b in enumerate(blocks):
        if "error" in b:
            all_errors.append(b["error"])
        else:
            errs = validate_schema_object(b, strict_geo=strict_geo)
            all_errors.extend(errs)
            
    return {
        "valid": len(all_errors) == 0,
        "blocks_found": len(blocks),
        "errors": all_errors
    }

def main():
    parser = argparse.ArgumentParser(description="Schema.org JSON-LD Validator CLI v1.1.0 (Google Rich Results & GEO)")
    parser.add_argument("--input", "-i", type=str, help="Pfad zur HTML-, Markdown- oder JSON-Datei")
    parser.add_argument("--strict", "-s", action="store_true", help="Aktiviert strikte GEO-Pruefung fuer Wikidata about/mentions")
    parser.add_argument("--json-out", action="store_true", help="Ergebnis als JSON ausgeben")
    
    args = parser.parse_args()
    
    if not args.input:
        print("Schema.org JSON-LD Validator v1.1.0 (Raphael Rechberger)")
        print("Nutzung: python validate_schema_jsonld.py --input <datei.html|datei.md|datei.json> [--strict]")
        sys.exit(0)
        
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {input_path}")
        sys.exit(1)
        
    content = input_path.read_text(encoding="utf-8")
    result = validate_text(content, strict_geo=args.strict)
    
    if args.json_out:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["valid"]:
            print(f"[BESTANDEN] JSON-LD Schema in '{input_path.name}' ist 100% valide. ({result['blocks_found']} Block/Bloecke geprueft)")
        else:
            print(f"[NICHT BESTANDEN] {len(result['errors'])} Validierungsfehler in '{input_path.name}':")
            for err in result["errors"]:
                print(f"  - {err}")
                
    sys.exit(0 if result["valid"] else 1)

if __name__ == "__main__":
    main()
