import json
from pathlib import Path

locations = [
    "Frankfurt Bornheim", "Frankfurt Sachsenhausen", "Frankfurt Nordend", "Frankfurt Bockenheim",
    "Frankfurt Westend", "Frankfurt Ostend", "Frankfurt Gallus", "Frankfurt Hoechst",
    "Frankfurt Niederrad", "Frankfurt Praunheim", "Offenbach am Main", "Neu-Isenburg",
    "Bad Vilbel", "Eschborn", "Oberursel", "Dreieich"
]

items = []

for loc in locations:
    items.append({
        "Pillar_Thema": "Ambulante Pflege",
        "Kategorie": "Lokal",
        "Cluster_Thema": f"Pflegedienst {loc}",
        "Content_Type": "Landingpage",
        "Region": loc,
        "Ziel_Keyword": f"pflegedienst {loc.lower()}",
        "Suchvolumen": 80 + len(loc) * 10,
        "Difficulty": 10 + (len(loc) % 15),
        "CPC": 4.20,
        "Is_Mandatory_Location": True
    })

ratgeber_topics = [
    ("Ambulante Pflege", "Kosten", "Ambulante Pflege Kosten Krankenkasse Tabelle", "Ratgeber", "ambulante pflege kosten krankenkasse", 2400, 28, 3.20),
    ("Ambulante Pflege", "Transaktional", "Pflegedienst beauftragen Schritt fuer Schritt", "Ratgeber", "pflegedienst beauftragen ablauf", 550, 15, 2.80),
    ("Ambulante Pflege", "Vergleich", "Grundpflege vs Behandlungspflege Leistungen", "Ratgeber", "grundpflege behandlungspflege unterschied", 1400, 22, 1.90),
    ("Ambulante Pflege", "Kosten", "Pflegesachleistungen Hoehe und Anspruch", "Ratgeber", "pflegesachleistungen anspruch tabelle", 3200, 32, 2.70),
    ("Ambulante Pflege", "W-Fragen", "Was zahlt die Pflegekasse bei Pflegegrad 2", "FAQ", "was zahlt pflegekasse pflegegrad 2", 4100, 35, 2.10),
    ("Ambulante Pflege", "W-Fragen", "Pflegegrad 3 Geldleistungen vs Sachleistungen", "FAQ", "pflegegrad 3 leistungen", 3800, 34, 2.30),
    ("Ambulante Pflege", "Erfahrung", "Haeusliche Krankenpflege Qualitaetskriterien MDK", "Ratgeber", "haeusliche krankenpflege qualitaet", 650, 18, 2.50),
    ("Verhinderungspflege", "Kosten", "Verhinderungspflege Budget und Stundenabrechnung", "Ratgeber", "verhinderungspflege budget anspruch", 4200, 30, 2.50),
    ("Verhinderungspflege", "Transaktional", "Verhinderungspflege stundenweise beantragen Formular", "Ratgeber", "verhinderungspflege stundenweise beantragen", 2100, 25, 2.90),
    ("Verhinderungspflege", "W-Fragen", "Verhinderungspflege rueckwirkend auszahlen Fristen", "FAQ", "verhinderungspflege rueckwirkend", 1200, 19, 1.80),
    ("Verhinderungspflege", "Vergleich", "Kurzzeitpflege vs Verhinderungspflege Kombination", "Ratgeber", "kurzzeitpflege verhinderungspflege kombinieren", 2800, 26, 2.40),
    ("Verhinderungspflege", "Kosten", "Verhinderungspflege durch nahe Angehoerige Verwandte", "Ratgeber", "verhinderungspflege angehoerige bezahlung", 3100, 29, 2.60),
    ("Verhinderungspflege", "Transaktional", "Verhinderungspflege Nachweis und Abrechnung Krankenkasse", "Ratgeber", "verhinderungspflege abrechnung krankenkasse", 1600, 21, 2.70),
    ("Demenzbetreuung", "Kosten", "Entlastungsbetrag Demenz 125 Euro Abrechnung", "Ratgeber", "entlastungsbetrag demenz 125 euro nutzen", 2900, 27, 2.20),
    ("Demenzbetreuung", "Erfahrung", "Demenzbetreuung zuhause Entlastung fuer pflegende Angehoerige", "Ratgeber", "demenzbetreuung zuhause angehoerige", 1100, 16, 2.60),
    ("Demenzbetreuung", "Transaktional", "Demenzbegleiter stundenweise buchen Kosten", "Ratgeber", "demenzbegleiter stundenweise kosten", 850, 14, 3.10),
    ("Demenzbetreuung", "W-Fragen", "Demenz Fruehsymptome Checkliste Angehoerige", "Ratgeber", "demenz fruehsymptome erkennen", 5400, 38, 1.80),
    ("Demenzbetreuung", "Vergleich", "Tagespflege Demenz vs ambulante Betreuung", "Ratgeber", "tagespflege demenz vs ambulant", 950, 17, 2.40),
    ("Seniorenbetreuung & Entlastung", "Kosten", "Haushaltshilfe Pflegekasse Kostenuebernahme", "Ratgeber", "haushaltshilfe pflegekasse anspruch", 3600, 31, 2.90),
    ("Seniorenbetreuung & Entlastung", "Transaktional", "Seniorenbegleitung im Alltag buchen", "Ratgeber", "seniorenbegleitung alltag buchen", 720, 15, 3.40),
    ("Seniorenbetreuung & Entlastung", "W-Fragen", "Hausnotruf Kostenuebernahme Pflegekasse Voraussetzungen", "FAQ", "hausnotruf kosten pflegekasse", 2200, 24, 2.10),
    ("Seniorenbetreuung & Entlastung", "Vergleich", "24 Stunden Pflege vs ambulanter Pflegedienst", "Ratgeber", "24 stunden pflege vs pflegedienst", 4800, 36, 4.10),
    ("Seniorenbetreuung & Entlastung", "Kosten", "Pflegehilfsmittel 40 Euro Pauschale beantragen", "Ratgeber", "pflegehilfsmittel 40 euro pauschale", 3400, 28, 2.30),
    ("Seniorenbetreuung & Entlastung", "Transaktional", "Wohnraumanpassung Zuschuss 4000 Euro Pflegekasse", "Ratgeber", "wohnraumanpassung zuschuss pflegekasse", 2600, 26, 3.50),
    ("Seniorenbetreuung & Entlastung", "Erfahrung", "Tipps gegen Ueberlastung pflegender Angehoeriger", "Ratgeber", "ueberlastung pflegende angehoerige hilfe", 1300, 18, 2.00)
]

for p, cat, title, ctype, kw, sv, kd, cpc in ratgeber_topics:
    items.append({
        "Pillar_Thema": p,
        "Kategorie": cat,
        "Cluster_Thema": title,
        "Content_Type": ctype,
        "Region": "",
        "Ziel_Keyword": kw,
        "Suchvolumen": sv,
        "Difficulty": kd,
        "CPC": cpc,
        "Is_Mandatory_Location": False
    })

extra_topics = [
    ("Ambulante Pflege", "W-Fragen", "Medikamentengabe durch Pflegedienst Verordnung", "FAQ", "medikamentengabe pflegedienst rezept", 890, 14, 2.20),
    ("Ambulante Pflege", "Kosten", "Zuzahlung haeusliche Krankenpflege Befreiung", "Ratgeber", "zuzahlung haeusliche krankenpflege", 760, 12, 2.10),
    ("Ambulante Pflege", "Transaktional", "Pflegevertrag kuendigen Fristen Muster", "Ratgeber", "pflegevertrag kuendigen muster", 1150, 16, 1.90),
    ("Ambulante Pflege", "Vergleich", "Pflegedienst wechseln Ablauf und Fristen", "Ratgeber", "pflegedienst wechseln", 980, 15, 2.40),
    ("Verhinderungspflege", "W-Fragen", "Verhinderungspflege fuer Nachbarn und Bekannte", "FAQ", "verhinderungspflege nachbarn", 1450, 20, 2.00),
    ("Verhinderungspflege", "Kosten", "Verhinderungspflege Steuerfreibetrag Uebersicht", "Ratgeber", "verhinderungspflege steuerfrei", 2300, 23, 2.20),
    ("Demenzbetreuung", "W-Fragen", "Validation bei Demenz Gespraechsfuehrung", "Ratgeber", "validation demenz beispiele", 1800, 21, 1.70),
    ("Demenzbetreuung", "Kosten", "Pflegegrad bei Demenz erhoehen Tipps MDK", "Ratgeber", "pflegegrad demenz erhoehen", 1650, 22, 2.80),
    ("Seniorenbetreuung & Entlastung", "W-Fragen", "Essen auf Raedern Kostenuebernahme Sozialamt", "FAQ", "essen auf raedern zuschuss", 1900, 22, 2.50),
    ("Seniorenbetreuung & Entlastung", "Transaktional", "Behindertengerechtes Bad Umbau Foerderung", "Ratgeber", "badumbau pflegekasse zuschuss", 3100, 29, 3.80),
    ("Ambulante Pflege", "Lokal", "Verhinderungspflege Offenbach", "Landingpage", "verhinderungspflege offenbach", 110, 11, 3.90),
    ("Demenzbetreuung", "Lokal", "Demenzbetreuung Offenbach", "Landingpage", "demenzbetreuung offenbach", 95, 10, 4.00),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Bad Homburg", "Landingpage", "pflegedienst bad homburg", 180, 14, 4.40),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Hanau", "Landingpage", "pflegedienst hanau", 310, 19, 4.10),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Darmstadt", "Landingpage", "pflegedienst darmstadt", 420, 22, 4.30),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Wiesbaden", "Landingpage", "pflegedienst wiesbaden", 510, 24, 4.50),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Mainz", "Landingpage", "pflegedienst mainz", 480, 23, 4.20),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Ruesselsheim", "Landingpage", "pflegedienst ruesselsheim", 190, 15, 4.00),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Maintal", "Landingpage", "pflegedienst maintal", 130, 12, 3.90),
    ("Ambulante Pflege", "Lokal", "Pflegedienst Langen Hessen", "Landingpage", "pflegedienst langen hessen", 120, 11, 3.80)
]

for p, cat, title, ctype, kw, sv, kd, cpc in extra_topics:
    is_m = ctype == "Landingpage"
    items.append({
        "Pillar_Thema": p,
        "Kategorie": cat,
        "Cluster_Thema": title,
        "Content_Type": ctype,
        "Region": "Rhein-Main",
        "Ziel_Keyword": kw,
        "Suchvolumen": sv,
        "Difficulty": kd,
        "CPC": cpc,
        "Is_Mandatory_Location": is_m
    })

p1 = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/tests/fixtures/sample_cluster_keywords.json")
p2 = Path("C:/Users/offic/Desktop/Heartweb/claude-desktop-seo-workflow-production/tests/fixtures/sample_cluster_keywords.json")

p1.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
p2.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated {len(items)} items in sample_cluster_keywords.json")
