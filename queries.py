"""
queries.py — Consultas T-SQL al Diccionario de Datos de SQL Server
Fuente: vistas de catálogo sys.* e INFORMATION_SCHEMA
Todas las consultas son estrictamente de SOLO LECTURA (SELECT).
Compatibilidad: SQL Server 2017+ (STRING_AGG); STRING_AGG con WITHIN GROUP: SQL Server 2022+
"""

# REQ 1 & 2 — Tablas e índices del esquema
# Lista cada tabla con su fecha de creación/modificación y la cantidad de índices
# (type > 0 excluye el heap "índice 0" que no es un índice real).
SQL_REQ1_2 = """
SELECT
    t.name                                   AS [Tabla],
    CONVERT(VARCHAR(19), t.create_date, 120) AS [Creada],
    CONVERT(VARCHAR(19), t.modify_date, 120) AS [Modificada],
    COUNT(i.index_id)                        AS [N° Índices],
    ISNULL(STRING_AGG(i.name, '  |  '), '(ninguno)')
                                             AS [Índices Definidos]
FROM sys.tables  t
JOIN sys.schemas s  ON t.schema_id = s.schema_id
LEFT JOIN sys.indexes i
       ON t.object_id = i.object_id
      AND i.type > 0
WHERE s.name = ?
GROUP BY t.name, t.create_date, t.modify_date
ORDER BY t.name;
"""

SQL_TOTAL_TABLES = """
SELECT COUNT(*) FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = ?;
"""

SQL_TOTAL_INDEXES = """
SELECT COUNT(*) FROM sys.indexes i
JOIN sys.tables  t ON i.object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = ? AND i.type > 0;
"""

# REQ 3 — Restricciones
# Consulta sys.objects para PK, FK, CHECK y UNIQUE con su tabla y tipo legible.
SQL_REQ3 = """
SELECT
    obj.name  AS [Restricción],
    tab.name  AS [Tabla],
    CASE obj.type
        WHEN 'PK' THEN 'Clave Primaria  (PK)'
        WHEN 'F'  THEN 'Clave Foránea   (FK)'
        WHEN 'C'  THEN 'CHECK'
        WHEN 'UQ' THEN 'UNIQUE'
        ELSE obj.type_desc
    END       AS [Tipo]
FROM sys.objects obj
JOIN sys.tables  tab ON obj.parent_object_id = tab.object_id
JOIN sys.schemas sch ON tab.schema_id        = sch.schema_id
WHERE sch.name = ?
  AND obj.type IN ('C','F','PK','UQ')
ORDER BY tab.name, obj.type, obj.name;
"""

# REQ 4 — Detalle de índices
# Para cada índice: tabla, tipo, si es único, si es PK, fill factor y columnas clave.
# STRING_AGG WITHIN GROUP ordena las columnas por su posición en el índice (key_ordinal).
SQL_REQ4 = """
SELECT
    t.name         AS [Tabla],
    i.name         AS [Índice],
    i.type_desc    AS [Tipo],
    CASE WHEN i.is_unique      = 1 THEN 'Sí' ELSE 'No' END AS [Único],
    CASE WHEN i.is_primary_key = 1 THEN 'Sí' ELSE 'No' END AS [Es PK],
    CASE WHEN i.fill_factor = 0
         THEN '100 % (default)'
         ELSE CAST(i.fill_factor AS VARCHAR(3)) + ' %'
    END            AS [Fill Factor],
    STRING_AGG(c.name, ', ')
        WITHIN GROUP (ORDER BY ic.key_ordinal)
                   AS [Columnas Clave]
FROM sys.indexes       i
JOIN sys.tables        t  ON i.object_id  = t.object_id
JOIN sys.schemas       s  ON t.schema_id  = s.schema_id
JOIN sys.index_columns ic ON i.object_id  = ic.object_id
                          AND i.index_id   = ic.index_id
JOIN sys.columns       c  ON ic.object_id = c.object_id
                          AND ic.column_id = c.column_id
WHERE s.name = ?
  AND i.type > 0
  AND ic.is_included_column = 0
GROUP BY t.name, i.name, i.type_desc, i.is_unique, i.is_primary_key, i.fill_factor
ORDER BY t.name, i.name;
"""

# REQ 5 — Triggers 
# Nombre, tipo, estado (habilitado/deshabilitado) y tabla asociada.
SQL_REQ5 = """
SELECT
    tr.name      AS [Trigger],
    tr.type_desc AS [Tipo],
    CASE WHEN tr.is_disabled = 1
         THEN 'Deshabilitado' ELSE 'Habilitado'
    END          AS [Estado],
    tab.name     AS [Tabla]
FROM sys.triggers tr
JOIN sys.tables   tab ON tr.parent_id   = tab.object_id
JOIN sys.schemas  s   ON tab.schema_id  = s.schema_id
WHERE s.name = ?
ORDER BY tab.name, tr.name;
"""

# REQ 6 — Tamaño de tablas
# sys.dm_db_partition_stats acumula páginas reservadas por partición/índice.
# Multiplicar por 8 da KB (cada página = 8 KB).
SQL_REQ6 = """
SELECT
    t.name                                           AS [Tabla],
    SUM(p.reserved_page_count)                       AS [Páginas Reservadas],
    SUM(p.reserved_page_count) * 8                   AS [Tamaño (KB)],
    CAST(SUM(p.reserved_page_count)*8.0/1024.0
         AS DECIMAL(10,3))                           AS [Tamaño (MB)],
    SUM(p.row_count)                                 AS [N° Registros]
FROM sys.dm_db_partition_stats p
JOIN sys.tables  t ON p.object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = ?
GROUP BY t.name
ORDER BY [Tamaño (KB)] DESC;
"""

# REQ 7 & 8 — Columnas: tipo y tamaño en bytes
# sys.columns.max_length retorna bytes para tipos de ancho fijo y variable.
# Para tipos MAX (varchar(max), etc.) max_length = -1; usamos estimado de 8000 bytes.
SQL_REQ7_8 = """
SELECT
    t.name     AS [Tabla],
    c.column_id AS [Pos],
    c.name     AS [Columna],
    tp.name    AS [Tipo de Dato],
    CASE WHEN c.max_length = -1 THEN 8000
         ELSE c.max_length
    END        AS [Tamaño Máx (Bytes)],
    CASE WHEN c.is_nullable = 1 THEN 'Sí' ELSE 'No' END AS [Nulable],
    CASE WHEN c.is_identity  = 1 THEN 'IDENTITY'
         WHEN c.is_computed  = 1 THEN 'COMPUTED'
         ELSE ''
    END        AS [Extra]
FROM sys.columns c
JOIN sys.tables  t  ON c.object_id    = t.object_id
JOIN sys.schemas s  ON t.schema_id    = s.schema_id
JOIN sys.types   tp ON c.user_type_id = tp.user_type_id
WHERE s.name = ?
ORDER BY t.name, c.column_id;
"""

# REQ 9 — Factor de bloqueo 
# tr  = suma de max_length de todas las columnas de la tabla (tamaño estimado del registro).
# fb  = FLOOR(8192 / tr)  — la división entera en T-SQL trunca hacia cero (= floor para positivos).
# Bloques estimados = CEILING(N° registros / fb).
# Se usa CTE para separar cálculo de columnas y estadísticas de partición.
SQL_REQ9 = """
WITH col_sizes AS (
    SELECT
        t.name        AS tabla_name,
        t.object_id,
        COUNT(c.column_id) AS num_cols,
        SUM(CASE WHEN c.max_length = -1 THEN 8000
                 ELSE c.max_length END) AS tr_bytes
    FROM sys.columns c
    JOIN sys.tables  t  ON c.object_id    = t.object_id
    JOIN sys.schemas s  ON t.schema_id    = s.schema_id
    WHERE s.name = ?
    GROUP BY t.name, t.object_id
),
part_stats AS (
    SELECT
        p.object_id,
        SUM(p.row_count)           AS rows_total,
        SUM(p.reserved_page_count) AS pages_total
    FROM sys.dm_db_partition_stats p
    WHERE p.index_id IN (0, 1)    -- heap (0) o índice clustered (1)
    GROUP BY p.object_id
)
SELECT
    cs.tabla_name                                  AS [Tabla],
    cs.num_cols                                    AS [N° Cols],
    cs.tr_bytes                                    AS [tr (Bytes/Reg)],
    8192 / cs.tr_bytes                             AS [Factor Bloqueo (fb)],
    ISNULL(ps.rows_total,  0)                      AS [N° Registros],
    ISNULL(ps.pages_total, 0)                      AS [Páginas Reales],
    CEILING(
        CAST(ISNULL(ps.rows_total, 0) AS FLOAT)
        / NULLIF(8192 / cs.tr_bytes, 0)
    )                                              AS [Bloques Estimados]
FROM col_sizes cs
LEFT JOIN part_stats ps ON cs.object_id = ps.object_id
ORDER BY cs.tabla_name;
"""

# REQ 10 — Dropdown: tablas disponibles
SQL_GET_TABLES = """
SELECT t.name
FROM sys.tables  t
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = ?
ORDER BY t.name;
"""

# REQ 10 — Dropdown: columnas de una tabla
SQL_GET_COLUMNS = """
SELECT c.name, tp.name AS tipo,
       CASE WHEN c.max_length = -1 THEN 8000 ELSE c.max_length END AS tam
FROM sys.columns c
JOIN sys.tables  t  ON c.object_id    = t.object_id
JOIN sys.schemas s  ON t.schema_id    = s.schema_id
JOIN sys.types   tp ON c.user_type_id = tp.user_type_id
WHERE s.name = ? AND t.name = ?
ORDER BY c.column_id;
"""

# REQ 10 — ¿La columna es clave líder de algún índice?
# key_ordinal = 1 significa que la columna ocupa la primera posición del índice,
# lo que la hace apta para consultas de igualdad eficientes (index seek).
SQL_REQ10_INDEX = """
SELECT TOP 1
    i.name       AS indice,
    i.type_desc  AS tipo_indice,
    i.is_unique  AS es_unico
FROM sys.index_columns ic
JOIN sys.indexes  i  ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns  c  ON ic.object_id = c.object_id AND ic.column_id = c.column_id
JOIN sys.tables   t  ON i.object_id  = t.object_id
JOIN sys.schemas  s  ON t.schema_id  = s.schema_id
WHERE s.name = ? AND t.name = ? AND c.name = ?
  AND ic.key_ordinal = 1
  AND i.type > 0;
"""

# REQ 10 — Páginas y registros de una tabla
SQL_REQ10_PAGES = """
SELECT
    SUM(p.reserved_page_count) AS paginas,
    SUM(p.row_count)           AS registros
FROM sys.dm_db_partition_stats p
JOIN sys.tables  t ON p.object_id = t.object_id
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = ? AND t.name = ?;
"""
