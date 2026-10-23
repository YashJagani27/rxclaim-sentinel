-- Read-only export projection for tableau_executive_overview.csv.
-- Source view confirmed by the project author; column order matches the saved
-- CSV/Tableau contract. Documented projection, not recovered SQL history.
-- Run separately and download ALL results as CSV with headers.
-- No additional filters or ordering are assumed.
SELECT
    STATE,
    REPORT_YEAR,
    REPORT_QUARTER,
    UTILIZATION_TYPE,
    SOURCE_ROWS,
    SUPPRESSED_ROWS,
    REPORTABLE_ROWS,
    REPORTED_PRESCRIPTIONS,
    REPORTED_UNITS,
    REPORTED_REIMBURSEMENT,
    REIMBURSEMENT_PER_RX,
    SUPPRESSED_ROW_PCT
FROM GOLD_QUARTERLY_PHARMACY_KPIS;
