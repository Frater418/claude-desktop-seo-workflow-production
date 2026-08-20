# Lane 1: Domain and Prompt Audit

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Auditmodus: Read-only source audit
- Urteilsebene: Fachliche Domainlogik, Promptvertraege und Kunden-Output-Qualitaet

## Executive Verdict

**No-Go fuer die Zielarchitektur UI, n8n und Notion sowie fuer die zehn realen Kundenfaelle.** Der Workflow ist ein gut dokumentierter, sinnvoll gegateter Einzelmarkt-SEO-Workflow fuer einen vorwiegend deutschsprachigen lokalen Pilotfall. Er ist noch kein ausfuehrbarer, internationaler und mandantenfaehiger Domainvertrag. Insbesondere kann das aktuelle Manifest nicht gleichzeitig Leistungsort, Suchmarkt, Suchregion, Sprache, Marktphase, Domain, Marke und GBP-Hierarchie modellieren. Das betrifft mindestens Ayurveda Shunyata Villa, Epargne Plurielle, Daniela Landgraf, MobilePhysiotherapie24 und Shunyata Villas Bali direkt.

Die groessten Risiken sind nicht fehlende Prompttexte, sondern falsche Geo-Klassifikation, nicht kontrollierbare YMYL-Claims, unvollstaendig durchsetzbare State-Uebergaenge und providerabhaengige Defaults. Ein schema-valides Manifest kann derzeit einen fachlich falschen Markt, eine unzulaessige Completion oder nicht deterministisch erzeugte Kundenoutputs enthalten.

## Evidence Scope

Gelesene Primaerevidenz:

- `AGENTS.md:10-28, 49-58, 62-73`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md:9-147`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md:7-39`
- `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:10-49`
- Alle neun Produktionsprompts unter `prompts/`: `0-kickoff.xml.md:1-142`, `1-pillar-identifikation.xml.md:1-83`, `1b-seitenarchitektur.xml.md:1-78`, `1c-pillar-template.xml.md:1-84`, `2-cluster-recherche.xml.md:1-106`, `3-120-tage-plan.xml.md:1-103`, `3b-performance-check.xml.md:1-76`, `4a-content-briefing-und-schema.xml.md:1-122`, `4b-landingpage-html.xml.md:1-89`
- `standards/manifest.schema.json:1-722`
- `standards/location-codes.json:1-22`
- `standards/dateinamen-und-output-vertrag.md:10-68`
- `docs/05-human-in-the-loop.md:10-120`
- `mcp/tool-contracts/agentseo_keyword_enricher.json:1-58`
- `mcp/tool-contracts/serp_gap_analyzer.json:1-38`
- `00_admin/PROJECT_STATE.md:26-100`

Baseline treatment: this report follows the host-provided baseline rather than container Git metadata, as required by `HOST_GIT_BASELINE.md:35-39`. It assesses current file contents. Tracked and untracked candidates listed in `HOST_GIT_BASELINE.md:11-33` are not treated as committed production proof.

## Strengths

1. **Useful artefact chain:** The outputs form a legible progression from manifest to pillar inventory, architecture, enriched cluster CSV, plan, briefing and HTML. The expected paths are explicit in `standards/dateinamen-und-output-vertrag.md:44-56`.
2. **Correct fail-fast intent for keyword data:** Prompt 2 requires a target market triple and rejects missing metrics rather than inventing values in `prompts/2-cluster-recherche.xml.md:25-30, 43-66, 81-87`.
3. **A real distinction between customer services and internal work:** Prompt 0 correctly excludes regions and recruiting from `core_services` in `prompts/0-kickoff.xml.md:76-85`, matching the use-case requirement to separate workstreams in the matrix at `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:23-34`.
4. **Human review is intended at the right decision points:** The separate gates cover strategy, design, data, roadmap, editorial and frontend review in `docs/05-human-in-the-loop.md:22-120`.
5. **Customer-facing HTML has explicit baseline quality requirements:** The templates require visible Local SEO signals, semantic sections, embedded structured data and no CDN dependency in `prompts/4b-landingpage-html.xml.md:39-71`.
6. **Known provider weakness is documented:** The location defect of `agentseo_content_serp_outline` is openly recorded in `standards/location-codes.json:18-20`. This transparency is valuable, but it must become an enforced routing decision.

## P0 Findings

### P0-1: The market model is incapable of representing the required customer reality

**Fact:** The manifest has exactly one `country`, one `location_code`, one `language`, one `primary_region` and undifferentiated string arrays for secondary regions in `standards/manifest.schema.json:131-145, 617-630`. `country` is limited to DE, AT and CH at `standards/manifest.schema.json:617-623`; the code list also contains only those markets at `standards/location-codes.json:8-16`.

**Interpretation:** This cannot model a Sri Lankan service location with separate DE, AT and CH search markets, a French market with a Luxembourg product jurisdiction, a Germany plus Austria expansion, French and English language variants, Bali with international English demand, or a primary versus expansion phase. It also cannot distinguish a target city from a physical location, a service area, a search region, or a provider location code. A single default language would silently create wrong research data.

**Risk:** Incorrect market data, illegal or irrelevant claims, false Local SEO pages, and manual exception handling in every non-DE/AT/CH case.

**Target correction:** Replace the scalar market fields with a versioned array of market deployments. Each deployment must include an immutable ID, search-market country and provider codes, language and locale, phase, service geography, service-area policy, legal jurisdiction, active status and primary-versus-secondary role. Model physical entities, brands, domains, satellites and GBPs separately with their ownership and location evidence.

### P0-2: The workflow can complete steps and cross gates without machine-enforced preconditions

**Fact:** Completion status is independent of required counts and artefact evidence. `clusters_per_pillar` and `validated_rows_per_pillar` are optional properties in `standards/manifest.schema.json:384-392, 484-491`; neither uses conditional schema rules requiring them when a phase is `completed`. Prompt 1 directly sets completion in `prompts/1-pillar-identifikation.xml.md:49-51`, Prompt 2 does the same in `prompts/2-cluster-recherche.xml.md:75-78`, and Prompt 3 does likewise in `prompts/3-120-tage-plan.xml.md:68-71`, before their human gate instructions. The schema does not model gates beyond Gate 0 in `standards/manifest.schema.json:238-279, 326-581`.

**Interpretation:** A prompt can state that a gate exists, but neither a JSON Schema validator nor a future n8n worker can prove approval, permitted predecessor state, output checksum, reviewer identity, run ID, retry count or decision timestamp. This violates the requested state machine and auditable human approval model.

**Risk:** Unapproved or partially valid strategy, data or content can be handed to Notion and production while retaining a `completed` status.

**Target correction:** Define one explicit transition contract with statuses such as `pending`, `running`, `awaiting_review`, `approved`, `blocked`, `failed`, `superseded` and `rolled_back`. Make every transition carry `run_id`, input and output content hashes, validator results, operator decision, timestamp and error object. Enforce transitions in a deterministic validator or workflow service, not in prose alone.

### P0-3: YMYL, claims and local-presence controls are absent from the domain contract

**Fact:** The real matrix explicitly includes medical, care, finance, sexuality and sustainability-risk projects and requires market-specific claims, legal and evidence rules at `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:12-21, 23-34`. The manifest contains no risk class, regulated-claim policy, evidence source, reviewer role, disclaimer policy, physical-location proof, licence or regulatory-jurisdiction field in `standards/manifest.schema.json:33-720`. Prompt 4a demands a hard data point per H2 and "definitive" language in `prompts/4a-content-briefing-und-schema.xml.md:50-57` but does not require source provenance or legal approval. Prompt 4b asks for NAP, map and local testimonials when local in `prompts/4b-landingpage-html.xml.md:49-59` without a rule that the entity has a verified physical location or permitted service-area representation.

**Interpretation:** The system turns a model instruction into medical, financial or local-business output without a verified evidence ledger. It has no basis to distinguish legitimate service-area content from a prohibited or misleading city-location claim.

**Risk:** Compliance breach, misleading Local SEO output, unsupported medical or financial assertions, and brand damage.

**Target correction:** Add a mandatory `risk_and_compliance` contract per market deployment and per output. It must classify YMYL and regulated content, bind claims to immutable evidence records, specify mandatory disclaimer and legal reviewer gates, record physical-location and service-area evidence, and reject claims or NAP output that lack approval.

### P0-4: Prompt 4a can consume a geo-invalid SERP result despite a documented provider limitation

**Fact:** The provider limitation says `agentseo_content_serp_outline` cannot accept `location_code` and resolved Germany to Many, Louisiana in `standards/location-codes.json:18-20`. Prompt 4a nevertheless lists that tool as a live SERP source in `prompts/4a-content-briefing-und-schema.xml.md:43-49` and contains no required `location`, `location_code`, `language`, asynchronous job handling, response geo assertion or fallback rejection. The SERP tool contract permits defaults of Germany and German and requires only `keyword` in `mcp/tool-contracts/serp_gap_analyzer.json:8-17`.

**Interpretation:** A critical final-briefing input can be produced using an explicitly known wrong geography. This contradicts the global rule requiring the complete market triple in `AGENTS.md:55-57`.

**Risk:** A location-specific briefing can be based on the wrong SERP, intent and competitors while appearing live-data grounded.

**Target correction:** Route SERP analysis through a provider abstraction that declares geo capability. For a required target market, reject a provider response unless its returned provider codes match the deployment contract. If the provider cannot carry the required code, stop with a named capability error and do not generate the briefing.

## P1 Findings

### P1-1: Prompt-only classification causes false Local SEO and scope drift

**Fact:** Prompt 1 requires local marking only when the briefing says Multi-Location in `prompts/1-pillar-identifikation.xml.md:54-59`. Prompt 2 brainstorms local variants "bei Multi-Location" in `prompts/2-cluster-recherche.xml.md:32-42`. Prompt 3 treats all mandatory locations as Phase 1 or 2 and gives local landingpages a factor of four in `prompts/3-120-tage-plan.xml.md:32-47`. The matrix expressly says a national B2B company is not automatically Local SEO and a regional provider may serve a target city without a physical location at `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:36-45`.

**Interpretation:** There is no customer archetype or deployment policy for local, regional, national, international, programmatic-local and digital models. The same keyword logic therefore drives fundamentally different website architectures.

**Target correction:** Make `seo_operating_model` and a `location_page_policy` required and enumerated. The policy must distinguish physical-location pages, service-area pages, national thematic pages, international language-market pages and programmatic-local pages. Enforce separate evidence, scale limits, content uniqueness, GBP eligibility and approval requirements for each.

### P1-2: The prompt sequence and gate names contradict the documented operating model

**Fact:** Prompt 3 points next to 3b in `prompts/3-120-tage-plan.xml.md:4-11`; Prompt 3b points next to 4a in `prompts/3b-performance-check.xml.md:4-11`; and Prompt 4a declares Prompt 3 as its predecessor in `prompts/4a-content-briefing-und-schema.xml.md:4-11`. Documentation states 3b starts after day 30 and runs parallel to day-to-day execution in `docs/05-human-in-the-loop.md:113-120`. Prompt gates are GATE-0, GATE-1, GATE-1B, GATE-1C, GATE-2, GATE-3, GATE-3B, GATE-4A and GATE-4B across the prompt files, while the handbook defines seven differently numbered gates in `docs/05-human-in-the-loop.md:22-39`.

**Interpretation:** A human operator, UI or n8n implementation cannot derive one unambiguous execution graph or approval identity.

**Target correction:** Publish a canonical machine-readable workflow graph. Define 3b as a cyclic side workflow triggered by accepted publication and elapsed time, not as a predecessor of 4a. Give every gate one immutable ID and map display labels separately.

### P1-3: The provider contract contradicts the no-default and full-parameter rules

**Fact:** Prompt 2 says all five keyword request parameters are mandatory in `prompts/2-cluster-recherche.xml.md:43-50`. The actual contract requires only `keywords`, omits `location_code` and `sync`, and defaults location to Germany and language to German in `mcp/tool-contracts/agentseo_keyword_enricher.json:8-35`.

**Interpretation:** The executable contract permits exactly the silent default behaviour the prompt prohibits.

**Target correction:** Replace provider-specific prompt instructions with a transport-neutral request schema requiring deployment ID, provider capability, location name, location code, language, locale, async policy, cost budget and idempotency key. Reject incomplete calls before provider dispatch.

### P1-4: Output quality is prescribed, not verifiably accepted

**Fact:** Prompt 1 estimates word counts from a website in `prompts/1-pillar-identifikation.xml.md:31-33`. Prompt 1b requires text and HTML to be "100% synchron" in `prompts/1b-seitenarchitektur.xml.md:55-60` without a comparator. Prompt 1c requires a screenshot-derived design system and all pillar templates in `prompts/1c-pillar-template.xml.md:20-58`, but does not define the fidelity evidence or a template manifest. Prompt 4a calls JSON-LD validated in `prompts/4a-content-briefing-und-schema.xml.md:59-77`, but Gate 5 only asks the reviewer to judge it in `docs/05-human-in-the-loop.md:90-98`.

**Interpretation:** Critical quality checks are prose assertions. There is no required input crawl snapshot, SERP evidence snapshot, HTML accessibility check, schema validation record, content-claim ledger or output-to-plan trace.

**Target correction:** Give each output a typed artefact contract with producer run ID, source artefacts, SHA-256, required fields, validator records, review decision and publish state. Treat estimates as estimates with a source and timestamp, never as observed facts.

## P2 Findings

### P2-1: The manifest accepts inconsistent geo data and unknown fields

**Fact:** `country` and `location_code` are independent scalar fields in `standards/manifest.schema.json:617-630`; no schema relation ties Germany to 2276. Root and nested objects generally omit `additionalProperties: false`, including the root at `standards/manifest.schema.json:33-720` and phase objects at `standards/manifest.schema.json:339-581`.

**Interpretation:** A valid manifest can use `country: DE` with a foreign code or carry ungoverned state that no UI, Notion integration or worker understands.

**Target correction:** Validate market objects against a versioned registry and reject undeclared properties except in explicit extension namespaces.

### P2-2: The capacity model does not fit variable-scale delivery

**Fact:** The schema only sets defaults for 10 to 15 hours and does not constrain min less than or equal to max in `standards/manifest.schema.json:165-187`. Prompt 3 says every week must exactly exhaust the budget in `prompts/3-120-tage-plan.xml.md:13-18`, but later permits active weeks between 10 and 15 hours and buffers in `prompts/3-120-tage-plan.xml.md:54-59`; the validator rule says only the maximum is enforced in `prompts/3-120-tage-plan.xml.md:74-78`.

**Interpretation:** The same fixed 17-week, 10 to 15-hour model is unsuitable for a slow one-person regional business and aggressive programmatic-local rollout. The stated behaviour is also internally inconsistent.

**Target correction:** Parameterize planning by delivery model, budget, team capacity, expansion phase and mandatory policy work. Enforce feasibility, include compliance and review effort, and allow an approved capacity exception instead of an implicit universal schedule.

### P2-3: Notion compatibility is only YAML-shaped, not a Notion operational contract

**Fact:** Step 4a calls its frontmatter Notion-ready in `prompts/4a-content-briefing-und-schema.xml.md:67-70` and gives an illustrative fixed field list in `prompts/4a-content-briefing-und-schema.xml.md:81-109`. The broader target requires Notion to manage customers, phases, approvals, outputs and assignment in `AUDIT_BRIEF.md:15-25`, but no manifest field or output contract contains Notion database IDs, property mappings, page IDs, revision IDs, workflow run IDs or conflict policy.

**Interpretation:** YAML can be imported manually but cannot safely act as the control plane for concurrent UI and n8n work.

**Target correction:** Define versioned Notion entity contracts and a bidirectional synchronization policy with immutable external IDs, expected revision, status mapping and conflict handling.

### P2-4: Core provider and verification sources are not represented as interchangeable evidence sources

**Fact:** The target architecture names DataForSEO as preferred raw-data source and AgentSEO as selective enrichment in `AUDIT_BRIEF.md:20-25`. Prompt 2 is exclusively AgentSEO-driven in `prompts/2-cluster-recherche.xml.md:13-16, 43-66`; Prompt 4a is likewise AgentSEO-driven in `prompts/4a-content-briefing-und-schema.xml.md:43-49`. The current contracts cover AgentSEO and schema only in `mcp/tool-contracts/agentseo_keyword_enricher.json:1-58`, `mcp/tool-contracts/serp_gap_analyzer.json:1-38` and `mcp/tool-contracts/schema_jsonld_generator.json`.

**Interpretation:** Costs, rate limits, raw SERP provenance and provider fallibility cannot be managed at the domain layer. The system cannot satisfy the requested DataForSEO-first strategy without prompt rewrites and ad hoc routing.

**Target correction:** Introduce provider-neutral evidence records and capability-based adapters for DataForSEO, AgentSEO, GSC, GBP, Analytics, Screaming Frog and permitted rank sources. Include source, query, market deployment, retrieval time, cost, response hash and validator result.

## P3 Findings

### P3-1: Documentation drift creates avoidable operator error

**Fact:** `AGENTS.md:64-70` says the JSON-LD validator has no CLI and only reports readiness, while the README describes a full CLI and strict mode in `README.md` section 3.4. `PROJECT_STATE.md:7` calls v1.3.0 in progress, while the README calls itself v1.4.0 and production active in `README.md` section 1.

**Interpretation:** Operators cannot safely know which validation path, version or release status governs a customer run.

**Target correction:** Generate one release manifest from validated source metadata, declare the compatibility version of every prompt, schema and tool, and fail a release check on conflicting operational statements.

### P3-2: Prompt hygiene defects reduce portability and trust

**Fact:** Prompt 1b contains malformed text in the Section-ID description at `prompts/1b-seitenarchitektur.xml.md:19`. Several prompts depend on client-local paths, browser behaviour or chat-file semantics, for example `prompts/1c-pillar-template.xml.md:20-24` and `prompts/1b-seitenarchitektur.xml.md:44-49`, rather than a platform-neutral input attachment contract.

**Interpretation:** These are not primary domain blockers, but they create friction when moving from Claude Desktop to an API worker.

**Target correction:** Normalize prompt encoding, move runtime-specific instructions into adapters, and retain only typed input and output references in the canonical workflow contract.

## Contradictions and False-Green Risks

1. **Sequence contradiction:** Prompt 3 routes through 3b before 4a, while the handbook makes 3b a delayed parallel cycle. Evidence: `prompts/3-120-tage-plan.xml.md:4-11`, `prompts/3b-performance-check.xml.md:4-11`, `prompts/4a-content-briefing-und-schema.xml.md:4-11`, `docs/05-human-in-the-loop.md:113-120`.
2. **Gate contradiction:** Prompt gate labels and handbook gate labels describe different numbered state machines. Evidence: all `human_review_gate` blocks in `prompts/0-kickoff.xml.md:130-141` through `prompts/4b-landingpage-html.xml.md:84-88`, versus `docs/05-human-in-the-loop.md:22-39`.
3. **Provider contradiction:** The no-default rule is stated in `AGENTS.md:53-57` and Prompt 2, but the keyword contract defaults Germany and German and does not carry `location_code` or `sync`. Evidence: `prompts/2-cluster-recherche.xml.md:43-50`, `mcp/tool-contracts/agentseo_keyword_enricher.json:8-35`.
4. **Geo false green:** Schema validation cannot prove country-code pairing, market phase, language-market pairing, physical presence or provider response match. Evidence: `standards/manifest.schema.json:617-665`, `standards/location-codes.json:8-20`.
5. **Completion false green:** A phase can be `completed` without counts, artefact integrity, prior approval or a later gate. Evidence: `standards/manifest.schema.json:362-581`, `prompts/1-pillar-identifikation.xml.md:49-51`, `prompts/2-cluster-recherche.xml.md:75-78`.
6. **Compliance false green:** JSON-LD syntax and visible NAP do not validate truth, legal basis, claim evidence or GBP eligibility. Evidence: `prompts/4a-content-briefing-und-schema.xml.md:59-77`, `prompts/4b-landingpage-html.xml.md:49-71`.
7. **Test false green:** The project state records fixtures for a single simCura care example in `00_admin/PROJECT_STATE.md:56-59`; no evidence scope read here establishes acceptance coverage for the ten required archetypes in the real-use-case matrix.

## Target Corrections

1. Establish a canonical, versioned domain model before editing individual prompts. It must separate customer, workspace, brand, domain, entity, physical location, service area, target market, language locale, legal jurisdiction, market phase, workstream and output.
2. Establish a workflow transition and gate service contract. The UI, n8n and Notion adapters must call this contract instead of mutating phase fields independently.
3. Create a policy engine for YMYL, claims, local presence, programmatic scale and evidence. It must block invalid output paths before generation.
4. Replace tool-named prompt instructions with provider-neutral evidence requests and capability checks. DataForSEO should supply scalable raw keyword and SERP data; AgentSEO should be optional semantic enrichment only where its declared capability matches the deployment.
5. Rebuild prompts as thin step contracts that consume and produce typed artefacts. Prompt text must not be the only enforcement layer.
6. Add end-to-end acceptance fixtures for every real archetype and for prohibited cases, including incorrect country-code pairs, a market without a supported provider, an unverified city, an unapproved medical claim and a stale concurrent Notion update.

## Machine-Checkable Acceptance Criteria

1. A manifest schema fixture representing each of the ten matrix projects validates without extensions or handwritten exceptions, including at least two concurrent target markets where required. Source scenarios: `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:10-21`.
2. A deployment cannot validate unless `country`, provider `location_code`, provider location name, `language`, `locale` and market phase are present and map to one registry entry.
3. A German service location with an Austrian search market, a Sri Lankan service location with DACH target markets, a Luxembourg product jurisdiction with a French tax market, and a Bali location with English international markets are distinct valid fixtures.
4. A national B2B deployment cannot create a Local SEO or GBP-required task without an explicit location-page policy and verified physical or service-area evidence.
5. A programmatic-local deployment cannot schedule a page unless the location policy, uniqueness evidence, entity ownership and approval scope are present.
6. A YMYL or regulated output cannot reach `awaiting_review` unless every claim has an evidence ID, source date, jurisdiction, required disclaimer and reviewer policy; it cannot reach `approved` without the required reviewer decision.
7. A phase cannot become `completed` until its predecessor is approved, its required artefacts pass their validators, counts meet the policy and its gate approval record includes a run ID and timestamp.
8. A provider request fails before dispatch if any required market field, asynchronous policy, idempotency key or cost budget is absent. A provider response fails validation if its returned market identifiers differ from the deployment.
9. The known SERP provider capability gap in `standards/location-codes.json:18-20` is represented by an automated negative test that blocks briefing generation for a market requiring a location code.
10. The canonical workflow graph has exactly one route from planning to first briefing and models 3b as a repeatable post-publication side workflow. All prompt metadata and UI or n8n mappings are generated from it.
11. Every output includes immutable source-artifact IDs, content hash, producer run ID, schema version, validation record and review state. A Notion synchronization rejects a stale expected revision.
12. Release validation fails if README, project state, operational instructions, schema version or tool CLI capability make contradictory claims.

## Exact Fix Order

1. Freeze the current prompt and schema versions as the legacy pilot contract. Do not expand market support through prompt exceptions.
2. Author the canonical domain model and versioned market registry, including entity, location, service area, brand, domain, GBP, jurisdiction, language locale and phase relationships.
3. Implement the transition, gate and artefact-evidence contracts with deterministic validation and immutable run identifiers.
4. Implement the YMYL, claims, local-presence and programmatic-local policy engine with negative fixtures.
5. Implement provider-neutral request and evidence contracts, then add DataForSEO and AgentSEO adapters with capability checks, async control, cost budgets and response geo validation.
6. Define Notion database mappings, revision policy and UI or n8n adapter boundaries against the canonical contracts.
7. Rewrite all nine prompts from the canonical graph and contracts. Remove direct uncontrolled phase completion and runtime-specific assumptions.
8. Add the ten positive real-customer fixtures and the required negative fixtures. Run end-to-end acceptance through the same public workflow surface used by UI and n8n.
9. Align README, AGENTS, PROJECT_STATE, output contract, gate handbook and tool documentation from generated release metadata.

## Go Verdict

**No-Go.** Do not position the current repository as a production-standard framework for UI, n8n, Notion, international, multi-market, programmatic-local or regulated YMYL delivery. A limited conditional pilot is possible only for one approved DE, AT or CH market, one language, one verified brand and service model, manually approved gates, and non-regulated content with a human legal and factual review outside the current contracts. That pilot limitation is narrower than the requested target architecture and does not resolve the P0 findings.
