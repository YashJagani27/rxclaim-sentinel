-- RxClaim Sentinel: export the actual DDL of the nine existing Oracle views.
-- Run in Oracle Database Actions > SQL while connected as the owning user.
-- Download the results as CSV, keeping all rows and all five columns.
-- Each row includes a 1000-character chunk to avoid CLOB export truncation.
-- DDL_LENGTH lets the import script check that no text was lost.
-- Increase the 200 limit below if any view exceeds 200,000 characters.

WITH view_names (sort_order, layer_name, view_name) AS (
    SELECT 1, 'bronze', 'RAW_MEDICAID_2025' FROM dual UNION ALL
    SELECT 2, 'silver', 'CLEAN_MEDICAID_2025' FROM dual UNION ALL
    SELECT 3, 'gold', 'GOLD_QUARTERLY_PHARMACY_KPIS' FROM dual UNION ALL
    SELECT 4, 'gold', 'GOLD_QUARTERLY_TRENDS' FROM dual UNION ALL
    SELECT 5, 'gold', 'GOLD_QUARTERLY_RISK_FLAGS' FROM dual UNION ALL
    SELECT 6, 'gold', 'GOLD_NDC_QUARTERLY' FROM dual UNION ALL
    SELECT 7, 'gold', 'GOLD_NDC_QOQ_ANALYSIS' FROM dual UNION ALL
    SELECT 8, 'gold', 'GOLD_NDC_INVESTIGATION_QUEUE' FROM dual UNION ALL
    SELECT 9, 'gold', 'GOLD_NDC_REVIEW_DASHBOARD' FROM dual
),
view_metadata AS (
    SELECT sort_order,
           layer_name,
           view_name,
           DBMS_METADATA.GET_DDL('VIEW', view_name, USER) AS ddl
    FROM view_names
),
chunk_numbers AS (
    SELECT LEVEL AS part_number
    FROM dual
    CONNECT BY LEVEL <= 200
)
SELECT v.view_name AS view_name,
       v.layer_name AS layer_name,
       n.part_number AS part_number,
       DBMS_LOB.GETLENGTH(v.ddl) AS ddl_length,
       DBMS_LOB.SUBSTR(v.ddl, 1000, (n.part_number - 1) * 1000 + 1) AS ddl_part
FROM view_metadata v
CROSS JOIN chunk_numbers n
WHERE (n.part_number - 1) * 1000 < DBMS_LOB.GETLENGTH(v.ddl)
ORDER BY v.sort_order, n.part_number;
