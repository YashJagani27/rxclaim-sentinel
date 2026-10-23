-- Read-only export projection for tableau_nadac_coverage.csv.
-- Source view confirmed by the project author; column order matches the saved
-- CSV/Tableau contract. Documented projection, not recovered SQL history.
-- Run separately and download ALL results as CSV with headers.
-- No additional filters or ordering are assumed.
SELECT
    STATE,
    REPORT_YEAR,
    REPORT_QUARTER,
    UTILIZATION_TYPE,
    MEDICAID_ROWS,
    MATCHED_ROWS,
    UNMATCHED_ROWS,
    REPORTABLE_ROWS,
    SUPPRESSED_ROWS,
    REPORTABLE_MATCHED_ROWS,
    MATCH_RATE_PCT
FROM GOLD_NADAC_COVERAGE_DASHBOARD;
