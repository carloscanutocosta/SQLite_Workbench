import csv
import json
import os
import threading
import re
import math
import sys
from collections import Counter, deque
from tkinter import BooleanVar, filedialog, messagebox, ttk, Listbox
from typing import Optional

import customtkinter as ctk
from pygments import lex
from pygments.lexers import SqlLexer

from .database import DatabaseManager
from .localization import TRANSLATIONS

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
SETTINGS_FILE = "settings.json"

class ToolTip:
    """Classe para exibir tooltips ao passar o rato sobre widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.schedule_show)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<ButtonPress>", self.hide_tooltip)
        self.id = None

    def schedule_show(self, event=None):
        self.id = self.widget.after(500, self.show_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text: return
        x, y = self.widget.winfo_rootx() + 20, self.widget.winfo_rooty() + 30
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes('-topmost', True)
        ctk.CTkLabel(self.tooltip_window, text=self.text, corner_radius=6, fg_color="#2b2b2b", text_color="#DCE4EE", padx=10, pady=5, font=ctk.CTkFont(size=12)).pack()

    def hide_tooltip(self, event=None):
        if self.id: self.widget.after_cancel(self.id); self.id = None
        if self.tooltip_window: self.tooltip_window.destroy(); self.tooltip_window = None

class CreateTableDialog(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, on_success):
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.on_success = on_success
        self.title(parent.t("create_table_title"))
        self.geometry("700x600")
        self.column_rows = []
        self.fk_rows = []
        self.existing_tables = db_manager.get_tables()

        # Nome da Tabela
        self.name_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.name_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.name_frame, text=parent.t("table_name_title")).pack(side="left")
        self.table_name_entry = ctk.CTkEntry(self.name_frame, width=300)
        self.table_name_entry.pack(side="left", padx=10)

        # Secção de Colunas
        self.cols_frame = ctk.CTkScrollableFrame(self, label_text=parent.t("columns"), height=200)
        self.cols_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.cols_header = ctk.CTkFrame(self.cols_frame, fg_color="transparent")
        self.cols_header.pack(fill="x")
        headers = [parent.t("col_name"), parent.t("col_type"), parent.t("pk"), "AI", parent.t("nn"), ""]
        widths = [150, 100, 30, 30, 30, 30]
        for h, w in zip(headers, widths):
            ctk.CTkLabel(self.cols_header, text=h, width=w, anchor="w").pack(side="left", padx=2)

        # Adicionar primeira coluna por defeito (ID)
        self.add_column_row(default_name="id", default_type="INTEGER", pk=True, ai=True)

        self.add_col_btn = ctk.CTkButton(self, text=parent.t("add_column"), command=self.add_column_row, height=25)
        self.add_col_btn.pack(pady=5)

        # Secção de Chaves Estrangeiras
        self.fks_frame = ctk.CTkScrollableFrame(self, label_text=parent.t("foreign_keys"), height=120)
        self.fks_frame.pack(fill="x", padx=10, pady=5)
        
        self.fks_header = ctk.CTkFrame(self.fks_frame, fg_color="transparent")
        self.fks_header.pack(fill="x")
        fk_headers = [parent.t("col_name"), parent.t("ref_table"), parent.t("ref_col"), ""]
        for h in fk_headers:
            ctk.CTkLabel(self.fks_header, text=h, width=130, anchor="w").pack(side="left", padx=2)

        self.add_fk_btn = ctk.CTkButton(self, text=parent.t("add_fk"), command=self.add_fk_row, height=25, fg_color="gray")
        self.add_fk_btn.pack(pady=5)

        # Botões de Ação
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkButton(self.btn_frame, text=parent.t("save"), command=self.save_table).pack(side="right", padx=5)
        ctk.CTkButton(self.btn_frame, text=parent.t("cancel"), fg_color="transparent", border_width=1, command=self.destroy).pack(side="right", padx=5)

    def add_column_row(self, default_name="", default_type="TEXT", pk=False, ai=False):
        row = ctk.CTkFrame(self.cols_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        entry_name = ctk.CTkEntry(row, width=150)
        entry_name.insert(0, default_name)
        entry_name.pack(side="left", padx=2)
        
        type_menu = ctk.CTkOptionMenu(row, values=["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"], width=100)
        type_menu.set(default_type)
        type_menu.pack(side="left", padx=2)
        
        var_pk = ctk.BooleanVar(value=pk)
        chk_pk = ctk.CTkCheckBox(row, text="", variable=var_pk, width=30)
        chk_pk.pack(side="left", padx=2)

        var_ai = ctk.BooleanVar(value=ai)
        chk_ai = ctk.CTkCheckBox(row, text="", variable=var_ai, width=30)
        chk_ai.pack(side="left", padx=2)

        var_nn = ctk.BooleanVar(value=False)
        chk_nn = ctk.CTkCheckBox(row, text="", variable=var_nn, width=30)
        chk_nn.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(row, text=self.parent.t("remove"), width=30, fg_color="#D2042D", command=lambda: self._remove_row(row, self.column_rows))
        btn_del.pack(side="left", padx=2)

        self.column_rows.append({"frame": row, "name": entry_name, "type": type_menu, "pk": var_pk, "ai": var_ai, "nn": var_nn})

    def add_fk_row(self):
        row = ctk.CTkFrame(self.fks_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        entry_local = ctk.CTkEntry(row, width=130, placeholder_text=self.parent.t("col_name"))
        entry_local.pack(side="left", padx=2)
        
        menu_table = ctk.CTkOptionMenu(row, values=self.existing_tables, width=130)
        menu_table.pack(side="left", padx=2)
        
        entry_ref_col = ctk.CTkEntry(row, width=130, placeholder_text="id")
        entry_ref_col.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(row, text=self.parent.t("remove"), width=30, fg_color="#D2042D", command=lambda: self._remove_row(row, self.fk_rows))
        btn_del.pack(side="left", padx=2)

        self.fk_rows.append({"frame": row, "local": entry_local, "table": menu_table, "ref": entry_ref_col})

    def _remove_row(self, row_frame, list_ref):
        row_frame.destroy()
        list_ref[:] = [item for item in list_ref if item["frame"] != row_frame]

    def save_table(self):
        name = self.table_name_entry.get().strip()
        if not name: return messagebox.showerror("Error", "Table name required")
        
        cols = []
        for r in self.column_rows:
            cols.append({"name": r["name"].get(), "type": r["type"].get(), "pk": r["pk"].get(), "ai": r["ai"].get(), "nn": r["nn"].get()})
            
        fks = []
        for r in self.fk_rows:
            fks.append({"from": r["local"].get(), "table": r["table"].get(), "to": r["ref"].get()})
            
        self.on_success(name, cols, fks)
        self.destroy()

class ERDViewer(ctk.CTkToplevel):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.title(parent.t("erd_view"))
        self.geometry("1000x800")
        
        self.canvas = ctk.CTkCanvas(self, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.tables = {} # {name: {x, y, w, h, columns, fks}}
        self.drag_data = {"item": None, "x": 0, "y": 0}
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        
        self.load_schema()
        self.arrange_tables()
        self.draw()

        ctk.CTkLabel(self, text=parent.t("erd_help"), text_color="gray", bg_color="#2b2b2b").place(x=10, y=10)

    def load_schema(self):
        table_names = self.db_manager.get_tables()
        for name in table_names:
            cols = self.db_manager.get_columns(name)
            fks = self.db_manager.get_foreign_keys(name)
            # Estimativa de dimensões
            h = 30 + (len(cols) * 20)
            w = 160
            self.tables[name] = {"x": 0, "y": 0, "w": w, "h": h, "cols": cols, "fks": fks}

    def arrange_tables(self):
        # Layout circular simples para distribuir as tabelas inicialmente
        n = len(self.tables)
        center_x, center_y = 500, 400
        radius = min(300, n * 30)
        if n > 0:
            angle_step = 360 / n
            for i, name in enumerate(self.tables):
                angle_rad = math.radians(i * angle_step)
                self.tables[name]["x"] = center_x + radius * math.cos(angle_rad) - self.tables[name]["w"]/2
                self.tables[name]["y"] = center_y + radius * math.sin(angle_rad) - self.tables[name]["h"]/2

    def draw(self):
        self.canvas.delete("all")
        
        # Desenhar conexões primeiro (atrás das tabelas)
        for name, data in self.tables.items():
            cx = data["x"] + data["w"]/2
            cy = data["y"] + data["h"]/2
            for fk in data["fks"]:
                target = fk["table"]
                if target in self.tables:
                    t_data = self.tables[target]
                    tx = t_data["x"] + t_data["w"]/2
                    ty = t_data["y"] + t_data["h"]/2
                    self.canvas.create_line(cx, cy, tx, ty, fill="#555", arrow="last", width=2)

        # Desenhar tabelas
        for name, data in self.tables.items():
            x, y, w, h = data["x"], data["y"], data["w"], data["h"]
            # Caixa
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="#333", outline="#555", tags=("table", name))
            # Cabeçalho
            self.canvas.create_rectangle(x, y, x+w, y+25, fill="#1f538d", outline="#555", tags=("table", name))
            self.canvas.create_text(x+w/2, y+12, text=name, fill="white", font=("Arial", 10, "bold"), tags=("table", name))
            # Colunas
            for i, col in enumerate(data["cols"]):
                self.canvas.create_text(x+10, y+40+(i*20), text=col, fill="#ddd", anchor="w", font=("Arial", 9), tags=("table", name))

    def on_press(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x, y, x+1, y+1)
        for item in items:
            tags = self.canvas.gettags(item)
            if "table" in tags:
                self.drag_data["item"] = tags[1]
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                return

    def on_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            name = self.drag_data["item"]
            self.tables[name]["x"] += dx
            self.tables[name]["y"] += dy
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.draw()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1100x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.db_manager: Optional[DatabaseManager] = None
        self.current_table_buttons = []
        self.query_history = deque(maxlen=20)
        self.history_buttons = []
        self.favorite_queries = []
        self.favorite_buttons = []
        self.tree_context_menu = None
        self.sidebar_context_menu = None
        self.context_menu_table_name: Optional[str] = None
        self.read_only_var = BooleanVar(value=False)
        self.current_table_name: Optional[str] = None
        self.current_filter: dict = {}
        self.current_page = 1
        self.rows_per_page = 1000
        self.sort_column: Optional[str] = None
        self.sort_order: str = "ASC"
        self.total_rows = 0
        self.total_pages = 1
        self.theme_mode = "Dark"
        self.language = "pt"
        self.autocomplete_list = []
        self.suggestion_window = None
        self._load_settings()
        ctk.set_appearance_mode(self.theme_mode)
        self.title(f"{self.t('app_title')} v1.0.0")

        # Configurar ícone da janela
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
            
        icon_path = os.path.join(base_path, "Assets", "Icons", "icon.ico")
        if not os.path.exists(icon_path): # Fallback para desenvolvimento
             icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Assets", "Icons", "icon.ico")

        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._setup_ui()
        self._setup_treeview_style()
        self._create_tree_context_menu()
        self._create_sidebar_context_menu()
        self._setup_sql_tags()
        self._load_favorites()
        self._load_history()

    def t(self, key):
        """Retorna o texto traduzido para a chave fornecida."""
        return TRANSLATIONS.get(self.language, TRANSLATIONS["pt"]).get(key, key)

    def _setup_ui(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        ctk.CTkLabel(self.sidebar_frame, text=self.t("db_explorer"), font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        load_btn = ctk.CTkButton(self.sidebar_frame, text=self.t("load_db"), command=self.load_database)
        load_btn.grid(row=1, column=0, padx=20, pady=10)
        ToolTip(load_btn, self.t("tooltip_load_db"))
        
        self.import_csv_btn = ctk.CTkButton(self.sidebar_frame, text=self.t("import_csv"), command=self._import_csv, state="disabled")
        self.import_csv_btn.grid(row=2, column=0, padx=20, pady=(0, 10))
        ToolTip(self.import_csv_btn, self.t("tooltip_import_csv"))

        self.new_table_btn = ctk.CTkButton(self.sidebar_frame, text=self.t("new_table"), command=self._open_create_table_dialog, state="disabled")
        self.new_table_btn.grid(row=3, column=0, padx=20, pady=(0, 10))
        ToolTip(self.new_table_btn, self.t("tooltip_new_table"))

        self.vacuum_btn = ctk.CTkButton(self.sidebar_frame, text=self.t("compact_db"), command=self._vacuum_database, state="disabled")
        self.vacuum_btn.grid(row=4, column=0, padx=20, pady=(0, 10))
        ToolTip(self.vacuum_btn, self.t("tooltip_vacuum"))

        self.erd_btn = ctk.CTkButton(self.sidebar_frame, text=self.t("erd_view"), command=self._open_erd_viewer, state="disabled", fg_color="#1f538d")
        self.erd_btn.grid(row=5, column=0, padx=20, pady=(0, 10))
        ToolTip(self.erd_btn, self.t("erd_help"))

        self.search_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text=self.t("search_placeholder"))
        self.search_entry.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.search_entry.configure(state="disabled")
        self.scrollable_tables_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text=self.t("tables"))
        self.scrollable_tables_frame.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="nsew")
        
        self.settings_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.settings_frame.grid(row=8, column=0, padx=20, pady=10, sticky="sw")

        # Language Menu
        self.language_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Português", "English"],
            command=self._change_language
        )
        self.language_menu.set("Português" if self.language == "pt" else "English")
        self.language_menu.pack(fill="x", pady=(5, 5))

        ctk.CTkLabel(self.settings_frame, text=self.t("theme")).pack(anchor="w")
        self.theme_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Dark", "Light", "System"],
            command=self._change_theme,
        )
        self.theme_menu.set(self.theme_mode)
        self.theme_menu.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(self.settings_frame, text=self.t("rows_per_page")).pack(anchor="w")
        self.rows_per_page_menu = ctk.CTkOptionMenu(self.settings_frame, values=["100", "500", "1000", "5000"], width=80, command=self._change_rows_per_page)
        self.rows_per_page_menu.set(str(self.rows_per_page))
        self.rows_per_page_menu.pack(anchor="w")

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.header_frame, text=self.t("no_file"), font=ctk.CTkFont(size=14), anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.export_btn = ctk.CTkButton(self.header_frame, text=self.t("export_csv"), width=100, fg_color="#2b825b", hover_color="#1e5c41", command=self.export_data, state="disabled")
        self.export_btn.grid(row=0, column=1, sticky="e")
        ToolTip(self.export_btn, self.t("tooltip_export"))

        self.new_record_btn = ctk.CTkButton(self.header_frame, text=self.t("new_record"), width=100, command=self._insert_record, state="disabled")
        self.new_record_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))
        ToolTip(self.new_record_btn, self.t("tooltip_new_record"))

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.tab_data = self.tabview.add(self.t("tab_data"))
        self.tab_schema = self.tabview.add(self.t("tab_schema"))
        self.tab_stats = self.tabview.add(self.t("tab_stats"))
        self.tab_sql = self.tabview.add(self.t("tab_sql"))
        for tab in self.tabview._tab_dict.values():
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        # Área de Pesquisa na aba de Dados
        self.search_frame = ctk.CTkFrame(self.tab_data, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        # Componentes do Filtro
        self.filter_col_menu = ctk.CTkOptionMenu(self.search_frame, values=["Todos"], width=120)
        self.filter_col_menu.pack(side="left", padx=(0, 5))
        ToolTip(self.filter_col_menu, "Coluna para filtrar")

        self.filter_op_menu = ctk.CTkOptionMenu(self.search_frame, values=["LIKE", "=", "!=", ">", "<", ">=", "<="], width=80)
        self.filter_op_menu.pack(side="left", padx=(0, 5))
        ToolTip(self.filter_op_menu, "Operador")

        self.data_search_entry = ctk.CTkEntry(self.search_frame, placeholder_text=self.t("search_data_placeholder"))
        self.data_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.data_search_entry.bind("<Return>", self._perform_data_search)
        
        self.data_search_btn = ctk.CTkButton(self.search_frame, text=self.t("search_btn"), width=80, command=self._perform_data_search)
        self.data_search_btn.pack(side="left")
        self.data_clear_btn = ctk.CTkButton(self.search_frame, text=self.t("clear_btn"), width=60, fg_color="gray", hover_color="gray30", command=self._clear_data_search)
        self.data_clear_btn.pack(side="left", padx=(5, 0))

        self.data_progress = ctk.CTkProgressBar(self.tab_data, height=10, mode="indeterminate")
        self.data_progress.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 5))
        self.data_progress.grid_remove()

        self.tree_container = ctk.CTkFrame(self.tab_data, fg_color="transparent")
        self.tree_container.grid(row=2, column=0, sticky="nsew")
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)
        self.tree = self._create_treeview(self.tree_container)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")
        self.tree.bind("<Button-3>", self._show_tree_context_menu)

        self.pagination_frame = ctk.CTkFrame(self.tab_data, fg_color="transparent")
        self.pagination_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(10, 0))
        self.prev_page_btn = ctk.CTkButton(self.pagination_frame, text=self.t("prev"), width=80, command=self.prev_page)
        self.prev_page_btn.pack(side="left")
        self.page_entry = ctk.CTkEntry(self.pagination_frame, width=60, justify="center")
        self.page_entry.pack(side="left", padx=10)
        self.page_entry.bind("<Return>", self.jump_to_page)
        self.page_label = ctk.CTkLabel(self.pagination_frame, text=f"{self.t('page_of')} 1")
        self.page_label.pack(side="left")
        self.next_page_btn = ctk.CTkButton(self.pagination_frame, text=self.t("next"), width=80, command=self.next_page)
        self.next_page_btn.pack(side="left", padx=10)
        self.pagination_frame.grid_remove()

        self.schema_textbox = ctk.CTkTextbox(self.tab_schema, font=ctk.CTkFont(family="Consolas", size=14))
        self.schema_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.schema_textbox.configure(state="disabled")
        self.stats_frame = ctk.CTkScrollableFrame(self.tab_stats, fg_color="transparent")
        self.stats_frame.grid(row=0, column=0, sticky="nsew")

        self.sql_frame = ctk.CTkFrame(self.tab_sql, fg_color="transparent")
        self.sql_frame.grid(row=0, column=0, sticky="nsew")
        self.sql_frame.grid_columnconfigure(0, weight=3)
        self.sql_frame.grid_columnconfigure(1, weight=1)
        self.sql_left_pane = ctk.CTkFrame(self.sql_frame, fg_color="transparent")
        self.sql_left_pane.grid(row=0, column=0, sticky="nsew")
        self.sql_left_pane.grid_rowconfigure(0, weight=1)
        self.sql_left_pane.grid_rowconfigure(2, weight=2)
        self.sql_left_pane.grid_columnconfigure(0, weight=1)
        self.sql_input = ctk.CTkTextbox(self.sql_left_pane, font=ctk.CTkFont(family="Consolas", size=14))
        self.sql_input.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        self.sql_input.insert("0.0", "-- Query SQL\nSELECT * FROM sqlite_master;")
        self.sql_input.bind("<KeyRelease>", self._on_key_release)
        self.sql_input.bind("<Tab>", self._confirm_autocomplete)
        self.sql_input.bind("<Up>", self._navigate_autocomplete)
        self.sql_input.bind("<Down>", self._navigate_autocomplete)
        self.sql_input.bind("<Return>", self._handle_return)
        self.sql_input.bind("<FocusOut>", lambda e: self._hide_autocomplete())
        self.sql_input.bind("<Control-Return>", lambda event: self.run_custom_query())
        self.sql_execute_btn = ctk.CTkButton(self.sql_left_pane, text=self.t("exec_sql"), command=self.run_custom_query, state="disabled")
        self.sql_execute_btn.grid(row=1, column=0, sticky="e", padx=(0, 5), pady=(5, 10))
        ToolTip(self.sql_execute_btn, self.t("tooltip_run_sql"))
        self.sql_tree_container = ctk.CTkFrame(self.sql_left_pane, fg_color="transparent")
        self.sql_tree_container.grid(row=2, column=0, sticky="nsew", padx=(0, 5))
        self.sql_tree_container.grid_rowconfigure(0, weight=1)
        self.sql_tree_container.grid_columnconfigure(0, weight=1)
        self.tree_sql = self._create_treeview(self.sql_tree_container)

        self.sql_right_pane = ctk.CTkTabview(self.sql_frame, width=250)
        self.sql_right_pane.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        self.history_tab = self.sql_right_pane.add(self.t("tab_history"))
        self.favorites_tab = self.sql_right_pane.add(self.t("tab_favorites"))
        self.history_frame = ctk.CTkScrollableFrame(self.history_tab, label_text="")
        self.history_frame.pack(expand=True, fill="both")
        self.favorites_frame = ctk.CTkScrollableFrame(self.favorites_tab, label_text="")
        self.favorites_frame.pack(expand=True, fill="both")

        # Footer
        self.footer_frame = ctk.CTkFrame(self, height=25, corner_radius=0, fg_color="transparent")
        self.footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))
        self.author_label = ctk.CTkLabel(self.footer_frame, text=self.t("footer_author"), font=ctk.CTkFont(size=11), text_color="gray")
        self.author_label.pack(side="left")

    def _create_treeview(self, parent):
        tree = ttk.Treeview(parent, selectmode="browse", show="headings")
        ttk.Scrollbar(parent, orient="vertical", command=tree.yview).grid(row=0, column=1, sticky="ns")
        ttk.Scrollbar(parent, orient="horizontal", command=tree.xview).grid(row=1, column=0, sticky="ew")
        tree.grid(row=0, column=0, sticky="nsew")
        return tree

    def _create_tree_context_menu(self):
        self.tree_context_menu = ctk.CTkFrame(self)
        ctk.CTkButton(self.tree_context_menu, text=self.t("edit"), command=self._edit_record, width=120).pack(pady=(5, 2), padx=5)
        ctk.CTkButton(self.tree_context_menu, text=self.t("delete"), command=self._delete_record, fg_color="#D2042D", hover_color="#8A031E", width=120).pack(pady=(2, 5), padx=5)

    def _create_sidebar_context_menu(self):
        self.sidebar_context_menu = ctk.CTkFrame(self)
        ctk.CTkButton(self.sidebar_context_menu, text=self.t("rename"), command=self._rename_table, width=140).pack(pady=(5, 2), padx=5)
        ctk.CTkButton(self.sidebar_context_menu, text=self.t("delete"), command=self._delete_table, fg_color="#D2042D", hover_color="#8A031E", width=140).pack(pady=(2, 5), padx=5)

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background="#343638", foreground="white", relief="flat")

    def _setup_sql_tags(self):
        for tag, color in {
            "Token.Keyword": "#ff79c6",
            "Token.Keyword.Dml": "#ff79c6",
            "Token.Literal.String.Single": "#f1fa8c",
            "Token.Literal.Number.Integer": "#bd93f9",
            "Token.Comment.Single": "#6272a4",
            "Token.Name": "#8be9fd",
            "Token.Operator": "#ffb86c",
        }.items():
            self.sql_input._textbox.tag_config(tag, foreground=color)
        self._update_syntax_highlighting()

    def _update_syntax_highlighting(self, event=None):
        if event and event.keysym in ["Left", "Right", "Up", "Down", "Shift_L", "Control_L"]:
            return
        text_widget = self.sql_input._textbox
        code = text_widget.get("1.0", "end-1c")
        for tag in text_widget.tag_names():
            text_widget.tag_remove(tag, "1.0", "end")
        line, col = 1, 0
        for token, content in lex(code, SqlLexer()):
            for part in content.splitlines(keepends=True):
                end_col = col + len(part)
                text_widget.tag_add(str(token), f"{line}.{col}", f"{line}.{end_col}")
                if part.endswith("\n"):
                    line += 1
                    col = 0
                else:
                    col = end_col

    def _on_tree_motion(self, event=None):
        if self.tree_context_menu:
            self.tree_context_menu.place_forget()

    def _on_tree_click(self, event=None):
        if self.tree_context_menu:
            self.tree_context_menu.place_forget()
        if self.sidebar_context_menu:
            self.sidebar_context_menu.place_forget()

    def _clear_main_view(self):
        self.current_table_name = None
        self.current_page = 1
        self.total_rows = 0
        self.total_pages = 1
        self._clear_treeview(self.tree)
        self._clear_treeview(self.tree_sql)
        self.schema_textbox.configure(state="normal")
        self.schema_textbox.delete("0.0", "end")
        self.schema_textbox.configure(state="disabled")
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        self.pagination_frame.grid_remove()
        self.export_btn.configure(state="disabled")
        self.new_record_btn.configure(state="disabled")
        self.status_label.configure(text=self.t("no_file"))
        self.data_search_entry.delete(0, "end")

    def load_database(self):
        file_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db"), ("Todos", "*.*")])
        if not file_path:
            return
        self._clear_main_view()
        try:
            if self.db_manager:
                self.db_manager.disconnect()
            self.db_manager = DatabaseManager(file_path)
            self.status_label.configure(text=f"{self.t('file_loaded')} {os.path.basename(file_path)}")
            self.import_csv_btn.configure(state="normal")
            self.vacuum_btn.configure(state="normal")
            self.new_table_btn.configure(state="normal")
            self.sql_execute_btn.configure(state="normal")
            self.erd_btn.configure(state="normal")
            self._refresh_table_list()
            if not self.current_table_buttons:
                messagebox.showwarning(self.t("warning"), self.t("db_empty_warning"))
        except Exception as e:
            messagebox.showerror(self.t("error"), str(e))

    def _refresh_table_list(self):
        for btn in self.current_table_buttons:
            btn.destroy()
        self.current_table_buttons.clear()
        if not self.db_manager:
            return
            
        self._load_autocomplete_data()
        
        tables = self.db_manager.get_tables()
        self.search_entry.configure(state="normal" if tables else "disabled")
        for table in tables:
            btn = ctk.CTkButton(self.scrollable_tables_frame, text=table, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), anchor="w", command=lambda t=table: self.show_table_data(t))
            btn.bind("<Button-3>", self._show_sidebar_context_menu)
            btn.pack(fill="x", pady=2, padx=5)
            self.current_table_buttons.append(btn)

    def _change_rows_per_page(self, new_value: str):
        self.rows_per_page = int(new_value)
        if self.current_table_name:
            self.show_table_data(self.current_table_name)

    def _change_theme(self, new_theme: str):
        self.theme_mode = new_theme
        ctk.set_appearance_mode(new_theme)
        self._save_settings()
    
    def _change_language(self, new_lang: str):
        self.language = "pt" if new_lang == "Português" else "en"
        self._save_settings()
        messagebox.showinfo(self.t("success"), self.t("restart_msg"))

    def _open_create_table_dialog(self):
        if not self.db_manager:
            messagebox.showwarning(self.t("warning"), self.t("load_db_first"))
            return
            
        def on_create(name, cols, fks):
            try:
                self.db_manager.create_table(name, cols, fks)
                self._refresh_table_list()
                self.show_table_data(name)
                messagebox.showinfo(self.t("success"), f"Tabela '{name}' criada.")
            except Exception as e:
                messagebox.showerror(self.t("error"), str(e))

        CreateTableDialog(self, self.db_manager, on_create)

    def _open_erd_viewer(self):
        if self.db_manager:
            ERDViewer(self, self.db_manager)

    def _import_csv(self):
        if not self.db_manager:
            messagebox.showwarning(self.t("warning"), self.t("load_db_first"))
            return
        csv_path = filedialog.askopenfilename(title=self.t("select_csv_title"), filetypes=[("CSV Files", "*.csv"), ("Todos os ficheiros", "*.*")])
        if not csv_path:
            return
        dialog = ctk.CTkInputDialog(text=self.t("enter_table_name"), title=self.t("table_name_title"))
        table_name = dialog.get_input()
        if not table_name or not table_name.strip():
            return
        try:
            self.db_manager.import_csv_to_table(csv_path, table_name.strip(), delimiter=";")
            self._refresh_table_list()
        except Exception as e:
            messagebox.showerror(self.t("error"), str(e))

    def _vacuum_database(self):
        if not self.db_manager:
            messagebox.showwarning(self.t("warning"), self.t("load_db_first"))
            return

        msg = self.t("vacuum_confirm")
        if messagebox.askyesno(self.t("confirm"), msg):
            try:
                self.db_manager.vacuum()
                messagebox.showinfo(self.t("success"), self.t("vacuum_success"))
                current_table = self.current_table_name
                self._refresh_table_list()
                if current_table and any(btn.cget("text") == current_table for btn in self.current_table_buttons):
                    self.show_table_data(current_table)
                else:
                    self._clear_main_view()
            except Exception as e:
                messagebox.showerror(self.t("error"), f"{e}")

    def _show_tree_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.tree_context_menu.lift()
            scaling = self._get_window_scaling()
            x = (event.x_root - self.winfo_rootx()) / scaling
            y = (event.y_root - self.winfo_rooty()) / scaling
            self.tree_context_menu.place(x=x, y=y)

    def _show_sidebar_context_menu(self, event):
        self.context_menu_table_name = event.widget.cget("text")
        self.sidebar_context_menu.lift()
        scaling = self._get_window_scaling()
        x = (event.x_root - self.winfo_rootx()) / scaling
        y = (event.y_root - self.winfo_rooty()) / scaling
        self.sidebar_context_menu.place(x=x, y=y)

    def show_table_data(self, table_name, reset_filter=True):
        if not self.db_manager:
            return
        self.current_table_name = table_name
        if reset_filter:
            self._clear_data_search(reload=False)
        self.sort_column = None
        self.sort_order = "ASC"
        schema = self.db_manager.get_table_schema(table_name)
        self.schema_textbox.configure(state="normal")
        self.schema_textbox.delete("0.0", "end")
        self.schema_textbox.insert("0.0", schema)
        self.schema_textbox.configure(state="disabled")
        self._load_table_statistics(table_name)
        self.pagination_frame.grid()
        
        # Atualizar dropdown de colunas
        columns = self.db_manager.get_columns(table_name)
        filter_opts = ["Todos"] + columns
        self.filter_col_menu.configure(values=filter_opts)
        self.filter_col_menu.set("Todos")
        
        self._refresh_data_view()
        self.new_record_btn.configure(state="normal")
        self.export_btn.configure(state="normal")

    def _perform_data_search(self, event=None):
        self.current_filter = {
            "column": self.filter_col_menu.get(),
            "operator": self.filter_op_menu.get(),
            "value": self.data_search_entry.get().strip()
        }
        self._refresh_data_view()

    def _clear_data_search(self, reload=True):
        self.current_filter = {}
        self.data_search_entry.delete(0, "end")
        self.filter_col_menu.set("Todos")
        self.filter_op_menu.set("LIKE")
        if reload and self.current_table_name:
            self._refresh_data_view()

    def _refresh_data_view(self):
        """Inicia o carregamento da primeira página e recálculo total."""
        self._load_page_data(1, calculate_total=True)

    def _load_page_data(self, page_number: int, calculate_total: bool = False):
        """Inicia o carregamento dos dados em thread separada."""
        if not self.db_manager or not self.current_table_name:
            return

        self.data_progress.grid()
        self.data_progress.start()
        self._set_data_controls_state("disabled")

        threading.Thread(
            target=self._thread_fetch_data,
            args=(self.current_table_name, page_number, self.current_filter, calculate_total, self.sort_column, self.sort_order),
            daemon=True
        ).start()

    def _thread_fetch_data(self, table_name, page, filter_config, calculate_total, sort_column, sort_order):
        try:
            total_rows = None
            if calculate_total:
                total_rows = self.db_manager.get_table_row_count(table_name, filter_config)
            
            offset = (page - 1) * self.rows_per_page
            columns, rows = self.db_manager.get_table_data(
                table_name, 
                limit=self.rows_per_page, 
                offset=offset, 
                filter_config=filter_config,
                sort_column=sort_column,
                sort_order=sort_order
            )
            
            self.after(0, lambda: self._on_data_ready(table_name, page, total_rows, columns, rows))
        except Exception as e:
            self.after(0, lambda: self._on_data_error(e))

    def _on_data_ready(self, table_name, page, total_rows, columns, rows):
        self.data_progress.stop()
        self.data_progress.grid_remove()
        self._set_data_controls_state("normal")

        if table_name != self.current_table_name:
            return
            
        if total_rows is not None:
            self.total_rows = total_rows
            self.total_pages = max(1, (self.total_rows + self.rows_per_page - 1) // self.rows_per_page)
        
        self.current_page = page
        self._clear_treeview(self.tree)
        self._fill_treeview(self.tree, columns, rows, sort_callback=self._sort_by_column)
        self._update_pagination_controls()

    def _on_data_error(self, error):
        self.data_progress.stop()
        self.data_progress.grid_remove()
        self._set_data_controls_state("normal")
        messagebox.showerror(self.t("error"), str(error))

    def _set_data_controls_state(self, state):
        self.data_search_btn.configure(state=state)
        self.prev_page_btn.configure(state=state if state == "disabled" else ("normal" if self.current_page > 1 else "disabled"))
        self.next_page_btn.configure(state=state if state == "disabled" else ("normal" if self.current_page < self.total_pages else "disabled"))

    def _update_pagination_controls(self):
        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, str(self.current_page))
        self.page_label.configure(text=f"{self.t('page_of')} {self.total_pages}  ({self.total_rows} {self.t('lines')})")
        self.prev_page_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")
        self.status_label.configure(text=f"{self.t('table_label')} {self.current_table_name}")

    def prev_page(self):
        if self.current_page > 1:
            self._load_page_data(self.current_page - 1)

    def next_page(self):
        if self.current_page < self.total_pages:
            self._load_page_data(self.current_page + 1)

    def jump_to_page(self, event=None):
        try:
            page = int(self.page_entry.get())
            if 1 <= page <= self.total_pages:
                self._load_page_data(page)
        except ValueError:
            self.page_entry.delete(0, "end")
            self.page_entry.insert(0, str(self.current_page))

    def _edit_record(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        values = self.tree.item(selected_items[0], "values")
        if not values:
            return

        # rowid é a primeira coluna (index 0) conforme configurado em _fill_treeview
        rowid = values[0]
        columns = self.tree["columns"]

        current_data = {}
        for i, col in enumerate(columns):
            if col == "rowid":
                continue
            current_data[col] = values[i]

        self._open_edit_dialog(rowid, current_data)

    def _open_edit_dialog(self, rowid, current_data):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{self.t('edit')} (ID: {rowid})")
        dialog.geometry("500x600")
        dialog.grab_set()
        dialog.focus_force()

        scroll_frame = ctk.CTkScrollableFrame(dialog, label_text=self.t("edit_values"))
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        entries = {}
        for col, value in current_data.items():
            ctk.CTkLabel(scroll_frame, text=col, anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(5, 0))
            entry = ctk.CTkEntry(scroll_frame)
            entry.pack(fill="x", pady=(0, 5))
            if value != "None":
                entry.insert(0, str(value))
            entries[col] = entry

        def save_changes():
            new_data = {col: entry.get() for col, entry in entries.items()}
            try:
                self.db_manager.update_record(self.current_table_name, rowid, new_data)
                messagebox.showinfo(self.t("success"), self.t("record_updated"))
                dialog.destroy()
                self._load_page_data(self.current_page, calculate_total=False)
            except Exception as e:
                messagebox.showerror(self.t("error"), str(e))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text=self.t("cancel"), fg_color="transparent", border_width=1, command=dialog.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text=self.t("save"), command=save_changes).pack(side="right", expand=True, padx=5)

    def _insert_record(self):
        if not self.current_table_name:
            return
            
        # Obter colunas da Treeview
        columns = list(self.tree["columns"])
        # Remover rowid se existir, pois é gerado automaticamente
        if "rowid" in columns:
            columns.remove("rowid")
            
        self._open_insert_dialog(columns)

    def _open_insert_dialog(self, columns):
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.t("new_record"))
        dialog.geometry("500x600")
        dialog.grab_set()
        dialog.focus_force()

        scroll_frame = ctk.CTkScrollableFrame(dialog, label_text=self.t("fill_values"))
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        entries = {}
        for col in columns:
            ctk.CTkLabel(scroll_frame, text=col, anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(5, 0))
            entry = ctk.CTkEntry(scroll_frame)
            entry.pack(fill="x", pady=(0, 5))
            entries[col] = entry

        def save_new():
            data = {col: entry.get() for col, entry in entries.items()}
            try:
                self.db_manager.insert_record(self.current_table_name, data)
                messagebox.showinfo(self.t("success"), self.t("record_inserted"))
                dialog.destroy()
                self._load_page_data(self.current_page, calculate_total=True)
            except Exception as e:
                messagebox.showerror(self.t("error"), str(e))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text=self.t("cancel"), fg_color="transparent", border_width=1, command=dialog.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text=self.t("insert"), command=save_new).pack(side="right", expand=True, padx=5)

    def _delete_record(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        rowid = self.tree.item(selected_items[0], "values")[0]
        if messagebox.askyesno(self.t("confirm"), self.t("confirm_delete_record").format(rowid)):
            self.db_manager.delete_record(self.current_table_name, rowid)
            self._load_page_data(self.current_page, calculate_total=True)

    def _rename_table(self):
        if not self.context_menu_table_name or not self.db_manager:
            return
        dialog = ctk.CTkInputDialog(text=self.t("rename_table_prompt").format(self.context_menu_table_name), title=self.t("rename"))
        new_name = dialog.get_input()
        if not new_name or not new_name.strip():
            return
        self.db_manager.rename_table(self.context_menu_table_name, new_name.strip())
        if self.current_table_name == self.context_menu_table_name:
            self.current_table_name = new_name.strip()
        self._refresh_table_list()

    def _delete_table(self):
        if not self.context_menu_table_name or not self.db_manager:
            return
        confirm_msg = self.t("confirm_delete_table").format(self.context_menu_table_name)
        if messagebox.askyesno(self.t("confirm"), confirm_msg):
            self.db_manager.delete_table(self.context_menu_table_name)
            if self.current_table_name == self.context_menu_table_name:
                self._clear_main_view()
            self._refresh_table_list()

    def _load_table_statistics(self, table_name):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        ctk.CTkButton(self.stats_frame, text=self.t("btn_pandas_stats"), 
                      command=lambda: self._show_pandas_stats(table_name),
                      fg_color="#2b825b", hover_color="#1e5c41").pack(pady=(10, 5))

        # Indicador de carregamento
        self.stats_loading_label = ctk.CTkLabel(self.stats_frame, text=self.t("calculating_stats"))
        self.stats_loading_label.pack(pady=(20, 5))
        
        self.stats_progress_bar = ctk.CTkProgressBar(self.stats_frame, width=300)
        self.stats_progress_bar.set(0)
        self.stats_progress_bar.pack(pady=(0, 10))

        # Botão de Cancelar
        self.cancel_stats = False
        self.stats_cancel_btn = ctk.CTkButton(self.stats_frame, text=self.t("cancel"), 
                                              fg_color="#D2042D", hover_color="#8A031E", 
                                              width=100, command=self._cancel_stats_process)
        self.stats_cancel_btn.pack(pady=(0, 20))
        
        try:
            # Iniciar cálculo em thread separada para não bloquear a UI com tabelas grandes
            threading.Thread(target=self._generate_stats_background, args=(table_name,), daemon=True).start()
        except Exception as e:
            self.stats_loading_label.destroy()
            self.stats_progress_bar.destroy()
            self.stats_cancel_btn.destroy()
            ctk.CTkLabel(self.stats_frame, text=self.t("stats_error").format(e)).pack(pady=20)

    def _cancel_stats_process(self):
        self.cancel_stats = True
        if hasattr(self, 'stats_loading_label'):
             self.stats_loading_label.configure(text=self.t("op_cancelled"))

    def _on_stats_cancelled(self):
        if hasattr(self, 'stats_loading_label'): self.stats_loading_label.destroy()
        if hasattr(self, 'stats_progress_bar'): self.stats_progress_bar.destroy()
        if hasattr(self, 'stats_cancel_btn'): self.stats_cancel_btn.destroy()
        ctk.CTkLabel(self.stats_frame, text=self.t("op_cancelled"), text_color="orange").pack(pady=20)

    def _generate_stats_background(self, table_name):
        """Executado numa thread separada."""
        if not self.db_manager:
            return

        try:
            columns = self.db_manager.get_columns(table_name)
            total_cols = len(columns)
            full_stats = {}
            
            # Obter row count total primeiro
            total_rows = self.db_manager.get_table_row_count(table_name)
            full_stats["__total_rows__"] = total_rows

            for i, col in enumerate(columns):
                if self.cancel_stats:
                    self.after(0, self._on_stats_cancelled)
                    return

                # Atualizar UI com o progresso
                progress = (i + 1) / total_cols if total_cols > 0 else 0
                self.after(0, lambda c=col, p=progress: self._update_stats_progress(c, p))
                
                # Calcular via SQL
                col_stats = self.db_manager.get_column_statistics(table_name, col)
                full_stats[col] = col_stats
            
            # Agendar atualização final da UI
            self.after(0, lambda: self._display_stats_results(table_name, full_stats))
            
        except Exception as e:
            self.after(0, lambda msg=str(e): self._show_stats_error(msg))

    def _update_stats_progress(self, col_name, progress):
        """Atualiza a barra de progresso e o texto na thread principal."""
        if hasattr(self, 'stats_loading_label'):
            self.stats_loading_label.configure(text=self.t("processing_column").format(col_name))
        if hasattr(self, 'stats_progress_bar'):
            self.stats_progress_bar.set(progress)

    def _show_stats_error(self, message):
        if hasattr(self, 'stats_loading_label'):
            self.stats_loading_label.destroy()
        if hasattr(self, 'stats_progress_bar'):
            self.stats_progress_bar.destroy()
        if hasattr(self, 'stats_cancel_btn'):
            self.stats_cancel_btn.destroy()
        ctk.CTkLabel(self.stats_frame, text=self.t("stats_error").format(message)).pack(pady=20)

    def _display_stats_results(self, table_name, stats_data):
        """Renderiza os resultados calculados."""
        if hasattr(self, 'stats_loading_label'):
            self.stats_loading_label.destroy()
        if hasattr(self, 'stats_progress_bar'):
            self.stats_progress_bar.destroy()
        if hasattr(self, 'stats_cancel_btn'):
            self.stats_cancel_btn.destroy()

        # Guardar cópia dos dados para exportação e adicionar botão
        self.current_stats_data = stats_data.copy()
        ctk.CTkButton(self.stats_frame, text=self.t("export_stats_btn"), 
                      command=lambda: self._export_stats_json(table_name),
                      fg_color="#2b825b", hover_color="#1e5c41").pack(pady=(0, 10))

        total_rows = stats_data.pop("__total_rows__", 0)
        
        summary = ctk.CTkTextbox(self.stats_frame, font=ctk.CTkFont(family="Consolas", size=13))
        summary.pack(fill="both", expand=True, padx=10, pady=10)

        lines = [
            f"{self.t('stats_table')} {table_name}",
            f"Total: {total_rows} {self.t('lines')}",
            "-" * 40,
            "",
        ]

        for col, data in stats_data.items():
            if not data:
                continue
                
            lines.append(f"[{col}]")
            lines.append(f"  {self.t('stats_filled')} {data.get('non_null_count', 0)}")
            lines.append(f"  {self.t('stats_empty')} {data.get('null_count', 0)}")
            lines.append(f"  {self.t('stats_unique')} {data.get('unique_count', 0)}")
            
            if data.get('min_value') is not None:
                lines.append(f"  {self.t('stats_min')} {data['min_value']}")
            if data.get('max_value') is not None:
                lines.append(f"  {self.t('stats_max')} {data['max_value']}")
            if data.get('avg_value') is not None:
                lines.append(f"  {self.t('stats_avg')} {round(data['avg_value'], 4)}")

            top_vals = data.get('top_values', [])
            if top_vals:
                lines.append(f"  {self.t('stats_top_values')}")
                for val, count in top_vals[:5]:
                    percentage = (count / total_rows * 100) if total_rows > 0 else 0
                    lines.append(f"    {str(val):<15} : {count} ({percentage:.1f}%)")
            else:
                lines.append(f"  {self.t('stats_top_values')} {self.t('stats_no_data')}")
            
            lines.append("")

        summary.insert("0.0", "\n".join(lines).strip())
        summary.configure(state="disabled")

    def _export_stats_json(self, table_name):
        if not hasattr(self, 'current_stats_data') or not self.current_stats_data:
            return
            
        filename = f"stats_{table_name}.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=filename,
            filetypes=[("JSON Files", "*.json")],
            title=self.t("export_stats_btn")
        )
        
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.current_stats_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo(self.t("success"), self.t("stats_saved").format(os.path.basename(path)))
            except Exception as e:
                messagebox.showerror(self.t("error"), self.t("export_error").format(e))

    def _load_autocomplete_data(self):
        self.autocomplete_list = [
            "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
            "CREATE", "TABLE", "DROP", "ALTER", "INDEX", "VIEW", "TRIGGER",
            "AND", "OR", "NOT", "NULL", "IS", "IN", "BETWEEN", "LIKE", "LIMIT", "OFFSET",
            "ORDER", "BY", "GROUP", "HAVING", "JOIN", "ON", "AS", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END"
        ]
        if self.db_manager:
            try:
                tables = self.db_manager.get_tables()
                self.autocomplete_list.extend(tables)
                for table in tables:
                    self.autocomplete_list.extend(self.db_manager.get_columns(table))
            except:
                pass
        
        self.autocomplete_list = sorted(list(set(self.autocomplete_list)), key=str.lower)

    def _on_key_release(self, event):
        self._update_syntax_highlighting(event)
        if event.keysym in ["Up", "Down", "Return", "Tab", "Escape", "Left", "Right", "Control_L", "Control_R", "Shift_L", "Shift_R"]:
            return
        self._show_autocomplete()

    def _show_autocomplete(self):
        text_widget = self.sql_input._textbox
        cursor_pos = text_widget.index("insert")
        line_start = text_widget.index("insert linestart")
        current_line = text_widget.get(line_start, cursor_pos)
        
        match = re.search(r"(\w+)$", current_line)
        if not match:
            self._hide_autocomplete()
            return
        
        word = match.group(1)
        if len(word) < 2:
             self._hide_autocomplete()
             return

        suggestions = [item for item in self.autocomplete_list if item.lower().startswith(word.lower())]
        if not suggestions:
            self._hide_autocomplete()
            return

        if not self.suggestion_window:
            self.suggestion_window = ctk.CTkToplevel(self)
            self.suggestion_window.wm_overrideredirect(True)
            self.suggestion_window.attributes('-topmost', True)
            self.suggestion_listbox = Listbox(self.suggestion_window, font=("Consolas", 12), bg="#2b2b2b", fg="white", selectbackground="#1f538d", borderwidth=0, highlightthickness=0)
            self.suggestion_listbox.pack(fill="both", expand=True)
        
        bbox = text_widget.bbox("insert")
        if bbox:
            x, y, w, h = bbox
            root_x = text_widget.winfo_rootx() + x
            root_y = text_widget.winfo_rooty() + y + h
            self.suggestion_window.geometry(f"200x{min(len(suggestions)*20, 150)}+{root_x}+{root_y}")

        self.suggestion_listbox.delete(0, "end")
        for s in suggestions:
            self.suggestion_listbox.insert("end", s)
        self.suggestion_listbox.select_set(0)
        self.current_prefix_len = len(word)

    def _confirm_autocomplete(self, event=None):
        if self.suggestion_window and self.suggestion_listbox.curselection():
            selection = self.suggestion_listbox.get(self.suggestion_listbox.curselection()[0])
            text_widget = self.sql_input._textbox
            text_widget.delete(f"insert-{self.current_prefix_len}c", "insert")
            text_widget.insert("insert", selection)
            self._hide_autocomplete()
            return "break"

    def _hide_autocomplete(self):
        if self.suggestion_window:
            self.suggestion_window.destroy()
            self.suggestion_window = None

    def _navigate_autocomplete(self, event):
        if self.suggestion_window:
            cur = self.suggestion_listbox.curselection()
            index = cur[0] if cur else 0
            
            if event.keysym == "Up": index = max(0, index - 1)
            elif event.keysym == "Down": index = min(self.suggestion_listbox.size() - 1, index + 1)
            
            self.suggestion_listbox.select_clear(0, "end")
            self.suggestion_listbox.select_set(index)
            self.suggestion_listbox.see(index)
            return "break"

    def _handle_return(self, event):
        if self.suggestion_window:
            return self._confirm_autocomplete()

    def _show_pandas_stats(self, table_name):
        if not self.db_manager:
            return
            
        report = self.db_manager.get_pandas_statistics(table_name)
        
        top = ctk.CTkToplevel(self)
        top.geometry("900x600")
        top.title(f"{self.t('title_pandas_stats')} - {table_name}")
        
        textbox = ctk.CTkTextbox(top, font=ctk.CTkFont(family="Consolas", size=13))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", report)
        textbox.configure(state="disabled")

    def run_custom_query(self):
        if not self.db_manager:
            messagebox.showwarning(self.t("warning"), self.t("load_db_first"))
            return
        query = self.sql_input.get("0.0", "end").strip()
        if not query:
            return
        self._clear_treeview(self.tree_sql)
        result = self.db_manager.execute_custom_query(query)
        if not self.query_history or query != self.query_history[0]:
            self.query_history.appendleft(query)
            self._save_history()
            self._update_history_panel()
        if isinstance(result, tuple):
            self._fill_treeview(self.tree_sql, result[0], result[1])
            self.export_btn.configure(state="normal")
        else:
            messagebox.showinfo(self.t("success"), result)

    def _fill_treeview(self, tree, cols, rows, sort_callback=None):
        tree["columns"] = cols
        for col in cols:
            if col == "rowid":
                tree.column(col, width=0, stretch=False)
                continue
            
            text = col
            if sort_callback and col == self.sort_column:
                text += " ▼" if self.sort_order == "DESC" else " ▲"

            if sort_callback:
                tree.heading(col, text=text, command=lambda c=col: sort_callback(c))
            else:
                tree.heading(col, text=text)
                
            tree.column(col, width=max(len(col) * 10, 100), minwidth=50)
        for row in rows:
            tree.insert("", "end", values=row)

    def _sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_column = column
            self.sort_order = "ASC"
        self._load_page_data(1)

    def _clear_treeview(self, tree):
        tree.delete(*tree.get_children())
        tree["columns"] = []

    def _filter_tables(self, event=None):
        term = self.search_entry.get().lower()
        for btn in self.current_table_buttons:
            if term in btn.cget("text").lower():
                btn.pack(fill="x", pady=2, padx=5)
            else:
                btn.pack_forget()

    def _update_history_panel(self):
        for btn in self.history_buttons:
            btn.destroy()
        self.history_buttons.clear()
        for query in self.query_history:
            item = ctk.CTkButton(self.history_frame, text=query.replace("\n", " ")[:30], anchor="w", fg_color="transparent", command=lambda q=query: self._reuse_query(q))
            item.pack(fill="x", pady=1, padx=2)
            self.history_buttons.append(item)

    def _update_favorites_panel(self):
        for btn in self.favorite_buttons:
            btn.destroy()
        self.favorite_buttons.clear()
        for query in self.favorite_queries:
            item = ctk.CTkButton(self.favorites_frame, text=query.replace("\n", " ")[:30], anchor="w", fg_color="transparent", command=lambda q=query: self._reuse_query(q))
            item.pack(fill="x", pady=1, padx=2)
            self.favorite_buttons.append(item)

    def _save_favorites(self):
        with open("favorites.json", "w", encoding="utf-8") as f:
            json.dump(self.favorite_queries, f, ensure_ascii=False, indent=4)

    def _save_settings(self):
        settings = {"theme_mode": self.theme_mode, "language": self.language}
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def _load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            theme_mode = settings.get("theme_mode", "Dark")
            self.language = settings.get("language", "pt")
            if theme_mode in {"Dark", "Light", "System"}:
                self.theme_mode = theme_mode
        except Exception:
            self.theme_mode = "Dark"

    def _load_favorites(self):
        if os.path.exists("favorites.json"):
            try:
                with open("favorites.json", "r", encoding="utf-8") as f:
                    self.favorite_queries = json.load(f)
                self._update_favorites_panel()
            except Exception:
                self.favorite_queries = []

    def _load_history(self):
        if os.path.exists("history.json"):
            try:
                with open("history.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.query_history = deque(data, maxlen=20)
                self._update_history_panel()
            except Exception:
                pass

    def _save_history(self):
        try:
            with open("history.json", "w", encoding="utf-8") as f:
                json.dump(list(self.query_history), f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _add_to_favorites(self, query: str):
        if query not in self.favorite_queries:
            self.favorite_queries.append(query)
            self._update_favorites_panel()
            self._save_favorites()

    def _remove_from_favorites(self, query: str):
        if query in self.favorite_queries:
            self.favorite_queries.remove(query)
            self._update_favorites_panel()
            self._save_favorites()

    def _reuse_query(self, query: str):
        self.sql_input.delete("0.0", "end")
        self.sql_input.insert("0.0", query)
        self._update_syntax_highlighting()

    def export_data(self):
        tab = self.tabview.get()
        target_tree = self.tree_sql if tab == self.t("tab_sql") else self.tree
        if not target_tree.get_children():
            messagebox.showwarning(self.t("warning"), self.t("no_data_export"))
            return
        base_name = self.current_table_name if (tab == self.t("tab_data") and self.current_table_name) else "export"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"{base_name}_export.csv",
            filetypes=[
                (self.t("export_csv_label"), "*.csv"),
                (self.t("export_json_label"), "*.json"),
            ],
            title=self.t("export_csv"),
        )
        if path:
            try:
                if path.lower().endswith(".json"):
                    columns = [c for c in target_tree["columns"] if c != "rowid"]
                    col_indices = [i for i, c in enumerate(target_tree["columns"]) if c != "rowid"]
                    data_to_export = []
                    for item in target_tree.get_children():
                        values = target_tree.item(item)["values"]
                        data_to_export.append({columns[j]: values[col_indices[j]] for j in range(len(columns))})
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data_to_export, f, ensure_ascii=False, indent=4)
                else:
                    cols = [c for c in target_tree["columns"] if c != "rowid"]
                    col_indices = [i for i, c in enumerate(target_tree["columns"]) if c != "rowid"]
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f, delimiter=";")
                        writer.writerow(cols)
                        for item in target_tree.get_children():
                            values = target_tree.item(item)["values"]
                            writer.writerow([values[i] for i in col_indices])
                messagebox.showinfo(self.t("success"), self.t("export_success"))
            except Exception as e:
                messagebox.showerror(self.t("error"), self.t("export_error").format(e))
