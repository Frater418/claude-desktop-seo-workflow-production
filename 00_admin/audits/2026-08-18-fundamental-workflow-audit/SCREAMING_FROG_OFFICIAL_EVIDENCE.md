# Screaming Frog Official Evidence

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Zweck: Primaerevidenz fuer den Heartweb Quality-Gate-Adapter

## Verifizierte lokale CLI

Pfad:

`C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe`

Der lokale Aufruf `--help` war erfolgreich und bestaetigte:

- `--crawl`
- `--crawl-list`
- `--config`
- `--headless`
- `--output-folder`
- `--export-format`
- `--overwrite`
- `--save-crawl`
- `--export-tabs`
- `--bulk-export`
- `--save-report`
- `--use-google-search-console`
- `--use-google-analytics-4`
- `--use-pagespeed`
- `--use-ahrefs`

## Verifizierte Exportgruppen

Der lokale Aufruf `--help export-tabs` bestaetigte unter anderem:

- `Internal:All`
- `Response Codes:All`
- `Page Titles:All`
- `Meta Description:All`
- `H1:All`
- `H2:All`
- `Canonicals:All`
- `Hreflang:All`
- `Structured Data:All`
- `Links:All`
- `Security:All`
- `Accessibility:All`
- `Search Console:All`
- `PageSpeed:All`

Der lokale Aufruf `--help save-report` bestaetigte unter anderem:

- `Crawl Overview`
- `Issues Overview`
- `Redirects:Redirect Chains`
- `Canonicals:Canonical Chains`
- `Hreflang:All hreflang URLs`
- `Structured Data:Validation Errors & Warnings`
- `Structured Data:Google Rich Results Features`
- `Accessibility:Accessibility Violations Summary`

## Offizielle Quellen

- https://www.screamingfrog.co.uk/seo-spider/user-guide/general/
- https://www.screamingfrog.co.uk/seo-spider/user-guide/configuration/
- https://www.screamingfrog.co.uk/seo-spider/user-guide/tabs/

Die offiziellen Dokumente bestaetigen:

1. Die kostenlose Version crawlt bis zu 500 URLs.
2. Lizenzierte Funktionen umfassen unter anderem gespeicherte Crawls, JavaScript Rendering, Custom Extraction, GA, GSC, PageSpeed und Scheduling.
3. Der Internal Export enthaelt Statuscode, Indexability, Titles, Meta Descriptions, H1, H2, Canonicals, Inlinks, Outlinks, Hashes und Redirectdaten.
4. Hreflang, strukturierte Daten und Rich-Result-Validierung sind separate, konfigurierbare Pruefbereiche.
5. JSON-LD, Microdata und RDFa koennen extrahiert und gegen Schema.org sowie Google Rich Result Features validiert werden.

## Heartweb-Grenzen

- Das 500-URL-Limit darf nie still als vollstaendiger Crawl interpretiert werden.
- Erweiterte Integrationen gelten nur, wenn die entsprechende lokale Konfiguration und Lizenz verifiziert sind.
- Ein Screaming-Frog-Ergebnis ist technische Crawl-Evidenz, kein Ersatz fuer fachliche Claim-, Markt- oder Compliance-Evidenz.
- Ahrefs, GSC, GA4 und PageSpeed werden nur bei explizit verfuegbarem Zugriff aktiviert. Fehlender Zugriff erzeugt einen strukturierten Blocker oder eine begruendete Not-Applicable-Entscheidung, niemals einen stillen Fallback.
