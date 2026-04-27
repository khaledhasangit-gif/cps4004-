"""
ui/dashboard_tab.py — Northshore Logistics Ltd
Dashboard with KPI stat cards and summary panels.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk
from app.models.reports import get_dashboard_stats
from app.auth import get_session
from app.ui.styles import C, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_SMALL, FONT_STAT


class DashboardTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["navy"], padx=20, pady=14)
        hdr.pack(fill="x")
        sess = get_session()
        name = sess.full_name if sess else "User"
        role = sess.role.capitalize() if sess else ""
        tk.Label(hdr, text="📊  Dashboard Overview",
                 font=FONT_TITLE, fg=C["teal"], bg=C["navy"]).pack(side="left")
        tk.Label(hdr, text=f"Welcome, {name}  ({role})",
                 font=FONT_BODY, fg=C["light_grey"], bg=C["navy"]).pack(side="right", padx=10)

        # ── Scrollable body ───────────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=C["off_white"], highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=C["off_white"])
        canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._body = body
        self.refresh()

    def refresh(self):
        for w in self._body.winfo_children():
            w.destroy()

        stats = get_dashboard_stats()

        # ── Section: Shipments ────────────────────────────────────────────────
        self._section_label(self._body, "📦  Shipment Summary")
        shp_frame = tk.Frame(self._body, bg=C["off_white"])
        shp_frame.pack(fill="x", padx=20, pady=(0, 10))

        cards_shp = [
            ("Total Shipments",  stats["total_shipments"],   C["navy"]),
            ("In Transit",       stats["shipments_in_transit"], C["blue_lt"]),
            ("Delivered",        stats["shipments_delivered"],  C["green"]),
            ("Pending",          stats["shipments_pending"],    C["amber"]),
            ("Delayed",          stats["shipments_delayed"],    C["red"]),
            ("Returned",         stats["shipments_returned"],   C["mid_grey"]),
        ]
        for i, (label, val, colour) in enumerate(cards_shp):
            self._stat_card(shp_frame, label, val, colour, col=i)

        # ── Section: Operations ───────────────────────────────────────────────
        self._section_label(self._body, "🔧  Operational Status")
        ops_frame = tk.Frame(self._body, bg=C["off_white"])
        ops_frame.pack(fill="x", padx=20, pady=(0, 10))

        cards_ops = [
            ("Available Vehicles", stats["vehicles_available"],  C["teal"]),
            ("Available Drivers",  stats["drivers_available"],   C["teal"]),
            ("Low Stock Items",    stats["low_stock_count"],      C["amber"]),
            ("Open Incidents",     stats["open_incidents"],       C["red"]),
        ]
        for i, (label, val, colour) in enumerate(cards_ops):
            self._stat_card(ops_frame, label, val, colour, col=i)

        # ── Section: Financials ───────────────────────────────────────────────
        self._section_label(self._body, "💷  Financial Summary")
        fin_frame = tk.Frame(self._body, bg=C["off_white"])
        fin_frame.pack(fill="x", padx=20, pady=(0, 20))

        cards_fin = [
            ("Total Revenue",   f"£{stats['total_revenue']:,.2f}",  C["green"]),
            ("Overdue Amount",  f"£{stats['overdue_amount']:,.2f}",  C["red"]),
        ]
        for i, (label, val, colour) in enumerate(cards_fin):
            self._stat_card(fin_frame, label, val, colour, col=i, is_str=True)

        # ── Quick tip ─────────────────────────────────────────────────────────
        tip = tk.Frame(self._body, bg=C["navy_lt"], padx=20, pady=12)
        tip.pack(fill="x", padx=20, pady=(0, 20))
        tk.Label(tip, text="ℹ  Use the tabs above to manage Shipments, Inventory, "
                           "Fleet, Drivers, Incidents and Reports.",
                 font=FONT_SMALL, fg=C["white"], bg=C["navy_lt"],
                 wraplength=800, justify="left").pack(anchor="w")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _section_label(self, parent, text: str):
        f = tk.Frame(parent, bg=C["navy"], height=2)
        f.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(parent, text=text,
                 font=FONT_HEAD, fg=C["navy"], bg=C["off_white"]).pack(
            anchor="w", padx=24)

    def _stat_card(self, parent, label: str, value, colour: str,
                   col: int = 0, is_str: bool = False):
        card = tk.Frame(parent, bg=C["white"], bd=0, relief="flat",
                        highlightbackground=colour, highlightthickness=2,
                        padx=20, pady=16)
        card.grid(row=0, column=col, padx=10, pady=8, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        # Coloured top bar
        bar = tk.Frame(card, bg=colour, height=4)
        bar.pack(fill="x")

        val_str = str(value) if is_str else str(value)
        tk.Label(card, text=val_str,
                 font=FONT_STAT, fg=colour, bg=C["white"]).pack(pady=(10, 2))
        tk.Label(card, text=label,
                 font=FONT_SMALL, fg=C["mid_grey"], bg=C["white"]).pack()
