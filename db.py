"""
db.py — Capa de acceso a datos (solo lectura)
Gestiona la conexión a SQL Server mediante pyodbc.
Todas las operaciones son SELECT sobre el catálogo sys.* del D/D.
"""

import pyodbc
from config import SERVER, DATABASE, USERNAME, PASSWORD, DRIVER


# Cadena de conexión
def _conn_string() -> str:
    return (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=10;"
    )


def get_connection():
    """Retorna una conexión activa a SQL Server."""
    return pyodbc.connect(_conn_string())


def test_connection() -> tuple:
    """
    Verifica la conexión a la BD.
    Retorna (True, version_string) si conecta, (False, error_msg) si falla.
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT @@VERSION")
        ver = cur.fetchone()[0].split("\n")[0].strip()
        conn.close()
        return True, ver
    except Exception as exc:
        return False, str(exc)


def execute_query(sql: str, params: tuple = ()) -> tuple:
    """
    Ejecuta una consulta SELECT y retorna (columnas, filas).
      columnas : list[str]   — nombres de columna del resultado.
      filas    : list[list]  — filas como listas de valores.
    Lanza Exception si la consulta falla.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params) if params else cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows    = [list(row) for row in cur.fetchall()]
        return columns, rows
    finally:
        conn.close()
