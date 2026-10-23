# Recovered Oracle implementation

Four tables and thirteen views were exported from the owning OCI schema on
October 22, 2026. The supplied inventory marked every object `VALID`.
Recovered SQL preserves the original definitions; new files only add a
statement terminator. The existing Bronze consolidation was identical apart
from its terminator/outer whitespace and was left unchanged.

The [recovery manifest](../docs/oracle_definition_manifest.json) records lengths
and SHA-256 checksums. These files contain DDL, not underlying datasets.

## Setup order for a new environment

This order was checked against all 17 relationships in the supplied Oracle
dependency export. Filenames retain the
original recovery mapping; do not execute every Gold file in filename order.

1. `bronze/00_raw_medicaid_2025_ca.sql`
2. `bronze/00_raw_medicaid_2025_ma.sql`
3. `bronze/00_raw_medicaid_2025_tn.sql`
4. `bronze/00_raw_nadac_2025.sql`
5. `bronze/01_raw_medicaid_2025.sql`
6. `silver/02_clean_medicaid_2025.sql`
7. `silver/03_clean_nadac_2025.sql`
8. `gold/01_quarterly_pharmacy_kpis.sql`
9. `gold/02_quarterly_trends.sql`
10. `gold/03_quarterly_risk_flags.sql`
11. `gold/04_ndc_quarterly.sql`
12. `gold/05_ndc_qoq_analysis.sql`
13. `gold/06_ndc_investigation_queue.sql`
14. `gold/07_ndc_review_dashboard.sql`
15. `gold/08_nadac_quarterly_reference.sql`
16. `gold/09_medicaid_nadac_reference.sql`
17. `gold/10_nadac_coverage_dashboard.sql`

The DDL uses the `ADMIN` schema, `DATA` tablespace, OCI storage settings,
collation, and ingestion annotations. Check target compatibility and privileges
before adapting or executing it. `CREATE TABLE` fails if the table already
exists; `CREATE OR REPLACE` can replace views. Recovery did not execute these
statements or change the existing OCI database.

The three files in `exports/` are read-only Tableau CSV projections, separate
from these 17 recovered definitions. Their sources were confirmed by the author
and column order matches the saved CSV contract; historic query text was not
recovered. Run each export separately after loading the source data.

Views use `FORCE`; after intentional deployment, check validity and compilation
errors. Source tables must be populated using the original loading process
before results can be reproduced. The author-confirmed
[loading/export instructions](../docs/data_loading.md) document that process.
A complete fresh-environment execution and reconciliation remain unverified.

See [dependency and analytical notes](../docs/dependency_map.md) for suppression,
historical pricing, investigation, and verification behavior.
