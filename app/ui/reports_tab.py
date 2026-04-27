"""
ui/reports_tab.py — Northshore Logistics Ltd
Reports dashboard: pandas-powered reports, CSV export, audit log viewer.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from app.models.reports import (
    report_shipment_status, report_vehicle_utilisation,
    report_warehouse_activity, report_driver_performance,
    export_report_csv, get_audit_logs
)
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows)


class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._current_df = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📊  Reports & Analytics",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._shp_panel  = ReportPanel(nb, "Shipment Status",
                                        report_shipment_status)
        self._veh_panel  = ReportPanel(nb, "Vehicle Utilisation",
                                        report_vehicle_utilisation)
        self._wh_panel   = ReportPanel(nb, "Warehouse Activity",
                                        report_warehouse_activity)
        self._drv_panel  = ReportPanel(nb, "Driver Performance",
                                        report_driver_performance)
        self._audit_panel = AuditLogPanel(nb)

        nb.add(self._shp_panel,   text="  📦 Shipments  ")
        nb.add(self._veh_panel,   text="  🚛 Vehicles   ")
        nb.add(self._wh_panel,    text="  🏭 Warehouses ")
        nb.add(self._drv_panel,   text="  👤 Drivers    ")
        nb.add(self._audit_panel, text="  🔍 Audit Log  ")


class ReportPanel(ttk.Frame):
    def __init__(self, parent, name: str, query_fn):
        super().__init__(parent)
        self._name     = name
        self._query_fn = query_fn
        self._df       = None
        self._build()

    def _build(self):
        tb = tk.Frame(self, bg=C["off_white"], pady=8)
        tb.pack(fill="x", padx=8)
        tk.Label(tb, text=f"Report: {self._name}", font=FONT_HEAD,
                 fg=C["navy"], bg=C["off_white"]).pack(side="left", padx=4)
        tk.Button(tb, text="🔄  Run Report", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=10, pady=4,
                  command=self._run).pack(side="right", padx=4)

        sess = get_session()
        if sess and sess.can("export_reports"):
            tk.Button(tb, text="⬇ Export CSV", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._export).pack(side="right", padx=4)

        # Placeholder treeview — columns built after first run
        self._frm = ttk.Frame(self)
        self._frm.pack(fill="both", expand=True, padx=8, pady=4)

        self._status_var = tk.StringVar(value="Click 'Run Report' to load data.")
        tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                 bg=C["off_white"], fg=C["mid_grey"], anchor="w").pack(
            fill="x", padx=14, pady=2)

        self._tree = None

    def _run(self):
        try:
            self._df = self._query_fn()
        except Exception as e:
            messagebox.showerror("Report Error", str(e))
            return

        # Rebuild treeview to match columns
        for w in self._frm.winfo_children():
            w.destroy()

        cols = [(c, c.replace("_", " ").title(), 130) for c in self._df.columns]
        self._tree = make_tree(self._frm, cols, height=18)
        vsb = ttk.Scrollbar(self._frm, orient="vertical",  command=self._tree.yview)
        hsb = ttk.Scrollbar(self._frm, orient="horizontal",command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        rows = [tuple(str(v) if pd.notna(v) else "—" for v in r)
                for r in self._df.itertuples(index=False)]
        insert_rows(self._tree, rows)
        self._status_var.set(f"{len(rows)} record(s)  |  {len(self._df.columns)} column(s)")

    def _export(self):
        if self._df is None or self._df.empty:
            messagebox.showinfo("Export", "Please run the report first.")
            return
        try:
            path = export_report_csv(self._df, self._name.lower().replace(" ", "_"))
            messagebox.showinfo("Export Complete",
                                f"Report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


class AuditLogPanel(ttk.Frame):
    COLUMNS = [
        ("log_id",     "ID",          50),
        ("username",   "User",        110),
        ("action",     "Action",      150),
        ("table_name", "Table",       100),
        ("record_id",  "Record ID",    80),
        ("description","Description", 280),
        ("timestamp",  "Timestamp",   140),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()

    def _build(self):
        tb = tk.Frame(self, bg=C["off_white"], pady=8)
        tb.pack(fill="x", padx=8)
        tk.Label(tb, text="Audit Log (last 200 entries)", font=FONT_HEAD,
                 fg=C["navy"], bg=C["off_white"]).pack(side="left", padx=4)

        tk.Label(tb, text="Search:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=(20, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        ttk.Entry(tb, textvariable=self._search_var, width=22).pack(side="left", padx=4)

        tk.Button(tb, text="🔄 Load", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=10, pady=4,
                  command=self.load_data).pack(side="right", padx=4)

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=8, pady=4)
        self._tree = make_tree(frm, self.COLUMNS, height=18)
        vsb = ttk.Scrollbar(frm, orient="vertical",  command=self._tree.yview)
        hsb = ttk.Scrollbar(frm, orient="horizontal",command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        self._status_var = tk.StringVar(value="Click 'Load' to view audit entries.")
        tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                 bg=C["off_white"], fg=C["mid_grey"], anchor="w").pack(
            fill="x", padx=14, pady=2)

    def load_data(self):
        self._rows = get_audit_logs(200)
        self._filter()

    def _filter(self):
        term = self._search_var.get().lower()
        visible = [r for r in self._rows
                   if not term or any(term in str(v).lower() for v in r)]
        display = [
            (r["log_id"], r["username"] or "—", r["action"],
             r["table_name"] or "—",
             r["record_id"] or "—",
             r["description"] or "—",
             r["timestamp"][:16])
            for r in visible
        ]
        insert_rows(self._tree, display)
        self._status_var.set(f"{len(visible)} log entries shown")
