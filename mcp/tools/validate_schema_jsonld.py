#!/usr/bin/env python3
"""
Schema.org JSON-LD Validator fuer SEO Content Briefings
Autor: Raphael Rechberger
Version: 1.0.0

Validiert generierte JSON-LD Bloecke gegen Google Rich Result Standards
(LocalBusiness, MedicalBusiness, Article, FAQPage, BreadcrumbList).
"""

import sys
import json
import re

REQUIRED_FIELDS = {
    "LocalBusiness": ["@type", "name", "address"],
    "MedicalBusiness": ["@type", "name", "address"],
    "Article": ["@type", "headline", "author", "datePublished"],
    "BlogPosting": ["@type", "headline", "author", "datePublished"],
    "FAQPage": ["@type", "mainEntity"],
    "BreadcrumbList": ["@type", "itemListElement"]
}

def extract_json_ld(text: str) -> list:
    """Extrahiert JSON-LD Bloecke aus Markdown oder HTML."""
    blocks = []
    # Pattern fuer <script type="application/ld+json">
    matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', text, re.DOTALL | re.IGNORECASE)
    for m in matches:
        try:
            data = json.loads(m.strip())
            blocks.append(data)
        except json.JSONDecodeError as e:
            return [{"error": f"JSON Decode Error: {str(e)}", "raw": m[:200]}]
            
    # Falls reines JSON uebergeben wurde
    if not blocks and text.strip().startswith("{"):
        try:
            data = json.loads(text.strip())
            blocks.append(data)
        except json.JSONDecodeError:
            pass
            
    return blocks

def validate_schema_object(obj: dict) -> list:
    """Prueft ein einzelnes Schema.org Objekt auf Pflichtfelder."""
    errors = []
    
    # Pruefe @graph Struktur
    if "@graph" in obj:
        for sub in obj["@graph"]:
            errors.extend(validate_schema_object(sub))
        return errors

    schema_type = obj.get("@type")
    if not schema_type:
        return ["Fehler: Objekt enthaelt kein '@type' Attribut."]
        
    # Behandle Listen von Typen
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

    return errors

def validate_text(text: str) -> dict:
    blocks = extract_json_ld(text)
    if not blocks:
        return {"valid": False, "errors": ["Kein valider JSON-LD Block im uebergebenen Text gefunden."]}
        
    all_errors = []
    for idx, b in enumerate(blocks):
        if "error" in b:
            all_errors.append(b["error"])
        else:
            errs = validate_schema_object(b)
            all_errors.extend(errs)
            
    return {
        "valid": len(all_errors) == 0,
        "blocks_found": len(blocks),
        "errors": all_errors
    }

if __name__ == "__main__":
    print("Schema JSON-LD Validator v1.0.0 bereit.")
