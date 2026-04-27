"""
ui/main_window.py — Northshore Logistics Ltd
Main application window: tab container, menu bar, status bar.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.auth import get_session, logout
from app.ui.styles import C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL, apply_theme


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Northshore Logistics Ltd — Database Management System")
        self.state("zoomed") if self._is_windows() else self.geometry("1280x800")
        self.configure(bg=C["navy"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        apply_theme(self)
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["navy"], pady=8)
        hdr.pack(fill="x")

        # Logo / title
        left = tk.Frame(hdr, bg=C["navy"])
        left.pack(side="left", padx=16)
        tk.Label(left, text="🚚", font=("Helvetica", 26),
                 bg=C["navy"], fg=C["teal"]).pack(side="left")
        title_frame = tk.Frame(left, bg=C["navy"])
        title_frame.pack(side="left", padx=8)
        tk.Label(title_frame, text="NORTHSHORE LOGISTICS LTD",
                 font=("Helvetica", 14, "bold"),
                 fg=C["white"], bg=C["navy"]).pack(anchor="w")
        tk.Label(title_frame, text="Database Management System — CPS4004",
                 font=("Helvetica", 9),
                 fg=C["mid_grey"], bg=C["navy"]).pack(anchor="w")

        # Right: user info + logout
        right = tk.Frame(hdr, bg=C["navy"])
        right.pack(side="right", padx=16)
        sess = get_session()
        if sess:
            tk.Label(right,
                     text=f"👤  {sess.full_name}   |   {sess.role.upper()}",
                     font=FONT_SMALL, fg=C["light_grey"],
                     bg=C["navy"]).pack(side="left", padx=8)
        tk.Button(right, text="  Logout  ", font=FONT_BTN,
                  bg=C["red"], fg=C["white"], relief="flat",
                  activebackground="#c0392b", activeforeground=C["white"],
                  cursor="hand2", padx=6, pady=3,
                  command=self._logout).pack(side="left")

        # Divider
        tk.Frame(self, bg=C["teal"], height=3).pack(fill="x")

    def _build_notebook(self):
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        sess = get_session()

        # ── Dashboard (all roles) ─────────────────────────────────────────────
        from app.ui.dashboard_tab import DashboardTab
        self._dash = DashboardTab(self._nb)
        self._nb.add(self._dash, text="  🏠  Dashboard  ")

        # ── Shipments (all except driver) ─────────────────────────────────────
        if sess and sess.can("view_shipments"):
            from app.ui.shipments_tab import ShipmentsTab
            self._shp = ShipmentsTab(self._nb)
            self._nb.add(self._shp, text="  📦  Shipments  ")

        # ── Inventory ─────────────────────────────────────────────────────────
        if sess and sess.can("view_inventory"):
            from app.ui.inventory_tab import InventoryTab
            self._inv = InventoryTab(self._nb)
            self._nb.add(self._inv, text="  📋  Inventory  ")

        # ── Fleet ─────────────────────────────────────────────────────────────
        if sess and sess.can("view_vehicles"):
            from app.ui.fleet_tab import FleetTab
            self._fleet = FleetTab(self._nb)
            self._nb.add(self._fleet, text="  🚛  Fleet  ")

        # ── Incidents ─────────────────────────────────────────────────────────
        if sess and sess.can("view_incidents"):
            from app.ui.incidents_tab import IncidentsTab
            self._inc = IncidentsTab(self._nb)
            self._nb.add(self._inc, text="  ⚠  Incidents  ")

        # ── Reports ───────────────────────────────────────────────────────────
        if sess and sess.can("view_reports"):
            from app.ui.reports_tab import ReportsTab
            self._rep = ReportsTab(self._nb)
            self._nb.add(self._rep, text="  📊  Reports  ")

        # ── Admin (admin only) ────────────────────────────────────────────────
        if sess and sess.can("view_users"):
            from app.ui.admin_tab import AdminTab
            self._adm = AdminTab(self._nb)
            self._nb.add(self._adm, text="  ⚙  Admin  ")

        # Refresh dashboard on tab focus
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C["navy_mid"], pady=3)
        bar.pack(fill="x", side="bottom")
        sess = get_session()
        role_txt = f"Role: {sess.role.capitalize()}" if sess else ""
        tk.Label(bar, text=f"  Northshore Logistics Ltd  |  CPS4004  |  {role_txt}",
                 font=("Helvetica", 8), fg=C["light_grey"],
                 bg=C["navy_mid"]).pack(side="left", padx=8)
        self._clock_var = tk.StringVar()
        tk.Label(bar, textvariable=self._clock_var,
                 font=("Helvetica", 8), fg=C["light_grey"],
                 bg=C["navy_mid"]).pack(side="right", padx=8)
        self._tick_clock()

    # ── Behaviour ─────────────────────────────────────────────────────────────
    def _on_tab_change(self, _):
        try:
            self._dash.refresh()
        except Exception:
            pass

    def _tick_clock(self):
        from datetime import datetime
        self._clock_var.set(datetime.now().strftime("  %A %d %B %Y   %H:%M:%S  "))
        self.after(1000, self._tick_clock)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            logout()
            self.destroy()
            _restart_app()

    def _on_close(self):
        if messagebox.askyesno("Exit",
                               "Are you sure you want to exit Northshore Logistics?"):
            logout()
            self.destroy()

    @staticmethod
    def _is_windows() -> bool:
        import sys
        return sys.platform.startswith("win")


def _restart_app():
    """Re-launch login → main window cycle."""
    from app.ui.login_window import LoginWindow

    root = tk.Tk()
    root.withdraw()

    def on_login_success():
        root.destroy()
        app = MainWindow()
        app.mainloop()

    LoginWindow(root, on_success=on_login_success)
    root.mainloop()
