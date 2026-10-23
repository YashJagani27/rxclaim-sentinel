-- Read-only export projection for tableau_drug_investigations.csv.
-- Source view confirmed by the project author; column order matches the saved
-- CSV/Tableau contract. Documented projection, not recovered SQL history.
-- Run separately and download ALL results as CSV with headers.
-- No additional filters or ordering are assumed.
SELECT
    STATE,
    REPORT_YEAR,
    REPORT_QUARTER,
    UTILIZATION_TYPE,
    NDC,
    PRODUCT_NAME,
    PREV_RX,
    REPORTED_RX,
    REPORTED_UNITS,
    REPORTED_REIMBURSEMENT,
    SUPPRESSED_ROWS,
    UNITS_PER_RX,
    REIMBURSEMENT_PER_UNIT,
    REIMBURSEMENT_PER_RX,
    UNITS_PER_RX_CHANGE_PCT,
    REIMB_PER_UNIT_CHANGE_PCT,
    REIMB_PER_RX_CHANGE_PCT,
    WITHIN_NDC_EFFECT,
    INVESTIGATION_CATEGORY,
    REVIEW_PRIORITY
FROM GOLD_NDC_REVIEW_DASHBOARD;
