-- Read-only export of the 17 objects confirmed in the OCI inventory.
-- Export all rows and all six columns as CSV. No database objects are modified.
-- Explicit names avoid evaluating GET_DDL against unrelated USER_OBJECTS rows.
WITH object_names (object_type, object_name) AS (
    SELECT 'TABLE', 'RAW_MEDICAID_2025_CA' FROM dual UNION ALL
    SELECT 'TABLE', 'RAW_MEDICAID_2025_MA' FROM dual UNION ALL
    SELECT 'TABLE', 'RAW_MEDICAID_2025_TN' FROM dual UNION ALL
    SELECT 'TABLE', 'RAW_NADAC_2025' FROM dual UNION ALL
    SELECT 'VIEW', 'RAW_MEDICAID_2025' FROM dual UNION ALL
    SELECT 'VIEW', 'CLEAN_MEDICAID_2025' FROM dual UNION ALL
    SELECT 'VIEW', 'CLEAN_NADAC_2025' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_MEDICAID_NADAC_REFERENCE' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NADAC_COVERAGE_DASHBOARD' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NADAC_QUARTERLY_REFERENCE' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NDC_INVESTIGATION_QUEUE' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NDC_QOQ_ANALYSIS' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NDC_QUARTERLY' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_NDC_REVIEW_DASHBOARD' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_QUARTERLY_PHARMACY_KPIS' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_QUARTERLY_RISK_FLAGS' FROM dual UNION ALL
    SELECT 'VIEW', 'GOLD_QUARTERLY_TRENDS' FROM dual
),
object_metadata AS (
    SELECT object_name, object_type,
           DBMS_METADATA.GET_DDL(object_type, object_name, USER) AS ddl
    FROM object_names
),
chunk_numbers AS (
    SELECT LEVEL AS part_number
    FROM dual
    CONNECT BY LEVEL <= (
        SELECT MAX(CEIL(DBMS_LOB.GETLENGTH(ddl) / 1000))
        FROM object_metadata
    )
)
SELECT m.object_name,
       m.object_type,
       n.part_number,
       CEIL(DBMS_LOB.GETLENGTH(m.ddl) / 1000) AS part_count,
       DBMS_LOB.GETLENGTH(m.ddl) AS ddl_length,
       DBMS_LOB.SUBSTR(m.ddl, 1000, (n.part_number - 1) * 1000 + 1) AS ddl_part
FROM object_metadata m
CROSS JOIN chunk_numbers n
WHERE (n.part_number - 1) * 1000 < DBMS_LOB.GETLENGTH(m.ddl)
ORDER BY m.object_type, m.object_name, n.part_number;
