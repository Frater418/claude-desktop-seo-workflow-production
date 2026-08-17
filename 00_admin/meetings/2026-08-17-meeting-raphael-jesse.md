# Meeting - 17. August 2026: Strategie-, Architektur- & Onboarding-Call

**Datum:** 17. August 2026  
**Teilnehmer:** Jesse Jensen (Co-Founder & Lead Heartweb), Raphael Rechberger (Technical Operations & AI Integration Architect)  
**Kontext:** Heartweb SEO-Workflow Automatisierung & Produktions-Rollout  

---

## 1. Management Summary & Kernentscheidungen

1. **Architektur-Review & Freigabe:**
   - Raphael hat den gesamten SEO-Workflow von Jesse in ein modulares, deterministisches Produktions-Framework refaktoriert (Manifest-JSON, AGENTS.md, CLAUDE.md, 120-Tage-Solver v1.2, 4a/4b-Split, Notion-Frontmatter, Design-System).
   - Jesse hat die Architektur vollstaendig bestaetigt: Das Framework bildet die Basis fuer die anstehende Skalierung.

2. **Zukunftsbild Web-UI & Notion-End-to-End-Pipeline:**
   - Langfristiges Ziel: Eine zentrale Web-UI / Dashboard zur gefuehrten Projektinitialisierung, Ausfuehrung und Qualitaetskontrolle.
   - Direkte Synchronisation mit Notion: Automatisierte Anlage von Kundendatenbanken, Aufgaben-Delegation an Mitarbeiter (Copywriter, Entwickler) und 30/60/90-Tage-Performance-Loops.

3. **Kunden-Modelle & Budget-Logik:**
   - Kunden geben in der Regel keine starren KPIs vor; Zieldefinitionen erfolgen partnerschaftlich intern.
   - Verguetung erfolgt ueber ein fixes Basishonorar (zur Kostendeckung) plus erfolgsabhaengige Komponenten.
   - Paid Backlinks: Werden bedarfsorientiert und individuell mit dem Kunden besprochen (im lokalen/nischigen Bereich meist nicht zwingend erforderlich).

4. **Integration Generative Engine Optimization (GEO) & LLM/AI Overviews:**
   - **Kernelement des Folgeauftrags:** Der bestehende Workflow fokussiert Primaer-SEO. Er soll nun tiefgreifend um GEO (Generative Engine Optimization / AI Overviews / SearchGPT / Perplexity / LLM-Zitationen) erweitert werden.
   - Schwerpunkte: Definition von Entity-Graphen, Informationsdichte (Information Gain), direkte Antwort-Strukturen in Hero- und H2-Absaetzen, Long-Tail-Fragenmuster, Schema.org-Erweiterungen und kanalabhaengige ICP-Ausrichtung.

5. **Agency-Meeting & Schnittstellenabstimmung:**
   - Jesse bindet Raphael in das anstehende Meeting mit der Automatisierungs-Agentur (Max) ein, um die Notion-Endpunkte und Middleware-Pipelines direkt technisch abzustimmen.

6. **Zugangsbereitstellung & Pilot-Test:**
   - AgentSEO-Zugang/Subscription sowie Cloud-/Notion-Zugriffe werden ueber Niklas bereitgestellt.
   - Jesse bereitet 2 Kunden-Briefings fuer Raphael vor, um den produktiven Testlauf durchzufuehren.

7. **Abrechnung:**
   - Consulting-Rechnung fuer August wird an Hardware Design LLC (Florida Limited Liability Company, Ansprechpartner: Andreas) ausgestellt.

---

## 2. Detaillierte Themen & Transkript-Highlights

### 2.1 Refaktoriertes Framework & Persistenz
- Die Trennung von Framework-Blueprint und persistentem Kundenordner (`manifest.json`, `design-system.css`, `outputs/`) eliminiert Kontextverluste in LLM-Chats vollstaendig.
- Feste Human-in-the-Loop Quality-Gates an jedem Schritt stellen sicher, dass kein ungepruefter KI-Content in die Produktion fliesst.

### 2.2 Tooling & AgentSEO MCP
- Einsatz von AgentSEO via MCP-Server (>45 Tools) ermoeglicht Keyword- und SERP-Anreicherung in 10 bis 15 Minuten.
- Ergaenzende Plausibilisierung ueber Ahrefs fuer spezifische Maerkte/Nischen.
- Deterministischer Kapazitaets-Solver `capacity_matrix_solver.py` garantiert mathematisch exakte 120-Tage-Plaene ohne Halluzinationen.

### 2.3 GEO / AI Overview Erweiterungspotenzial
- Integration von "Direct Answer"-Blueprints fuer LLM-Crawler (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).
- Strukturierte Beantwortung von Kernfragen direkt in der H1/H2-Ebene.
- ICP- und Intent-basierte Optimierung fuer unterschiedliche Suchraeume (Google Search, AI Overviews, Maps, Fach-Plattformen).

---

## 3. Operative Action Items & Zustaendigkeiten

- [x] **Raphael Rechberger:** Refaktorierung des Grund-Frameworks v1.2.0 abgeschlossen & auf GitHub gepusht.
- [ ] **Niklas / Jesse:** Bereitstellung der Zugangsdaten (AgentSEO Subscription, Cloud, Notion).
- [ ] **Jesse:** Uebermittlung von 2 echten Kundenbriefings fuer den Testlauf.
- [ ] **Jesse:** Einladung von Raphael in das Meeting mit Max (Automatisierungsagentur) nach terminlicher Verschiebung.
- [ ] **Raphael Rechberger:** Tiefen-Research zu 2026 GEO-Standards (Perplexity Deep Research) und Konzeption der Workflow-Erweiterung (GEO-Branch / Spezifikation).
- [ ] **Raphael Rechberger:** Durchfuehrung des ersten Pilot-Rollouts anhand des Kundenbriefings nach Freischaltung.
- [ ] **Raphael Rechberger:** Einreichung der Consulting-Rechnung an Hardware Design LLC (Andreas).

---

## 4. Vollstaendiges Transkript

*(Gespraechsprotokoll abgelegt fuer Nachvollziehbarkeit und Kontext-Wiederherstellung)*

### Attendees: Jesse Jensen, Raphael Rechberger

**Jesse Jensen:** Hi raphael, Hallo. Hallo,  
**Raphael Rechberger:** Schoenen Abend, alles gut,  
**Jesse Jensen:** Ja, alles gut. Heute extrem viel zu tun gehabt, aber alles gut.  
**Raphael Rechberger:** erledigen wir das gerade in Ruhe, so lassen wir den Abend. Jetzt bin ich der Letzte sozusagen heute fuer heute  
**Jesse Jensen:** Ja, leider Gottes. Du, ich habe ja, ich wollte ja auch alles fuer dich vorbereiten, ich habe es aber einfach nicht geschafft, schon extra sehr frueh angefangen heute, aber heute war wirklich komplett voll. Also ich habe bis jetzt eigentlich keine einzige.  
**Raphael Rechberger:** kein Stress. Also ich bin ein neuer Mitarbeiter, den du einarbeiten musst, du musst deine Dinge erledigen. Ich habe da wie gesagt, es wird einfach eine Zeit dauern, bis wir das alles uebergegeben haben, es wird dann kein Stress du, also wie gesagt, ist okay,  
**Jesse Jensen:** Ich habe mir aber schon fuer morgen, weil auch schon Priority, dass du das alles bekommst. Also ich habe mir fuer morgen schon mal einen ganzen 4 Stunden Block freigehalten, wo ich das alles und da habe ich auch keine Meetings. Das heisst, das werde ich auf jeden Fall schaffen in der Zeit. Genau, ich habe zwei Kunden Briefings mal fuer dich vorbereitet schon mal,  
**Raphael Rechberger:** super,  
**Jesse Jensen:** die kann ich dir schon mal rueberschicken.  
**Raphael Rechberger:** Hast du Zeit gehabt kurz, dass du das anschaust, was ich da gemacht habe oder gar nicht, weil sonst,  
**Jesse Jensen:** Ich habe es ueberflogen, aber es waere super, wenn wir es jetzt einmal durchgehen.  
**Raphael Rechberger:** passt ja super. Also grundsaetzlich wie gesagt, also ich mache einfach den Bildschirm auf dann wenn es dir passt... [vollstaendige Aufzeichnung im System persistiert]
