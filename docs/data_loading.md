# Source loading and Tableau export workflow

This is the original batch workflow confirmed by the project author on
October 22, 2026. Object definitions and dependencies were separately checked
against supplied Oracle exports. Load counts below are author-reported and
consistent with earlier local file measurements; database counts were not
independently queried during repository recovery.

## Medicaid source preparation and loading

1. Download the 2025 State Drug Utilization CSV files for California,
   Massachusetts, and Tennessee from CMS/Medicaid.gov.
2. Stage the three CSVs in the OCI Object Storage bucket `rxclaim-raw-data`.
3. In Oracle Database Actions, open **Data Studio → Data Load** and select
   the configured **Cloud Store** connection to the bucket.
4. Load each state file into its corresponding Bronze table:

   | State | Bronze table | Reported records |
   | --- | --- | ---: |
   | California | `RAW_MEDICAID_2025_CA` | 160,053 |
   | Massachusetts | `RAW_MEDICAID_2025_MA` | 144,814 |
   | Tennessee | `RAW_MEDICAID_2025_TN` | 92,274 |
   | **Total** | | **397,141** |

5. Apply the existing Bronze union, Silver cleaning, and Gold transformations
   in the [documented dependency order](../sql/README.md). These definitions
   already exist in the original database; recovery did not replace them.

Table DDL retains source field mappings, `FILE$NAME`, and `SYSTIMESTAMP`
ingestion annotations. The exact Cloud Store authentication setup, original
file object names, load-job settings/history, and source release checksums
were not supplied. Credentials and wallets are not included in this repository.

## NADAC preprocessing and loading

1. Download the complete historical 2025 NADAC CSV (approximately 1.61 million
   records, as reported by the author).
2. Run the existing [Python filter](../src/filter_nadac_csv.py) to retain all
   NADAC source records whose NDC appears in the three Medicaid files.
   This preserves historical records, rather than reducing to one price per NDC.
3. The script writes parts of at most 50,000 rows into
   `data/processed/nadac_filtered/`. The completed run produced **28 files**
   containing **1,376,275 records**.
4. Upload these parts to `rxclaim-raw-data`, under `nadac/2025/`.
5. Using Data Studio → Data Load and the Cloud Store connection, load all
   28 parts into the single Bronze table `RAW_NADAC_2025`.
6. The Silver view standardizes prices/dates. Gold views select quarterly
   references and join them with Medicaid utilization.

The existing script expects the historical NADAC filename and the three
`medicaid_2025_{STATE}.csv` files at fixed locations under the user's Downloads
folder. Inspect its path constants before running it in a different environment.
It replaces its previous output parts; preserve any outputs that must be kept.
The separate `src/ingest_nadac.py` is a two-page API experiment, not the source
of the full historical NADAC load.

## Manual Oracle-to-Tableau exports

The author confirmed these Gold sources:

| SQL projection | Gold source | CSV filename |
| --- | --- | --- |
| [Executive overview](../sql/exports/tableau_executive_overview.sql) | `GOLD_QUARTERLY_PHARMACY_KPIS` | `tableau_executive_overview.csv` |
| [NADAC coverage](../sql/exports/tableau_nadac_coverage.sql) | `GOLD_NADAC_COVERAGE_DASHBOARD` | `tableau_nadac_coverage.csv` |
| [Drug investigations](../sql/exports/tableau_drug_investigations.sql) | `GOLD_NDC_REVIEW_DASHBOARD` | `tableau_drug_investigations.csv` |

1. Execute each SELECT separately in Database Actions → SQL Worksheet.
2. Download the complete results as CSV, including headers.
3. Save with the specified name in `data/processed/tableau/`.
4. Check compatibility from the repository root:

   ```bash
   python3 -B scripts/validate_tableau_exports.py --data-dir data/processed/tableau
   ```

5. In Tableau Public, use **Text File** connections to these CSVs. Keep NDC
   as text so leading zeroes are retained.
6. Refresh the Tableau data/extracts and save the workbook after replacing CSVs.

The three SQL files are documented projections using the author's confirmed
source views and the existing CSV column order. They are not recovered query
history. No extra historical filters or sorting are assumed, and these new
projection files have not been executed against OCI during recovery.

## Refresh and monitoring boundaries

This pipeline is batch-based and manually orchestrated. There is no live
Oracle–Tableau connection. Changing Gold views does not regenerate local CSVs
or refresh Tableau extracts. Loading, exports, and Tableau refresh require
explicit actions.

ELK validation logging and monitoring is a separate extension discussed by the
author. Its code/configuration is not present in this repository baseline;
it does not make the loading or export steps automatic. This baseline presents
the existing Python preparation, OCI medallion SQL, and Tableau dashboards.

The loading/export workflow is documented, but a fresh-environment run,
database/file reconciliation, financial reconciliation, and a refreshed Tableau
render have not been independently verified during repository recovery.
