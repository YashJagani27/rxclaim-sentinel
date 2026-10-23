-- Read-only discovery. Run as the schema owner in Oracle Database Actions.
-- Export EACH result separately as CSV. Do not publish private schema metadata
-- without review. These SELECT statements do not create or modify objects.

-- 1. Inventory relevant tables, views, materialized views and program units.
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name LIKE '%MEDICAID%'
   OR object_name LIKE '%NADAC%'
   OR object_name LIKE 'GOLD\_%' ESCAPE '\'
   OR object_name LIKE '%TABLEAU%'
ORDER BY object_type, object_name;

-- 2. All dependencies in the owning schema, including objects whose names
-- do not match the filters above. This supports transitive dependency review.
SELECT name, type, referenced_owner, referenced_name, referenced_type,
       referenced_link_name
FROM user_dependencies
ORDER BY name, type, referenced_owner, referenced_name;

-- 3. Column types and precision; needed for loading and CSV export contracts.
SELECT table_name, column_id, column_name, data_type, data_length,
       data_precision, data_scale, nullable
FROM user_tab_columns
WHERE table_name LIKE '%MEDICAID%'
   OR table_name LIKE '%NADAC%'
   OR table_name LIKE 'GOLD\_%' ESCAPE '\'
   OR table_name LIKE '%TABLEAU%'
ORDER BY table_name, column_id;

-- 4. Existing constraints. Do not infer a source-record key from column names.
SELECT c.table_name, c.constraint_name, c.constraint_type, c.status,
       c.validated, cc.position, cc.column_name
FROM user_constraints c
LEFT JOIN user_cons_columns cc
  ON cc.constraint_name = c.constraint_name AND cc.table_name = c.table_name
ORDER BY c.table_name, c.constraint_name, cc.position;

-- 5. Compilation errors, including invalid FORCE-created views.
SELECT name, type, sequence, line, position, text
FROM user_errors
ORDER BY name, type, sequence;
