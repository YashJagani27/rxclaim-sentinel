-- Read-only check of direct dependencies of the 17 recovered objects.
-- Export the complete result as CSV or TSV for comparison with the saved SQL.
SELECT name, type, referenced_owner, referenced_name,
       referenced_type, referenced_link_name
FROM user_dependencies
WHERE name IN (
    'RAW_MEDICAID_2025_CA',
    'RAW_MEDICAID_2025_MA',
    'RAW_MEDICAID_2025_TN',
    'RAW_NADAC_2025',
    'CLEAN_MEDICAID_2025',
    'CLEAN_NADAC_2025',
    'GOLD_MEDICAID_NADAC_REFERENCE',
    'GOLD_NADAC_COVERAGE_DASHBOARD',
    'GOLD_NADAC_QUARTERLY_REFERENCE',
    'GOLD_NDC_INVESTIGATION_QUEUE',
    'GOLD_NDC_QOQ_ANALYSIS',
    'GOLD_NDC_QUARTERLY',
    'GOLD_NDC_REVIEW_DASHBOARD',
    'GOLD_QUARTERLY_PHARMACY_KPIS',
    'GOLD_QUARTERLY_RISK_FLAGS',
    'GOLD_QUARTERLY_TRENDS',
    'RAW_MEDICAID_2025'
)
ORDER BY name, type, referenced_owner, referenced_name, referenced_type;
