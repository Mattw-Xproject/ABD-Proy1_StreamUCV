"""
streamucv_app.py — Aplicación principal
StreamUCV Data Dictionary Interrogator
Proyecto #1  |  Administración de Bases de Datos  |  UCV  |  Semestre 1-2026

Dependencias:  pip install pyodbc
Ejecución:     python streamucv_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
import math

from config import (
    SERVER, DATABASE, SCHEMA,
    PAGE_SIZE_BYTES, TRANSFER_RATE_MBS, BTREE_HEIGHT,
)
from db import execute_query, test_connection
from queries import (
    SQL_REQ1_2, SQL_TOTAL_TABLES, SQL_TOTAL_INDEXES,
    SQL_REQ3, SQL_REQ4, SQL_REQ5, SQL_REQ6,
    SQL_REQ7_8, SQL_REQ9,
    SQL_GET_TABLES, SQL_GET_COLUMNS,
    SQL_REQ10_INDEX, SQL_REQ10_PAGES,
)

# ══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES
# ══════════════════════════════════════════════════════════════════════════════
BG_ROOT    = "#0D1117"
BG_SIDE    = "#161B22"
BG_CARD    = "#21262D"
BG_HEAD    = "#010409"
FG_WHITE   = "#E6EDF3"
FG_GRAY    = "#8B949E"
FG_BLUE    = "#58A6FF"
FG_GREEN   = "#3FB950"
FG_ORANGE  = "#E3B341"
FG_RED     = "#F85149"
BTN_NORM   = "#21262D"
BTN_HOVER  = "#30363D"
BTN_ACT    = "#1F6FEB"
TREE_ODD   = "#0D1117"
TREE_EVEN  = "#161B22"
TREE_SEL   = "#1F6FEB"
FONT_MAIN  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_H2    = ("Segoe UI", 11, "bold")
FONT_CODE  = ("Consolas", 9)

# ══════════════════════════════════════════════════════════════════════════════
# DEFINICIÓN DE REPORTES EN EL MENÚ LATERAL
# ══════════════════════════════════════════════════════════════════════════════
REPORTS = [
    ("1_2",  "📋  Req 1 & 2  —  Tablas e Índices"),
    ("3",    "🔐  Req 3      —  Restricciones"),
    ("4",    "🗂   Req 4      —  Detalle de Índices"),
    ("5",    "⚡  Req 5      —  Triggers"),
    ("6",    "💾  Req 6      —  Tamaño de Tablas"),
    ("7_8",  "📏  Req 7 & 8  —  Registros / Columnas"),
    ("9",    "🧮  Req 9      —  Factor de Bloqueo"),
    ("10",   "⚙   Req 10     —  Estimador de Costos"),
]

DESCRIPTIONS = {
    "1_2":  "Lista las tablas del esquema streaming, la cantidad de índices por tabla y los nombres de los índices definidos.",
    "3":    "Muestra todas las restricciones del esquema: Claves Primarias, Claves Foráneas, CHECK y UNIQUE, con su tabla y tipo.",
    "4":    "Para cada índice: tabla, tipo, unicidad, si es PK, fill factor y columnas clave en orden de posición.",
    "5":    "Triggers definidos en el esquema: nombre, tipo, estado (habilitado/deshabilitado) y tabla que los activa.",
    "6":    "Espacio ocupado por cada tabla usando sys.dm_db_partition_stats: páginas, KB, MB y número de registros.",
    "7_8":  "Tamaño en bytes de cada columna según su tipo de dato (sys.columns.max_length), y tamaño estimado del registro (tr).",
    "9":    "Factor de Bloqueo fb = ⌊8192 / tr⌋  y bloques estimados = ⌈N° registros / fb⌉. Supuesto: registros fijos.",
    "10":   "Dado una tabla y columna, estima el costo de una consulta de igualdad: accesos a disco y tiempo (17 MB/s).",
}


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class StreamUCVApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("StreamUCV — Data Dictionary Interrogator")
        self.root.geometry("1200x720")
        self.root.minsize(900, 580)
        self.root.configure(bg=BG_ROOT)

        # Estado interno
        self._active_btn  = None       # Botón sidebar activo
        self._active_key  = None       # Clave del reporte activo
        self._last_cols   = []         # Columnas del último resultado
        self._last_rows   = []         # Filas del último resultado
        self._req10_table_var  = tk.StringVar()
        self._req10_col_var    = tk.StringVar()

        self._setup_styles()
        self._build_ui()
        self._check_connection()

    # ── Estilos ttk ──────────────────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Treeview
        style.configure("DD.Treeview",
            background=TREE_ODD, foreground=FG_WHITE,
            fieldbackground=TREE_ODD, rowheight=24,
            font=FONT_SMALL, borderwidth=0)
        style.configure("DD.Treeview.Heading",
            background=BG_CARD, foreground=FG_BLUE,
            font=("Segoe UI", 9, "bold"), relief="flat",
            borderwidth=1)
        style.map("DD.Treeview",
            background=[("selected", TREE_SEL)],
            foreground=[("selected", FG_WHITE)])
        style.map("DD.Treeview.Heading",
            background=[("active", BTN_HOVER)])

        # Scrollbar
        style.configure("DD.Vertical.TScrollbar",
            troughcolor=BG_SIDE, background=BG_CARD,
            arrowcolor=FG_GRAY, borderwidth=0, relief="flat")
        style.configure("DD.Horizontal.TScrollbar",
            troughcolor=BG_SIDE, background=BG_CARD,
            arrowcolor=FG_GRAY, borderwidth=0, relief="flat")

        # Combobox (Req 10)
        style.configure("DD.TCombobox",
            fieldbackground=BG_CARD, background=BG_CARD,
            foreground=FG_WHITE, selectbackground=BTN_ACT,
            arrowcolor=FG_BLUE, font=FONT_MAIN)
        style.map("DD.TCombobox",
            fieldbackground=[("readonly", BG_CARD)],
            foreground=[("readonly", FG_WHITE)],
            selectbackground=[("readonly", BTN_ACT)])

        # Separator
        style.configure("DD.TSeparator", background=BG_CARD)

    # ── UI principal ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # ─ Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_HEAD, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎬", bg=BG_HEAD, fg=FG_BLUE,
                 font=("Segoe UI", 20)).pack(side="left", padx=(14, 4), pady=8)
        tk.Label(hdr, text="StreamUCV", bg=BG_HEAD, fg=FG_WHITE,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(hdr, text="  —  Data Dictionary Interrogator", bg=BG_HEAD,
                 fg=FG_GRAY, font=("Segoe UI", 11)).pack(side="left")
        tk.Label(hdr, text=f"BD: {DATABASE}  |  Esquema: {SCHEMA}",
                 bg=BG_HEAD, fg=FG_GRAY,
                 font=FONT_SMALL).pack(side="right", padx=12)
        self._conn_dot = tk.Label(hdr, text="●", bg=BG_HEAD,
                                  fg=FG_ORANGE, font=("Segoe UI", 12))
        self._conn_dot.pack(side="right", padx=(0, 2))
        self._conn_lbl = tk.Label(hdr, text="Conectando…", bg=BG_HEAD,
                                  fg=FG_ORANGE, font=FONT_SMALL)
        self._conn_lbl.pack(side="right", padx=(0, 4))

        # ─ Body (sidebar + main) ─────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG_ROOT)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main_area(body)

        # ─ Status bar ────────────────────────────────────────────────────────
        sb = tk.Frame(self.root, bg=BG_CARD, height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self._status_lbl = tk.Label(sb, text="Listo.", bg=BG_CARD,
                                    fg=FG_GRAY, font=FONT_SMALL, anchor="w")
        self._status_lbl.pack(side="left", padx=10)
        self._time_lbl = tk.Label(sb, text="", bg=BG_CARD,
                                  fg=FG_GRAY, font=FONT_SMALL, anchor="e")
        self._time_lbl.pack(side="right", padx=10)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG_SIDE, width=240)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, text="REPORTES", bg=BG_SIDE, fg=FG_GRAY,
                 font=("Segoe UI", 8, "bold"),
                 pady=10).pack(fill="x", padx=14, anchor="w")

        tk.Frame(side, bg=BTN_ACT, height=1).pack(fill="x", padx=14)

        self._sidebar_btns = {}
        for key, label in REPORTS:
            btn = tk.Button(
                side, text=label, anchor="w",
                bg=BTN_NORM, fg=FG_WHITE, activebackground=BTN_HOVER,
                activeforeground=FG_WHITE,
                font=FONT_SMALL, relief="flat", bd=0,
                padx=14, pady=8, cursor="hand2",
                command=lambda k=key: self._nav_click(k)
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: self._btn_hover(b, True))
            btn.bind("<Leave>", lambda e, b=btn: self._btn_hover(b, False))
            self._sidebar_btns[key] = btn

        # Botón Reconectar
        tk.Frame(side, bg=BG_CARD, height=1).pack(fill="x", padx=10, pady=(16, 4))
        tk.Button(
            side, text="🔄  Reconectar", anchor="w",
            bg=BTN_NORM, fg=FG_ORANGE, activebackground=BTN_HOVER,
            font=FONT_SMALL, relief="flat", bd=0,
            padx=14, pady=7, cursor="hand2",
            command=self._check_connection
        ).pack(fill="x")

    def _btn_hover(self, btn, entering: bool):
        if btn is self._active_btn:
            return
        btn.configure(bg=BTN_HOVER if entering else BTN_NORM)

    def _nav_click(self, key: str):
        # Desactivar botón anterior
        if self._active_btn:
            self._active_btn.configure(bg=BTN_NORM, fg=FG_WHITE)
        # Activar nuevo
        btn = self._sidebar_btns[key]
        btn.configure(bg=BTN_ACT, fg="#FFFFFF")
        self._active_btn = btn
        self._active_key = key
        # Cargar reporte
        self._load_report(key)

    # ── Área principal ────────────────────────────────────────────────────────
    def _build_main_area(self, parent):
        self._main = tk.Frame(parent, bg=BG_ROOT)
        self._main.pack(side="left", fill="both", expand=True)

        # Bienvenida inicial
        self._show_welcome()

    def _clear_main(self):
        for w in self._main.winfo_children():
            w.destroy()

    def _show_welcome(self):
        self._clear_main()
        mid = tk.Frame(self._main, bg=BG_ROOT)
        mid.place(relx=0.5, rely=0.42, anchor="center")
        tk.Label(mid, text="🎬", bg=BG_ROOT, fg=FG_BLUE,
                 font=("Segoe UI", 52)).pack()
        tk.Label(mid, text="StreamUCV Data Dictionary Interrogator",
                 bg=BG_ROOT, fg=FG_WHITE,
                 font=("Segoe UI", 16, "bold")).pack(pady=(8, 4))
        tk.Label(mid, text=f"Seleccione un reporte en el panel izquierdo.\nBase de datos: {DATABASE}  |  Esquema: {SCHEMA}",
                 bg=BG_ROOT, fg=FG_GRAY,
                 font=("Segoe UI", 11), justify="center").pack()

    # ── Cabecera de reporte ───────────────────────────────────────────────────
    def _build_report_header(self, title: str, key: str):
        hdr = tk.Frame(self._main, bg=BG_CARD, padx=18, pady=12)
        hdr.pack(fill="x", padx=14, pady=(14, 0))
        tk.Label(hdr, text=title, bg=BG_CARD, fg=FG_WHITE,
                 font=FONT_TITLE, anchor="w").pack(anchor="w")
        tk.Label(hdr, text=DESCRIPTIONS[key], bg=BG_CARD, fg=FG_GRAY,
                 font=FONT_SMALL, wraplength=900, justify="left",
                 anchor="w").pack(anchor="w", pady=(3, 0))

    # ── Tarjetas de resumen ───────────────────────────────────────────────────
    def _build_summary_row(self, stats: list):
        """stats = list of (label, value, color) tuples."""
        row = tk.Frame(self._main, bg=BG_ROOT)
        row.pack(fill="x", padx=14, pady=(8, 0))
        for label, value, color in stats:
            card = tk.Frame(row, bg=BG_CARD, padx=16, pady=10)
            card.pack(side="left", padx=(0, 8))
            tk.Label(card, text=str(value), bg=BG_CARD, fg=color,
                     font=("Segoe UI", 20, "bold")).pack()
            tk.Label(card, text=label, bg=BG_CARD, fg=FG_GRAY,
                     font=FONT_SMALL).pack()

    # ── Treeview con scrollbars ───────────────────────────────────────────────
    def _build_treeview(self, columns: list) -> ttk.Treeview:
        """Crea y retorna un Treeview con las columnas indicadas."""
        wrapper = tk.Frame(self._main, bg=BG_ROOT)
        wrapper.pack(fill="both", expand=True, padx=14, pady=8)

        tree = ttk.Treeview(wrapper, columns=columns, show="headings",
                            style="DD.Treeview")
        vsb = ttk.Scrollbar(wrapper, orient="vertical",
                            command=tree.yview, style="DD.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(wrapper, orient="horizontal",
                            command=tree.xview, style="DD.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # Configurar columnas: ancho dinámico basado en el nombre
        for col in columns:
            w = max(100, min(220, len(col) * 11))
            tree.heading(col, text=col, anchor="w")
            tree.column(col, width=w, minwidth=60, anchor="w")

        tree.tag_configure("odd",  background=TREE_ODD)
        tree.tag_configure("even", background=TREE_EVEN)
        return tree

    def _populate_tree(self, tree: ttk.Treeview, rows: list):
        """Inserta filas en el Treeview con colores alternados."""
        tree.delete(*tree.get_children())
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            display = [("" if v is None else str(v)) for v in row]
            tree.insert("", "end", values=display, tags=(tag,))

    # ── Barra de acciones (Export + Refresh) ─────────────────────────────────
    def _build_action_bar(self, refresh_cmd):
        bar = tk.Frame(self._main, bg=BG_ROOT, pady=4)
        bar.pack(fill="x", padx=14)
        tk.Button(bar, text="📥  Exportar CSV", bg=BG_CARD, fg=FG_GREEN,
                  activebackground=BTN_HOVER, font=FONT_SMALL, relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._export_csv).pack(side="left", padx=(0, 6))
        tk.Button(bar, text="🔄  Actualizar", bg=BG_CARD, fg=FG_BLUE,
                  activebackground=BTN_HOVER, font=FONT_SMALL, relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=refresh_cmd).pack(side="left")

    # ── Exportar CSV ──────────────────────────────────────────────────────────
    def _export_csv(self):
        if not self._last_cols:
            messagebox.showinfo("Sin datos", "No hay resultados para exportar.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"StreamUCV_{self._active_key}_{datetime.date.today()}.csv"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self._last_cols)
                writer.writerows(self._last_rows)
            self._set_status(f"✅ Exportado: {path}", FG_GREEN)
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))

    # ── Status bar ────────────────────────────────────────────────────────────
    def _set_status(self, msg: str, color: str = FG_GRAY):
        self._status_lbl.configure(text=msg, fg=color)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._time_lbl.configure(text=ts)

    # ── Verificar conexión ────────────────────────────────────────────────────
    def _check_connection(self):
        self._conn_lbl.configure(text="Conectando…", fg=FG_ORANGE)
        self._conn_dot.configure(fg=FG_ORANGE)
        ok, info = test_connection()
        if ok:
            self._conn_lbl.configure(text=f"Conectado  — {SERVER}", fg=FG_GREEN)
            self._conn_dot.configure(fg=FG_GREEN)
            self._set_status(f"Conexión establecida: {info[:80]}", FG_GREEN)
        else:
            self._conn_lbl.configure(text="Sin conexión", fg=FG_RED)
            self._conn_dot.configure(fg=FG_RED)
            self._set_status(f"❌ Error: {info}", FG_RED)
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a SQL Server.\n\n{info}\n\n"
                "Verifique los valores en config.py."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # DISPATCHER DE REPORTES
    # ══════════════════════════════════════════════════════════════════════════
    def _load_report(self, key: str):
        dispatch = {
            "1_2": self._show_req1_2,
            "3":   self._show_req3,
            "4":   self._show_req4,
            "5":   self._show_req5,
            "6":   self._show_req6,
            "7_8": self._show_req7_8,
            "9":   self._show_req9,
            "10":  self._show_req10,
        }
        fn = dispatch.get(key)
        if fn:
            fn()

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 1 & 2 — Tablas e Índices
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req1_2(self):
        self._clear_main()
        self._build_report_header("Req 1 & 2  —  Tablas e Índices del Esquema", "1_2")
        try:
            cols, rows = execute_query(SQL_REQ1_2, (SCHEMA,))
            n_tabs = execute_query(SQL_TOTAL_TABLES, (SCHEMA,))[1][0][0]
            n_idx  = execute_query(SQL_TOTAL_INDEXES, (SCHEMA,))[1][0][0]
            self._build_summary_row([
                ("Total de Tablas",  n_tabs, FG_BLUE),
                ("Total de Índices", n_idx,  FG_ORANGE),
                ("Esquema",         SCHEMA,  FG_GRAY),
            ])
            self._build_action_bar(self._show_req1_2)
            tree = self._build_treeview(cols)
            self._populate_tree(tree, rows)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 1 & 2: {n_tabs} tablas, {n_idx} índices.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 3 — Restricciones
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req3(self):
        self._clear_main()
        self._build_report_header("Req 3  —  Restricciones del Esquema", "3")
        try:
            cols, rows = execute_query(SQL_REQ3, (SCHEMA,))
            tipos = {}
            for r in rows:
                tipos[r[2]] = tipos.get(r[2], 0) + 1
            self._build_summary_row([
                ("Total Restricciones", len(rows),              FG_BLUE),
                ("PK",  tipos.get("Clave Primaria  (PK)", 0),   FG_GREEN),
                ("FK",  tipos.get("Clave Foránea   (FK)", 0),   FG_ORANGE),
                ("CHECK", tipos.get("CHECK", 0),                FG_GRAY),
                ("UNIQUE", tipos.get("UNIQUE", 0),              FG_BLUE),
            ])
            self._build_action_bar(self._show_req3)
            tree = self._build_treeview(cols)
            self._populate_tree(tree, rows)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 3: {len(rows)} restricciones encontradas.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 4 — Detalle de Índices
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req4(self):
        self._clear_main()
        self._build_report_header("Req 4  —  Detalle de Índices", "4")
        try:
            cols, rows = execute_query(SQL_REQ4, (SCHEMA,))
            n_unique = sum(1 for r in rows if r[3] == "Sí")
            self._build_summary_row([
                ("Total Índices",   len(rows),  FG_BLUE),
                ("Únicos",         n_unique,    FG_GREEN),
                ("No únicos",      len(rows) - n_unique, FG_GRAY),
            ])
            self._build_action_bar(self._show_req4)
            tree = self._build_treeview(cols)
            self._populate_tree(tree, rows)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 4: {len(rows)} índices con detalle de columnas.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 5 — Triggers
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req5(self):
        self._clear_main()
        self._build_report_header("Req 5  —  Triggers del Esquema", "5")
        try:
            cols, rows = execute_query(SQL_REQ5, (SCHEMA,))
            if rows:
                n_on  = sum(1 for r in rows if r[2] == "Habilitado")
                n_off = len(rows) - n_on
                self._build_summary_row([
                    ("Total Triggers",   len(rows), FG_BLUE),
                    ("Habilitados",      n_on,      FG_GREEN),
                    ("Deshabilitados",   n_off,     FG_RED),
                ])
            else:
                self._build_summary_row([
                    ("Triggers definidos", 0, FG_GRAY),
                ])
            self._build_action_bar(self._show_req5)
            tree = self._build_treeview(cols)
            if rows:
                self._populate_tree(tree, rows)
            else:
                tree.insert("", "end",
                            values=["Sin triggers en el esquema"] + [""] * (len(cols) - 1),
                            tags=("even",))
            self._last_cols, self._last_rows = cols, rows
            msg = f"Req 5: {len(rows)} triggers." if rows else "Req 5: No se encontraron triggers en el esquema streaming."
            self._set_status(msg)
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 6 — Tamaño de Tablas
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req6(self):
        self._clear_main()
        self._build_report_header("Req 6  —  Tamaño Ocupado por Tabla", "6")
        try:
            cols, rows = execute_query(SQL_REQ6, (SCHEMA,))
            total_kb   = sum(int(r[2]) for r in rows)
            total_regs = sum(int(r[4]) for r in rows)
            self._build_summary_row([
                ("Total (KB)",     total_kb,   FG_ORANGE),
                ("Total (MB)",     f"{total_kb/1024:.2f}", FG_BLUE),
                ("Total Registros", total_regs, FG_GREEN),
                ("Tablas",         len(rows),  FG_GRAY),
            ])
            self._build_action_bar(self._show_req6)
            tree = self._build_treeview(cols)
            self._populate_tree(tree, rows)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 6: {len(rows)} tablas — total {total_kb} KB.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 7 & 8 — Tamaño de Registros y Columnas
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req7_8(self):
        self._clear_main()
        self._build_report_header("Req 7 & 8  —  Tamaño de Registros y Columnas", "7_8")
        try:
            cols, rows = execute_query(SQL_REQ7_8, (SCHEMA,))
            # Calcular tr por tabla en Python
            tr_map = {}
            for r in rows:
                tabla = r[0]
                tam   = int(r[4]) if r[4] is not None else 0
                tr_map[tabla] = tr_map.get(tabla, 0) + tam

            max_tr = max(tr_map.values()) if tr_map else 0
            avg_tr = sum(tr_map.values()) // len(tr_map) if tr_map else 0
            self._build_summary_row([
                ("Columnas totales",  len(rows),        FG_BLUE),
                ("Mayor tr (Bytes)", max_tr,            FG_ORANGE),
                ("tr Promedio",      avg_tr,            FG_GREEN),
                ("Tablas",           len(tr_map),       FG_GRAY),
            ])

            # Panel informativo de tr por tabla
            tr_frame = tk.Frame(self._main, bg=BG_CARD, padx=14, pady=6)
            tr_frame.pack(fill="x", padx=14, pady=(4, 0))
            tk.Label(tr_frame, text="Tamaño estimado del registro (tr) por tabla:",
                     bg=BG_CARD, fg=FG_BLUE, font=FONT_BOLD).pack(anchor="w")
            tr_text = "  ".join(
                f"{t}: {v} B" for t, v in sorted(tr_map.items())
            )
            tk.Label(tr_frame, text=tr_text, bg=BG_CARD, fg=FG_WHITE,
                     font=FONT_CODE, wraplength=1000,
                     justify="left").pack(anchor="w", pady=(2, 0))

            self._build_action_bar(self._show_req7_8)
            tree = self._build_treeview(cols)
            self._populate_tree(tree, rows)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 7 & 8: {len(rows)} columnas en {len(tr_map)} tablas.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 9 — Factor de Bloqueo
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req9(self):
        self._clear_main()
        self._build_report_header("Req 9  —  Factor de Bloqueo", "9")
        try:
            cols, rows = execute_query(SQL_REQ9, (SCHEMA,))
            # fb = col[3], tr = col[2]
            fbs = [int(r[3]) for r in rows if r[3] is not None]
            self._build_summary_row([
                ("Tablas",        len(rows),             FG_BLUE),
                ("fb Mínimo",     min(fbs) if fbs else 0, FG_RED),
                ("fb Máximo",     max(fbs) if fbs else 0, FG_GREEN),
                ("fb Promedio",   f"{sum(fbs)/len(fbs):.1f}" if fbs else 0, FG_ORANGE),
            ])

            # Fórmula
            fml = tk.Frame(self._main, bg=BG_CARD, padx=14, pady=8)
            fml.pack(fill="x", padx=14, pady=(4, 0))
            tk.Label(fml, text="Fórmulas aplicadas:", bg=BG_CARD,
                     fg=FG_BLUE, font=FONT_BOLD).pack(anchor="w")
            tk.Label(fml,
                text="  tr  =  Σ max_length de todas las columnas (bytes, supuesto registros fijos)\n"
                     "  fb  =  ⌊ 8.192 / tr ⌋  (división entera — 8 KB por página SQL Server)\n"
                     "  Bloques estimados  =  ⌈ N° registros / fb ⌉",
                bg=BG_CARD, fg=FG_WHITE, font=FONT_CODE,
                justify="left").pack(anchor="w", pady=(2, 0))

            self._build_action_bar(self._show_req9)
            tree = self._build_treeview(cols)
            # Colorear filas con fb bajo (< 3) en naranja
            tree.tag_configure("lowfb", background="#2D1B00", foreground=FG_ORANGE)
            tree.delete(*tree.get_children())
            for i, row in enumerate(rows):
                fb  = int(row[3]) if row[3] is not None else 0
                tag = ("lowfb",) if fb < 3 else (("even" if i % 2 == 0 else "odd"),)
                tree.insert("", "end",
                            values=[("" if v is None else str(v)) for v in row],
                            tags=tag)
            self._last_cols, self._last_rows = cols, rows
            self._set_status(f"Req 9: {len(rows)} tablas — Factor de bloqueo calculado.")
        except Exception as e:
            self._error_panel(str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # REQ 10 — Estimador de Costos de Consulta
    # ══════════════════════════════════════════════════════════════════════════
    def _show_req10(self):
        self._clear_main()
        self._build_report_header("Req 10  —  Estimador de Costos de Consulta", "10")

        # ── Formulario de entrada ─────────────────────────────────────────
        form = tk.Frame(self._main, bg=BG_CARD, padx=20, pady=14)
        form.pack(fill="x", padx=14, pady=(10, 0))

        tk.Label(form, text="Consulta de igualdad:  WHERE  <columna>  =  <valor>",
                 bg=BG_CARD, fg=FG_BLUE, font=FONT_H2).grid(
                 row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Tabla
        tk.Label(form, text="Tabla:", bg=BG_CARD, fg=FG_WHITE,
                 font=FONT_BOLD).grid(row=1, column=0, padx=(0, 8), sticky="w")
        self._req10_table_var.set("")
        tbl_cb = ttk.Combobox(form, textvariable=self._req10_table_var,
                              style="DD.TCombobox", state="readonly",
                              font=FONT_MAIN, width=24)
        tbl_cb.grid(row=1, column=1, padx=(0, 20), sticky="w")

        # Columna
        tk.Label(form, text="Columna:", bg=BG_CARD, fg=FG_WHITE,
                 font=FONT_BOLD).grid(row=1, column=2, padx=(0, 8), sticky="w")
        self._req10_col_var.set("")
        self._col_cb = ttk.Combobox(form, textvariable=self._req10_col_var,
                                    style="DD.TCombobox", state="readonly",
                                    font=FONT_MAIN, width=24)
        self._col_cb.grid(row=1, column=3, sticky="w")

        # Poblar tablas
        try:
            _, tab_rows = execute_query(SQL_GET_TABLES, (SCHEMA,))
            tbl_cb["values"] = [r[0] for r in tab_rows]
        except Exception as e:
            self._error_panel(str(e)); return

        # Cuando cambia la tabla, actualizar columnas
        tbl_cb.bind("<<ComboboxSelected>>", lambda e: self._req10_load_cols())

        # Botón Estimar
        tk.Button(form, text="  ⚙  Estimar Costo  ",
                  bg=BTN_ACT, fg="#FFFFFF", activebackground="#1158CB",
                  font=FONT_BOLD, relief="flat", padx=10, pady=6,
                  cursor="hand2",
                  command=self._estimate_cost).grid(
                  row=1, column=4, padx=(20, 0))

        # ── Área de resultados ────────────────────────────────────────────
        self._req10_result = tk.Frame(self._main, bg=BG_ROOT)
        self._req10_result.pack(fill="both", expand=True, padx=14, pady=10)

        self._set_status("Req 10: Seleccione tabla y columna, luego presione Estimar Costo.")

    def _req10_load_cols(self):
        tabla = self._req10_table_var.get()
        if not tabla:
            return
        try:
            _, rows = execute_query(SQL_GET_COLUMNS, (SCHEMA, tabla))
            self._col_cb["values"] = [f"{r[0]}  [{r[1]}, {r[2]} B]" for r in rows]
            self._col_info_map = {f"{r[0]}  [{r[1]}, {r[2]} B]": r[0] for r in rows}
            self._req10_col_var.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _estimate_cost(self):
        tabla  = self._req10_table_var.get()
        col_lbl = self._req10_col_var.get()
        if not tabla or not col_lbl:
            messagebox.showwarning("Datos incompletos",
                                   "Seleccione una tabla y una columna.")
            return
        columna = getattr(self, "_col_info_map", {}).get(col_lbl, col_lbl.split("  ")[0])

        # Limpiar resultados anteriores
        for w in self._req10_result.winfo_children():
            w.destroy()

        try:
            # ¿Tiene índice?
            _, idx_rows = execute_query(SQL_REQ10_INDEX, (SCHEMA, tabla, columna))
            # Páginas totales
            _, pg_rows  = execute_query(SQL_REQ10_PAGES, (SCHEMA, tabla))
            paginas  = int(pg_rows[0][0]) if pg_rows and pg_rows[0][0] else 0
            registros = int(pg_rows[0][1]) if pg_rows and pg_rows[0][1] else 0

            hay_indice = len(idx_rows) > 0
            if hay_indice:
                nombre_idx = idx_rows[0][0]
                tipo_idx   = idx_rows[0][1]
                es_unico   = bool(idx_rows[0][2])
                accesos    = BTREE_HEIGHT
                tiempo     = (accesos * PAGE_SIZE_BYTES) / (TRANSFER_RATE_MBS * 1024 * 1024)
                metodo     = f"Index Seek  →  {nombre_idx}  ({tipo_idx})"
                color_met  = FG_GREEN
            else:
                accesos = paginas
                tiempo  = (accesos * PAGE_SIZE_BYTES) / (TRANSFER_RATE_MBS * 1024 * 1024) if accesos else 0
                metodo  = "Full Table Scan  (sin índice en esta columna)"
                color_met = FG_ORANGE
                nombre_idx = "—"; tipo_idx = "—"; es_unico = False

            # ── Panel de resultado ────────────────────────────────────────
            # Título
            q_lbl = tk.Label(self._req10_result,
                text=f"SELECT  *  FROM  streaming.{tabla}  WHERE  {columna}  =  ?",
                bg=BG_CARD, fg=FG_WHITE, font=FONT_CODE,
                padx=14, pady=10, anchor="w")
            q_lbl.pack(fill="x")

            # Método de acceso
            m_frm = tk.Frame(self._req10_result, bg=BG_CARD, padx=14, pady=8)
            m_frm.pack(fill="x", pady=(4, 0))
            tk.Label(m_frm, text="Método de acceso:", bg=BG_CARD,
                     fg=FG_GRAY, font=FONT_SMALL).pack(anchor="w")
            tk.Label(m_frm, text=metodo, bg=BG_CARD,
                     fg=color_met, font=FONT_H2).pack(anchor="w")

            # Métricas en tarjetas
            cards = tk.Frame(self._req10_result, bg=BG_ROOT)
            cards.pack(fill="x", pady=(8, 0))
            metricas = [
                ("Tabla",              tabla,         FG_GRAY),
                ("Columna",            columna,       FG_GRAY),
                ("N° Registros",       f"{registros:,}", FG_WHITE),
                ("Páginas totales",    f"{paginas:,}",   FG_WHITE),
                ("Accesos a disco",    f"{accesos:,}",   FG_ORANGE if not hay_indice else FG_GREEN),
                ("Tiempo estimado",    f"{tiempo:.6f} s", FG_BLUE),
                ("Índice utilizable",  "Sí ✓" if hay_indice else "No ✗",
                 FG_GREEN if hay_indice else FG_RED),
            ]
            for lbl, val, col in metricas:
                c = tk.Frame(cards, bg=BG_CARD, padx=14, pady=10)
                c.pack(side="left", padx=(0, 6))
                tk.Label(c, text=str(val), bg=BG_CARD,
                         fg=col, font=("Segoe UI", 14, "bold")).pack()
                tk.Label(c, text=lbl, bg=BG_CARD,
                         fg=FG_GRAY, font=FONT_SMALL).pack()

            # ── Cálculo detallado ─────────────────────────────────────────
            calc_frm = tk.Frame(self._req10_result, bg=BG_CARD, padx=14, pady=12)
            calc_frm.pack(fill="x", pady=(10, 0))
            tk.Label(calc_frm, text="Cálculo detallado:", bg=BG_CARD,
                     fg=FG_BLUE, font=FONT_H2).pack(anchor="w")

            if hay_indice:
                detalle = (
                    f"  Estrategia     :  Index Seek sobre '{nombre_idx}' ({tipo_idx})"
                    + ("  [UNIQUE]" if es_unico else "") + "\n"
                    f"  Supuesto       :  Árbol B-Tree de altura ~3 niveles + 1 página de datos = {BTREE_HEIGHT} accesos\n"
                    f"  Accesos        :  {BTREE_HEIGHT}\n"
                    f"  Bytes leídos   :  {BTREE_HEIGHT} × {PAGE_SIZE_BYTES:,} B  =  {BTREE_HEIGHT * PAGE_SIZE_BYTES:,} B\n"
                    f"  Tasa transf.   :  {TRANSFER_RATE_MBS} MB/s  =  {TRANSFER_RATE_MBS * 1024 * 1024:,} B/s\n"
                    f"  Tiempo         :  {BTREE_HEIGHT * PAGE_SIZE_BYTES:,} B  ÷  {TRANSFER_RATE_MBS * 1024 * 1024:,} B/s"
                    f"  =  {tiempo:.6f} s"
                )
            else:
                detalle = (
                    f"  Estrategia     :  Full Table Scan (columna '{columna}' no es clave líder de ningún índice)\n"
                    f"  Páginas tabla  :  {paginas:,}\n"
                    f"  Accesos        :  {paginas:,}  (una lectura por cada página)\n"
                    f"  Bytes leídos   :  {paginas:,} × {PAGE_SIZE_BYTES:,} B  =  {paginas * PAGE_SIZE_BYTES:,} B\n"
                    f"  Tasa transf.   :  {TRANSFER_RATE_MBS} MB/s  =  {TRANSFER_RATE_MBS * 1024 * 1024:,} B/s\n"
                    f"  Tiempo         :  {paginas * PAGE_SIZE_BYTES:,} B  ÷  {TRANSFER_RATE_MBS * 1024 * 1024:,} B/s"
                    + (f"  =  {tiempo:.6f} s" if accesos else "  =  0 s (tabla vacía)")
                )
            tk.Label(calc_frm, text=detalle, bg=BG_CARD, fg=FG_WHITE,
                     font=FONT_CODE, justify="left").pack(anchor="w", pady=(4, 0))

            self._set_status(
                f"Req 10: {tabla}.{columna} — "
                + ("Índice encontrado" if hay_indice else "Sin índice (Full Scan)")
                + f" — {accesos} accesos — {tiempo:.6f} s"
            )

        except Exception as e:
            self._error_panel(str(e))

    # ── Panel de error ────────────────────────────────────────────────────────
    def _error_panel(self, msg: str):
        frm = tk.Frame(self._main, bg=BG_CARD, padx=20, pady=20)
        frm.pack(fill="x", padx=14, pady=14)
        tk.Label(frm, text="❌  Error al ejecutar la consulta",
                 bg=BG_CARD, fg=FG_RED, font=FONT_H2).pack(anchor="w")
        tk.Label(frm, text=str(msg), bg=BG_CARD, fg=FG_ORANGE,
                 font=FONT_CODE, wraplength=900,
                 justify="left").pack(anchor="w", pady=(6, 0))
        tk.Label(frm, text="Verifique la conexión en config.py y que la BD StreamUCV esté activa.",
                 bg=BG_CARD, fg=FG_GRAY, font=FONT_SMALL).pack(anchor="w", pady=(4, 0))
        self._set_status(f"Error: {msg[:100]}", FG_RED)


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    # Icono (si existe)
    try:
        root.iconbitmap("icon.ico")
    except Exception:
        pass
    app = StreamUCVApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
