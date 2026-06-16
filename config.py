"""
StreamUCV — Data Dictionary Interrogator
Proyecto #1  |  Administración de Bases de Datos  |  UCV  |  Semestre 1-2026

ARCHIVO DE CONFIGURACIÓN — MODIFICAR ANTES DE EJECUTAR EN SU INSTANCIA LOCAL.

Instrucciones:
  1. Cambie SERVER   → nombre del servidor o IP donde corre SQL Server.
    Ejemplos: "localhost", "192.168.1.10", "MiPC\\SQLEXPRESS"
  2. Cambie USERNAME → login SQL Server con permisos de lectura sobre StreamUCV.
  3. Cambie PASSWORD → contraseña del login anterior.
  4. Cambie DRIVER   → nombre exacto de
       → Orígel driver ODBC instalado en su máquina.
  Verificar en: Panel de control → Herramientas administrativasnes de datos ODBC → pestaña Controladores

Las variables DATABASE y SCHEMA corresponden al ambiente oficial del proyecto
y NO deben modificarse.
"""

# Credenciales de conexión SQL Server
SERVER   = "localhost"                    # Servidor o IP
DATABASE = "StreamUCV"                   # Base de datos oficial — no modificar
USERNAME = "sa"                          # Login SQL Server
PASSWORD = "tu_password"                 # Contraseña
DRIVER   = "ODBC Driver 17 for SQL Server"   # Driver ODBC instalado
SCHEMA   = "streaming"                   # Esquema oficial — no modificar

# Parámetros físicos (supuestos del proyecto)
PAGE_SIZE_BYTES    = 8192   # Tamaño de página SQL Server = 8 KB
TRANSFER_RATE_MBS  = 17     # Velocidad de transferencia = 17 MB/s (supuesto)
BTREE_HEIGHT       = 4      # Accesos estimados con índice B-Tree:
                            #   ~3 niveles de árbol + 1 acceso a la página de datos
MAX_COL_ESTIMATE   = 8000   # Estimado en bytes para columnas de tipo MAX (varchar(max))
