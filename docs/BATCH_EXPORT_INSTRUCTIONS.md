# Recovering Oracle definitions and export lineage

These steps recover existing implementation. They do not create objects, load
data, or deploy transformations. Do not send credentials or wallet files.

## Current recovery status: October 22, 2026

The full 17-object export has now been recovered: 4 tables and 13 views,
including NADAC objects beyond the original nine-view list. All 39 chunks
passed exact-length, unique contiguous part, part-count, and target checks.
See [the manifest](oracle_definition_manifest.json), [SQL setup order](../sql/README.md),
and [updated dependencies](dependency_map.md).

For a complete repeat export, use `docs/export_pipeline_definitions.sql`.
The nine-view CSV importer described below remains a legacy subset workflow;
it does not accept the full six-column TSV or the four table definitions.
The complete recovery preserved existing SQL and added statement terminators
to new files. It did not execute database DDL or load data.

The dependency export has also been supplied and verified: all 17 relationships
match the recovered SQL, with no references outside the recovered object set
and no database links. See `docs/oracle_dependency_manifest.json`.
The author-confirmed loading and export workflow is in `docs/data_loading.md`;
three documented projections are in `sql/exports/`. Original SQL Worksheet
history and exact load-job settings were not supplied.

## Inventory the owning schema

1. Open Oracle Autonomous Database > Database Actions > SQL as the schema owner.
2. Run each SELECT in `docs/inventory_oracle_objects.sql` separately.
3. Export each complete result as its own CSV: object inventory, dependencies,
   columns, constraints, and compilation errors. Save locally and provide the
   exact paths for review. Keep metadata exports out of Git until reviewed.
4. Review the dependency result for additional objects beyond those matching the
   initial name filters. The inventory filters are a starting point, not proof
   of completeness. Objects in another owner's schema require the appropriate
   owner or permitted metadata access; do not invent definitions if absent.

The inventory query has not been executed against OCI during local baseline
testing. Report any errors rather than changing privileges or database objects.

## Export the nine currently named Medicaid views

1. Run `docs/export_all_views.sql` from the owning schema.
2. Export the **complete result**, including all rows and these five columns:
   `VIEW_NAME`, `LAYER_NAME`, `PART_NUMBER`, `DDL_LENGTH`, and `DDL_PART`.
3. The query uses 1,000-character chunks with a maximum of 200 per view. If any
   definition exceeds 200,000 characters, increase the query's chunk limit and
   export again. The importer's length check rejects truncated definitions.
4. From the project root, validate without writing:

   ```bash
   python3 scripts/import_oracle_views.py /path/to/view-export.csv --dry-run
   ```

5. After reviewing the result, restore missing local files:

   ```bash
   python3 scripts/import_oracle_views.py /path/to/view-export.csv
   ```

The helper requires all nine known names, contiguous unique chunk numbers,
consistent lengths, and a matching CREATE VIEW target. It handles unordered
export rows. Existing files are skipped by default. `--overwrite` deliberately
replaces them and should be used only after reviewing the export and existing
SQL. A dry run never writes, even when `--overwrite` is supplied.

The helper validates the complete export before starting writes, but is not a
transactional filesystem backup: an I/O error during writing can leave some new
files present. It never executes SQL or establishes its safety or validity.
Secret-marker screening is a limited precaution, not a complete credential scan.

## Original recovery checklist

The full export now includes the table/view definitions below. This checklist
remains a record of the original recovery scope; see the current status and
loading guide for what is confirmed and what remains unverified:

- The three Bronze source tables and their load/provenance rules.
- NADAC staging/history tables, constraints, views, and load steps.
- Effective-date matching, unit compatibility, coverage and suppression logic.
- Referenced functions, synonyms, materialized views, or other prerequisites.
- The exact queries producing all three Tableau CSVs.

Do not feed unrelated objects into the current nine-view importer: it deliberately
rejects unknown view names. Export additional definitions separately using the
owning schema's object-definition export tools. Review their real names and
dependencies before extending the importer mapping. Do not rename analytical
columns or reconstruct SQL from screenshots.

## Verify and publish

Inspect recovered SQL for credentials, private connection details, database
links, and schema-specific settings. Check Git diffs and run:

```bash
python3 -B -m unittest discover -s tests -v
```

Database object status, compilation errors, join grain, reconciliation, and
export results still need separate OCI verification before automation is claimed.
Do not execute CREATE/REPLACE, DROP, TRUNCATE, or loading steps as part of this
read-only recovery process.

The final Tableau deliverable is
`dashboard/RxClaim_Sentinel_Executive_dashboard.twbx`. It is the selected package,
including three public analytical extracts. Earlier loose `.twb` files are
historical local copies and should not be published as additional deliverables.
Future packages require metadata/data review; do not blanket-stage extracts or
source datasets. Keep environment files, wallets, passwords, and keys out of Git.

Present changed files, test results, and a descriptive commit message for approval
before creating a commit. Obtain approval before any push and verify its remote
branch and commit afterward. ELK implementation is outside this baseline.
