# PQ-0 Requirement Matrix

Author: Raphael Rechberger

Date: 2026-08-23

Status: Complete read-only baseline inventory for M08. This matrix is the hard gate before PQ-1, PQ-2, or PQ-4 product work.

## Scope and Authority

This matrix covers only the first-route release-critical requirements for Steps 1B, 1C, 2, 3, 4A, and 4B. It excludes Step 3B and PQ-3, plus real-output parity and PQ-5.

The approved M08 restoration plan requires every output-critical requirement to have one authority and one verification route before product changes. Source authority is the approved restoration plan at `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md:64-77`. The parity audit is historical requirement evidence. DIB-001 and the deferred GEO restoration plan are the approved Step 4A and 4B requirement sources. The binding test policy controls later validation scope.

## Counts

| Step | Rows | Preserved | Strengthened | Restored | Missing | Separated external |
|---|---:|---:|---:|---:|---:|---:|
| 1B | 5 | 1 | 2 | 0 | 2 | 0 |
| 1C | 12 | 0 | 1 | 0 | 11 | 0 |
| 2 | 10 | 1 | 1 | 0 | 8 | 0 |
| 3 | 5 | 1 | 0 | 0 | 4 | 0 |
| 4A | 8 | 0 | 1 | 6 | 0 | 1 |
| 4B | 6 | 0 | 1 | 4 | 0 | 1 |
| Total | 46 | 3 | 6 | 10 | 25 | 2 |

| Target package | Rows | Planned | Verified | Not needed | Deferred |
|---|---:|---:|---:|---:|---:|
| PQ-1 | 17 | 13 | 4 | 0 | 0 |
| PQ-2 | 15 | 12 | 3 | 0 | 0 |
| PQ-4 | 14 | 0 | 12 | 0 | 2 |

## Fixture Evidence Classification

- Existing `positive-*`, non-AHD, and deterministic fixtures are local contract evidence only. They are not provider-backed, customer, staging, or external-tool evidence.
- Rows classified `verified` have a named current fixture and focused test proving the stated current safety or state requirement.
- Rows classified `planned` require the specifically named future positive and negative fixtures and focused acceptance test before their package can close.
- Rows classified `deferred_external` have a separated production gate and local contract proof but require real external execution before production eligibility.
- `not_applicable` in a schema-field cell means the required typed field is absent from the current contract. It does not mean the requirement is out of scope.

## Acceptance-Proof Gaps

1. Steps 1B, 1C, 2, and 3 lack identified direct positive full-preflight tests covering released predecessor lineage. Their current candidate-level tests do not establish full operational acceptance.
2. Step 4A has no verified positive external Rich Results record. Its production gate remains `deferred_external` and unsatisfied by local fixtures.
3. Step 4B locally proves the immutable four-tool evidence contract but has not executed Screaming Frog, Lighthouse, axe, visual comparison, staging, or production gates.
4. Step 2 to Step 3 real-provider proof remains distinct from deterministic local bridge evidence. No deterministic fixture may be presented as live provider proof.

## Integrity Assertion

The CSV contains 46 stable unique IDs, each with exactly one source authority, one current V2 target seam, a target package allowed by M08, fixture/test routing, and an evidence path. There are zero duplicate IDs, zero multiply-owned requirements, and zero unexplained requirements. PQ-4 contains 12 locally verified rows and 2 explicitly deferred external rows. No Step 3B, PQ-3, PQ-5, M09, M10, live-provider, or real-customer execution claim appears in this inventory.
