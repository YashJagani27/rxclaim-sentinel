# Data dependencies and verification status

Updated October 22, 2026 after recovery of the supplied OCI definition export.
All 17 objects in the supplied inventory were marked `VALID`. The export
contained 39 chunks; exact character lengths, contiguous unique part numbers,
declared part counts, and CREATE targets passed offline validation. No database
DDL or data loading was executed during recovery.

## Dependencies visible in recovered SQL

| Object | Direct project dependencies |
| --- | --- |
| `RAW_MEDICAID_2025` | Three state tables: CA, MA, TN |
| `CLEAN_MEDICAID_2025` | `RAW_MEDICAID_2025` |
| `CLEAN_NADAC_2025` | `RAW_NADAC_2025` |
| `GOLD_QUARTERLY_PHARMACY_KPIS` | `CLEAN_MEDICAID_2025` |
| `GOLD_QUARTERLY_TRENDS` | `GOLD_QUARTERLY_PHARMACY_KPIS` |
| `GOLD_QUARTERLY_RISK_FLAGS` | `GOLD_QUARTERLY_TRENDS` |
| `GOLD_NDC_QUARTERLY` | `CLEAN_MEDICAID_2025` |
| `GOLD_NDC_QOQ_ANALYSIS` | `GOLD_NDC_QUARTERLY` |
| `GOLD_NDC_INVESTIGATION_QUEUE` | `GOLD_NDC_QOQ_ANALYSIS` |
| `GOLD_NDC_REVIEW_DASHBOARD` | `GOLD_NDC_INVESTIGATION_QUEUE`, `GOLD_NDC_QUARTERLY` |
| `GOLD_NADAC_QUARTERLY_REFERENCE` | `CLEAN_NADAC_2025` |
| `GOLD_MEDICAID_NADAC_REFERENCE` | `CLEAN_MEDICAID_2025`, `GOLD_NADAC_QUARTERLY_REFERENCE` |
| `GOLD_NADAC_COVERAGE_DASHBOARD` | `GOLD_MEDICAID_NADAC_REFERENCE` |

The supplied Oracle dependency export confirms all 17 direct relationships
above (including the three separate state-table edges). Every referenced object
is in the recovered set, all referenced owners are `ADMIN`, and no database
links are listed. The documented setup order respects every exported edge.
See [SQL setup order](../sql/README.md), the
[definition manifest](oracle_definition_manifest.json), and the
[dependency manifest](oracle_dependency_manifest.json).

## Bronze loading evidence

All four source-table definitions are present. Source business fields are
`VARCHAR2(64)`; provenance uses `FILENAME` and a time-zone-aware timestamp.
Oracle ingestion annotations record source mappings and expressions
`FILE$NAME` and `SYSTIMESTAMP`. These annotations are not a complete loader or
a record of the actual uploaded files. The author confirmed Object Storage
staging in `rxclaim-raw-data` and Cloud Store Data Load; see
[the loading guide](data_loading.md). Exact load-job settings/history and
database counts remain independently unverified. The recovered
table DDL defines no primary keys. The consolidation uses `UNION ALL`,
retaining duplicates.

Earlier local source-file measurements recorded 397,141 rows across CA, MA, and
TN and 1,376,275 filtered NADAC rows across 28 files. These are not Oracle
reconciliation results.

## Silver semantics

Medicaid conversion errors become null. Numeric measures are populated only
when suppression text equals `false`, ignoring case/outer spaces. The
`IS_SUPPRESSED` label is `Y` for `true` and `N` otherwise: unexpected/null flags
can be labeled reportable while their measures are null. Identifiers are trimmed
text; the views do not enforce 11-digit NDC validity.

NADAC prices convert to numbers, and effective/as-of dates use `MM/DD/YYYY`.
Conversion errors become null. NADAC Silver retains provenance.

## Gold behavior and analytical limits

- State quarterly trends compare the previous available row, without enforcing
  consecutive quarters. Summary risk flags trigger at cost growth >= 5% with
  volume growth < 0.
- NDC comparisons require consecutive quarters, zero suppressed source rows,
  at least 30 prescriptions in both quarters, and positive comparison metrics.
- The investigation queue retains reimbursement-per-Rx growth >= 20% and
  positive `WITHIN_NDC_EFFECT`. The effect is current prescription count times
  the difference in reimbursement per prescription, not confirmed savings or
  overpayment. Priorities use >= $500,000 for high and >= $100,000 for medium.
- NADAC quarterly reference selection keeps positive prices with `AS_OF_DATE`
  in 2025, choosing the latest date per NDC/quarter. Tied latest dates have no
  secondary ordering; pricing unit is not in the partition key.
- Medicaid joins the reference on NDC/year/quarter. Effective dates are exposed
  but do not govern selection, and pricing units are not reconciled. Coverage
  indicates reference availability, not proven price comparability.
- NDC investigation rules use Medicaid trends independently of NADAC coverage.

These describe recovered code, not newly validated business rules. The SQL
was preserved without analytical changes.

## Tableau lineage confirmed by the author

The packaged workbook contains three principal dashboards, an alternate layout,
16 worksheets, and three extracts. Earlier local CSV counts were 24 executive,
24 coverage, and 7,652 investigation records; no new cloud run was performed.

| CSV interface | Author-confirmed source | Historic SQL text recovered? |
| --- | --- | --- |
| `tableau_executive_overview.csv` | `GOLD_QUARTERLY_PHARMACY_KPIS` | No |
| `tableau_nadac_coverage.csv` | Selected/reordered fields of `GOLD_NADAC_COVERAGE_DASHBOARD` | No |
| `tableau_drug_investigations.csv` | `GOLD_NDC_REVIEW_DASHBOARD` | No |

The author confirmed manual SQL Worksheet CSV exports and Tableau Public Text
File connections. The [documented SELECTs](../sql/exports/) project the existing
contract columns from these confirmed sources. They do not recover historical
query filters/ordering or establish extract freshness. See the
[loading and export guide](data_loading.md).

## Remaining baseline work

The author-confirmed loading and CSV export workflow is now documented.
The portfolio baseline is ready for final review and publication; historic
query text and exact load-job settings are recorded as unavailable.

Database/file reconciliation, a fresh pipeline run, and Tableau refresh remain
unverified; the repository does not claim these checks have been completed.

Offline tests check import handling and CSV/workbook compatibility, not Oracle
execution, financial reconciliation, or screening accuracy. Automation and
scheduling are subsequent enhancements. Recovery made no commit or push.
