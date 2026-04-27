"""
ui/admin_tab.py — Northshore Logistics Ltd
Admin-only panel: user management, system info.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.reports import get_all_users, toggle_user_active
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows)

USER_COLS = [
    ("id",       "ID",        45),
    ("username", "Username", 120),
    ("name",     "Full Name",180),
    ("role",     "Role",      90),
    ("email",    "Email",    200),
    ("active",   "Active",    60),
    ("created",  "Created",  130),
]


class AdminTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()
        self.load_data()

    def _build(self):
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Administration — User Management",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        # Info banner
        info = tk.Frame(self, bg=C["navy_lt"], padx=16, pady=8)
        info.pack(fill="x")
        tk.Label(info, text="⚠  This panel is restricted to Administrators only.",
                 font=FONT_SMALL, fg=C["white"], bg=C["navy_lt"]).pack(anchor="w")

        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=10)
        tk.Button(tb, text="🔄 Refresh", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self.load_data).pack(side="left", padx=4)
        tk.Button(tb, text="✏ Toggle Active", font=FONT_BTN,
                  bg=C["amber"], fg=C["white"], relief="flat",
                  command=self._toggle).pack(side="left", padx=4)

        # User treeview
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=6)
        self._tree = make_tree(frm, USER_COLS, height=16)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # System info
        sys_frame = tk.Frame(self, bg=C["white"], padx=16, pady=12)
        sys_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(sys_frame, text="System Information", font=FONT_HEAD,
                 fg=C["navy"], bg=C["white"]).pack(anchor="w")
        import sys, sqlite3
        info_text = (
            f"Python version : {sys.version.split()[0]}\n"
            f"SQLite version : {sqlite3.sqlite_version}\n"
            f"Database path  : northshore.db\n"
            f"Allowed libs   : sqlite3, pandas, datetime, logging, hashlib, secrets, tkinter"
        )
        tk.Label(sys_frame, text=info_text, font=FONT_SMALL,
                 fg=C["dark_grey"], bg=C["white"], justify="left").pack(anchor="w", pady=4)

    def load_data(self):
        self._rows = get_all_users()
        display = [
            (r["user_id"], r["username"], r["full_name"], r["role"],
             r["email"] or "—", "✔" if r["is_active"] else "✘",
             r["created_at"][:10])
            for r in self._rows
        ]
        insert_rows(self._tree, display)

    def _toggle(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a user first.")
            return
        uid      = self._tree.item(sel[0])["values"][0]
        username = self._tree.item(sel[0])["values"][1]
        sess     = get_session()
        if sess and sess.user_id == uid:
            messagebox.showwarning("Warning", "You cannot deactivate your own account.")
            return
        if messagebox.askyesno("Confirm",
                               f"Toggle active status for '{username}'?"):
            toggle_user_active(uid)
            self.load_data()
