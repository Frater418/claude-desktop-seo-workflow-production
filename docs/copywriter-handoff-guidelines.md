# Copywriter-Handoff & Notion-Guidelines

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Zielgruppe:** Regina, Katja, Alexander (Heartweb Copywriting Team) & Projektleiter  
**Version:** 1.0.0  

---

## 1. Ueberblick fuer die Redaktion

Dieses Dokument beschreibt, wie das Copywriting-Team (Regina, Katja, Alexander) die aus Schritt 4a erzeugten Content-Briefings erhaelt, interpretiert und in fertige, hochkonvertierende Texte verwandelt.

**Unser Leitsatz:**
Reiner KI-Text existiert bei Heartweb nicht. Claude Desktop liefert das datengestuetzte, SEO-gepruefte Fundament (SERP-Intent, Wettbewerbsstruktur, FAQs, Keywords, Schema-Markup); ihr als erfahrene Copywriter haucht den Texten Leben, Tonalitaet, Conversion-Psychologie und echte Erfahrung (EEAT) ein.

---

## 2. Struktur eines Briefings (Schritt 4a)

Jedes Briefing liegt als saubere Markdown-Datei unter `outputs/briefings/briefing-[thema-slug].md` vor und enthaelt:

### 2.1 Notion-Frontmatter (fuer die Datenbank)
```yaml
---
title: "Pflegedienst Frankfurt Bornheim"
pillar: "Ambulante Pflege"
content_type: "Landingpage"
target_keyword: "pflegedienst frankfurt bornheim"
search_volume: 70
difficulty: 12
priority: "Hoch"
phase: 1
status: "Bereit fuer Copywriting"
author: "Raphael Rechberger"
---
```
Diese Eigenschaften werden in Notion automatisch als Tabellen-Eigenschaften (Properties) erkannt.

### 2.2 Die 4 redaktionellen Kern-Abschnitte im Briefing:
1. **Search Intent & Zielgruppen-Fokus:** Was sucht der Nutzer in diesem Moment wirklich (akute Notsituation, reiner Preisvergleich oder rechtliche Information)?
2. **Meta-Tags:** Vorgeschlagener Meta-Title und Meta-Description mit Keyword-Platzierung (koennen stilistisch verfeinert werden).
3. **Section-fuer-Section Gliederung:**
   - Jede H2/H3-Ueberschrift mit Zweck und inhaltlichen Pflichtpunkten.
   - Konkrete Text- und Einstiegsbeispiele in der vorgegebenen Tonalitaet.
   - Platzierung von Zwischen-CTAs.
4. **Verlinkungsvorgaben:**
   - Vertikaler Link: Zwingender Link zur uebergeordneten Pillar-Page (mit empfohlenem Ankertext).
   - Horizontaler Sibling-Link: Zwingender Link zu einem verwandten Cluster-Artikel oder Nachbar-Standort.

---

## 3. Redaktions-Checkliste vor dem Handoff

Bevor ein Text als "Fertiggestellt" in Notion markiert wird, prueft der Copywriter:
- [ ] Wurde das Haupt-Keyword natuerlich in der H1, im ersten Absatz und in mindestens einer H2 eingebunden?
- [ ] Wurden die Fragen aus dem FAQ-Bereich mit echten, fachlich fundierten Antworten beantwortet?
- [ ] Wurden die beiden internen Links (Pillar + Sibling) mit natuerlichen Ankertexten gesetzt?
- [ ] Bei Standort-Seiten: Wurden Stadtteil-Besonderheiten natuerlich eingeflochten (kein generisches Template-Feeling)?
- [ ] Klingt der Text lebendig, menschlich und empathisch?

---

## 4. Notion-Workflow-Phasen

```text
[Bereit fuer Copywriting] ---> [In Bearbeitung (Texter)] ---> [Review / Lektorat] ---> [Bereit fuer Upload/HTML]
```
