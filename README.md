# 🎬 StreamUCV — Data Dictionary Interrogator

> [!NOTE] 
> **Proyecto #1 · Administración de Bases de Datos · UCV · Escuela de Computación · Semestre 1-2026**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-CC2927?style=flat-square&logo=microsoftsqlserver&logoColor=white)
![tkinter](https://img.shields.io/badge/UI-tkinter-FFD43B?style=flat-square&logo=python&logoColor=black)
![pyodbc](https://img.shields.io/badge/Conexión-pyodbc-0078D4?style=flat-square)
![License](https://img.shields.io/badge/Uso-Académico-22C55E?style=flat-square)

---

## 📌 Descripción

**StreamUCV Data Dictionary Interrogator** es una aplicación de escritorio en Python que interroga automáticamente el **Diccionario de Datos (catálogo del sistema)** de SQL Server para la base de datos `StreamUCV`, esquema `streaming`.

En lugar de que los analistas escriban consultas SQL manualmente, la aplicación expone **10 reportes técnicos** sobre la estructura interna de la BD —tablas, índices, restricciones, triggers, tamaños físicos y estimaciones de costo— todos extraídos en tiempo real desde las vistas de catálogo `sys.*` de SQL Server.

> [!CAUTION]
> *"El Diccionario de Datos no describe series ni actores: describe las propias tablas, columnas e índices. Es la BD dentro de la BD."*

---

## 🖥️ Vista previa de la interfaz 

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  StreamUCV  —  Data Dictionary Interrogator    BD: StreamUCV | streaming    │
├──────────────────┬──────────────────────────────────────────────────────────┤
│  REPORTES        │  Requerimiento 9  —  Factor de Bloqueo                   │
│------------------│  Calcula fb = ⌊8192/tr⌋ y bloques estimados por tabla.    │
│  📋 Req 1 & 2    │                                                          │
│  🔐 Req 3        │   13 Tablas   fb Mín: 4   fb Máx: 40   fb Prom: 12.3     │
│  📊 Req 4        │                                                          │
│  ⚡ Req 5        │  Fórmulas aplicadas:                                     │
│  💾 Req 6        │  tr  =  Σ max_length de todas las columnas (bytes)       │
│  📏 Req 7 & 8    │  fb  =  ⌊ 8.192 / tr ⌋                                    │
│  🧮 Req 9   ◄    │  Bloques est. = ⌈ N° registros / fb ⌉                     │
│  ⚙  Req 10       │                                                          │
│------------------│  Tabla        N°Cols  tr(B/Reg)  fb   Regs   Bloques      │
│   Reconectar     │  artista         4      1114      7    200      29        │
│                  │  cadena          4      1070      7    120      17        │
│                  │  horario         4       202     40     80       2        │
│                  │  interpreta      7      1724      4    450     113        │
│                  │  ...                                                      │
│                  │  [📥 Exportar CSV]  [🔄 Actualizar]                      │
├──────────────────┴──────────────────────────────────────────────────────────┤
│  ✅ Conectado — localhost       Req 9: 13 tablas — Factor de bloqueo calc.  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estructura del proyecto

```
StreamUCV_DD/
│
├── config.py               ★ ÚNICO archivo a modificar para cada entorno
├── db.py                   Capa de acceso a datos — conexión pyodbc
├── queries.py              13 consultas T-SQL al catálogo sys.* (solo lectura)
├── streamucv_eer.mmd       ← Diagrama EER en Mermaid (Diagram as Code)
├── streamucv_app.py        Aplicación completa tkinter (831 líneas)
├── requirements.txt        Dependencia: pyodbc
├── README.md               Este archivo
│
└── docs/
└── sql/
    ├── create_repositorio_sqlserver.sql   Crea BD StreamUCV + esquema streaming
    ├── create_tables_sqlserver.sql        13 tablas, PK, FK, CHECK, índices
    └── insert_tables_sqlserver.sql        Datos de prueba (series, actores, etc.)
```

### Responsabilidad de cada módulo

| Archivo | Rol | Patrón |
|---|---|---|
| `config.py` | Única fuente de verdad para credenciales y parámetros físicos | Configuration Object |
| `db.py` | Abstrae `pyodbc`: `get_connection()`, `execute_query()`, `test_connection()` | Gateway |
| `queries.py` | Constantes T-SQL nombradas por requerimiento (`SQL_REQ1_2`, `SQL_REQ9`…) | Query Object |
| `streamucv_app.py` | UI tkinter: sidebar, Treeview, tarjetas de resumen, formulario Req 10 | MVC |

---

## ⚙ Requisitos del entorno

| Componente | Versión mínima | Notas |
|---|---|---|
| **Python** | 3.10 | Incluye tkinter en la instalación estándar |
| **SQL Server** | 2017 | `STRING_AGG` disponible desde 2017; `WITHIN GROUP` desde 2022 |
| **ODBC Driver** | 17 for SQL Server | Descargar desde Microsoft si no está instalado |
| **pyodbc** | 4.0.39 | Única dependencia externa |
| **Sistema operativo** | Windows 10 / 11 | tkinter incluido; en Linux instalar `python3-tk` |
> [!WARNING]  
> **Verificar driver ODBC instalado** → Panel de control → Herramientas administrativas → Orígenes de datos ODBC → pestaña *Controladores*.

---

## Instalación y ejecución

### Paso 1 — Preparar la base de datos

Ejecutar los tres scripts SQL desde **SSMS** o `sqlcmd`, **en este orden exacto**:

```sql
-- 1. Crea la base de datos StreamUCV y el esquema streaming
:r sql\create_repositorio_sqlserver.sql

-- 2. Crea las 13 tablas con restricciones e índices
:r sql\create_tables_sqlserver.sql

-- 3. Carga los datos de prueba del sistema audiovisual
:r sql\insert_tables_sqlserver.sql
```

Alternativamente desde terminal con `sqlcmd`:

```bash
sqlcmd -S localhost -U sa -P tu_password -i sql/create_repositorio_sqlserver.sql
sqlcmd -S localhost -U sa -P tu_password -d StreamUCV -i sql/create_tables_sqlserver.sql
sqlcmd -S localhost -U sa -P tu_password -d StreamUCV -i sql/insert_tables_sqlserver.sql
```

### Paso 2 — Configurar la conexión

Abrir `config.py` y ajustar las variables:

```python
# ── config.py — MODIFICAR ESTOS VALORES ───────────────────────────────
SERVER   = "localhost"                     # Servidor o IP de SQL Server
DATABASE = "StreamUCV"                    # No modificar
USERNAME = "sa"                           # Login con acceso a StreamUCV
PASSWORD = "tu_password"                  # Contraseña del login
DRIVER   = "ODBC Driver 17 for SQL Server"   # Nombre exacto del driver ODBC
SCHEMA   = "streaming"                    # No modificar
```

### Paso 3 — Instalar dependencia

```bash
pip install -r requirements.txt
```

### Paso 4 — Ejecutar

```bash
python streamucv_app.py
```

---

## Requerimientos funcionales implementados

Cada reporte se activa con un clic en el menú lateral. **No se escribe SQL manualmente.**

| Req | Nombre | Vistas `sys.*` consultadas | Qué muestra |
|---|---|---|---|
| **1 & 2** | Tablas e Índices | `sys.tables` `sys.indexes` `sys.schemas` | Nombre de tabla, fecha creación/modificación, cantidad de índices y sus nombres |
| **3** | Restricciones | `sys.objects` `sys.tables` | Nombre, tabla y tipo legible: PK, FK, CHECK, UNIQUE |
| **4** | Detalle de Índices | `sys.indexes` `sys.index_columns` `sys.columns` | Tabla, tipo, unicidad, si es PK, fill factor y columnas clave en orden |
| **5** | Triggers | `sys.triggers` `sys.tables` | Nombre, tipo, estado (Habilitado/Deshabilitado) y tabla que lo activa |
| **6** | Tamaño de Tablas | `sys.dm_db_partition_stats` | Páginas reservadas, tamaño en KB y MB, número de registros |
| **7 & 8** | Registros y Columnas | `sys.columns` `sys.types` | `max_length` por columna en bytes + tamaño estimado del registro `tr` |
| **9** | Factor de Bloqueo | `sys.columns` + `sys.dm_db_partition_stats` (CTE) | `tr`, `fb`, registros reales, bloques estimados |
| **10** | Estimador de Costos | `sys.index_columns` `sys.dm_db_partition_stats` | Formulario interactivo: tabla y columna → accesos a disco y tiempo en segundos |

---

## 📋 Arquitectura del Diccionario de Datos en SQL Server

El **Diccionario de Datos** (D/D) de SQL Server es un conjunto de vistas de sistema accesibles mediante SQL estándar. La aplicación lo consulta exclusivamente en modo lectura:

```
  Aplicación Python (pyodbc)
         │
         ▼  SELECT (solo lectura)
  ┌──────────────────────────────────────────────────────┐
  │          CATÁLOGO DEL SISTEMA — sys.*                │
  │                                                      │
  │  sys.tables          → tablas del usuario            │
  │  sys.schemas         → esquemas (streaming)          │
  │  sys.columns         → columnas y sus tipos          │
  │  sys.types           → tipos de dato nativos         │
  │  sys.indexes         → índices definidos             │
  │  sys.index_columns   → columnas de cada índice       │
  │  sys.objects         → objetos: PK, FK, CHECK, UQ    │
  │  sys.triggers        → triggers DML                  │
  │  sys.dm_db_          → vista de gestión dinámica:    │
  │    partition_stats   → páginas y registros reales    │
  └──────────────────────────────────────────────────────┘
         │
         ▼  Resultados → Treeview / tarjetas / CSV
  Interfaz tkinter (sin que el usuario escriba SQL)
```
> [!IMPORTANT] 
> A diferencia de los datos de negocio (series, actores, cadenas), el catálogo almacena **metadatos**: definiciones de tablas, tipos de columnas, ubicación física, estadísticas de almacenamiento. Consultar el D/D es la base del trabajo del DBA.

---

## Formulas aplicadas — supuestos y fórmulas

### Tamaño estimado del registro (`tr`)

```
tr = Σ  max_length(columnaᵢ)   para i = 1..N columnas de la tabla
```

`sys.columns.max_length` retorna el tamaño máximo en **bytes** según el tipo:

| Tipo SQL Server | `max_length` | Notas |
|---|---|---|
| `varchar(n)` | `n` bytes | 1 byte por carácter |
| `nvarchar(n)` | `n × 2` bytes | UTF-16, 2 bytes por carácter |
| `int` | 4 bytes | Fijo |
| `decimal(p, s)` | 5 – 17 bytes | Depende de la precisión `p` |
| `date` | 3 bytes | Fijo |
| `time(0)` | 3 bytes | Fijo |
| `varchar(max)` | −1 → estimado **8 000 B** | Sin límite definido |

**Supuesto**: se usa el máximo posible por columna (longitud fija), sin overhead de cabecera de página.

### Factor de bloqueo (`fb`)

```
fb = ⌊ 8 192 / tr ⌋
```

- `8 192` bytes = tamaño de página de datos SQL Server (8 KB).
- División entera (floor): un registro **no puede partirse** entre dos páginas.

### Bloques estimados para almacenar todos los registros

```
Bloques estimados = ⌈ N° registros / fb ⌉
```

### Estimador de costos de consulta de igualdad (Req 10)

**Caso A — La columna es clave líder de un índice** (`key_ordinal = 1` en `sys.index_columns`):

```
Estrategia  : Index Seek (B-Tree)
Accesos     : 4   ≈ 3 niveles de árbol + 1 página de datos
Bytes leídos: 4 × 8 192 = 32 768 bytes
Tiempo (s)  : 32 768 / (17 × 1 048 576) ≈ 0.001843 s
```

**Caso B — Sin índice en la columna:**

```
Estrategia  : Full Table Scan
Accesos     : reserved_page_count  (todas las páginas de la tabla)
Bytes leídos: páginas × 8 192 bytes
Tiempo (s)  : (páginas × 8 192) / (17 × 1 048 576)
```

Tasa de transferencia: **17 MB/s** = 17 × 1 024 × 1 024 = **17 825 792 bytes/s**.

---

## 🗃️ Esquema de la base de datos StreamUCV

![STREAMUCV - Diagrama Entidad Relación Extendido (ER-E) V2](docs/STREAMUCV - Diagrama Entidad Relación Extendido (ER-E) V2.png)
```
cadena ─────────────── lanzar ───────────── serie ─────────────┐
          └──────────── venta ─────────────────────────────────┤
                                                               ├── interpreta ── personaje
artista ───────────────────────────────────────────────────────┤
          └──────────── participa ── pelicula ── involucrada ── semana
horario ─────────────── transmite ── serie
```

| Tabla | Descripción | Clave primaria |
|---|---|---|
| `serie` | Series de TV con tipo y rating | `cod_serie` |
| `cadena` | Cadenas televisivas y de streaming | `cod_cadena` |
| `artista` | Actores y sus datos personales | `cod_artista` |
| `personaje` | Personajes ficticios de las series | `cod_personaje` |
| `pelicula` | Películas del catálogo | `cod_pelicula` |
| `semana` | Semanas de programación | `(numero_semana, mes, anio)` |
| `horario` | Franjas horarias de transmisión | `cod_horario` |
| `lanzar` | Relación cadena ↔ serie con fecha de lanzamiento | `(cod_cadena, cod_serie, fecha_lanzamiento)` |
| `venta` | Ventas de derechos entre cadenas | `(serie, vendedora, compradora, fecha_venta)` |
| `interpreta` | Artista interpreta personaje en serie | `(serie, personaje, artista, fecha)` |
| `participa` | Artista en película | `(cod_pelicula, cod_artista)` |
| `transmite` | Serie en horario con sustituta | `(horario, serie, sustituta)` |
| `involucrada` | Película asociada a una semana | `(semana, mes, anio, pelicula)` |

---

## 💡 Funcionalidades de la interfaz

- **Menú lateral** con los 10 reportes, resaltado activo e indicador hover.
- **Tarjetas de resumen** en la parte superior de cada reporte (totales, promedios, extremos).
- **Treeview** con filas de colores alternados, scroll horizontal y vertical, columnas redimensionables.
- **Formulario interactivo** en Req 10: dropdowns dinámicos tabla → columna, con cálculo detallado paso a paso.
- **Exportar CSV** en cada reporte (UTF-8 con BOM, compatible con Excel en español).
- **Botón Reconectar** para cambiar de instancia SQL Server sin reiniciar la aplicación.
- **Barra de estado** con indicador de conexión en tiempo real (verde/naranja/rojo) y timestamp.
- **Panel de error** descriptivo si la BD no responde — sin crasheos silenciosos.

---

## Restricciones del proyecto cumplidas

- [X] Operaciones **exclusivamente de lectura** (`SELECT`) sobre el catálogo `sys.*`
- [X] Las tablas, columnas, restricciones, índices y datos de `StreamUCV` **no se modifican**
- [X] No se crean vistas auxiliares ni procedimientos almacenados en la BD
- [X] Toda la lógica analítica (cálculo de `tr`, `fb`, costos) vive en la **capa Python**
- [X] Los datos de conexión están centralizados en un único archivo (`config.py`)
- [X] La aplicación puede adaptarse a cualquier instancia local modificando solo `config.py`

---

## Resolución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `[IM002] Data source not found` | Driver ODBC no instalado o nombre incorrecto | Descargar *ODBC Driver 17 for SQL Server* de Microsoft; actualizar `DRIVER` en `config.py` |
| `Login failed for user 'sa'` | Credenciales incorrectas o autenticación Windows | Verificar que SQL Server use *SQL Server Authentication* y que `sa` esté habilitado en SSMS |
| `Cannot open database "StreamUCV"` | BD no creada o sin permiso de acceso | Ejecutar los 3 scripts en orden; otorgar permisos con `GRANT CONNECT TO <usuario>` |
| `STRING_AGG WITHIN GROUP` error | SQL Server < 2022 | Usar `STRING_AGG(c.name, ', ')` sin `WITHIN GROUP` en el Req 4 de `queries.py` |
| Treeview vacío, sin error | Esquema `streaming` no encontrado | Verificar que `create_repositorio` y `create_tables` se ejecutaron correctamente |
| Ventana no abre en Linux | tkinter no instalado | `sudo apt install python3-tk` |

---

## 📁 Formato de entrega

Descargado desde Github y Comprimido el directorio como `.zip`:

```
<NombreApellido1>_<NombreApellido2>_<NombreApellido3>.zip
```

Contenido mínimo requerido y cumplido:
- `config.py`, `db.py`, `queries.py`, `streamucv_app.py`
- `requirements.txt`
- Documentación (este `README.md`, PDF en /docs)
- Scripts SQL en `sql/`


---

## 👥 Integrantes / Devs

| Rol | Nombre | Carnet |
|---|---|---|
| Propietario del Repo. y Lead Developer | Mateo González | V 29900089 |
| Desarrollador, QA y Documentación PDF | Samuel Flores  | V 30416486 |

---

## 📄 Licencia

Uso académico exclusivo — **Administración de Bases de Datos · UCV · 2026**

---

<p align="center">
  <em>Universidad Central de Venezuela · Facultad de Ciencias </em><br/>
  <em> Dra. Concettina Di Vasta y MSc. Christian Lechiguero · Escuela de Computación </em><br/>
  <em>Administración de Bases de Datos — Semestre 1-2026 — Aux. Doc. J. Rojas & M. Barboza</em>
</p>
