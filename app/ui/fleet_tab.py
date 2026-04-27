"""
ui/fleet_tab.py — Northshore Logistics Ltd
Fleet management: Vehicles, Drivers, and Warehouses with sub-tabs.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.fleet import (
    get_all_vehicles, add_vehicle, update_vehicle, delete_vehicle,
    get_all_drivers, update_driver_status, add_driver,
    get_all_warehouses, add_warehouse, update_warehouse
)
from app.models.reports import get_all_users
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows)

VEH_COLS = [
    ("id",      "ID",           40),
    ("reg",     "Registration", 100),
    ("make",    "Make",          80),
    ("model",   "Model",        120),
    ("cap",     "Cap (kg)",      80),
    ("status",  "Status",        90),
    ("lm",      "Last Maint.",  110),
    ("nm",      "Next Maint.",  110),
    ("wh",      "Warehouse",    140),
]

DRV_COLS = [
    ("id",     "ID",          40),
    ("name",   "Full Name",  160),
    ("lic",    "Licence No.",130),
    ("exp",    "Expiry",     100),
    ("status", "Status",      90),
    ("email",  "Email",      180),
]

WH_COLS = [
    ("id",   "ID",          40),
    ("name", "Name",       160),
    ("city", "City",       100),
    ("addr", "Address",    200),
    ("cap",  "Capacity",    90),
    ("mgr",  "Manager",    140),
]


class FleetTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚚  Fleet & Resources Management",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._veh_tab = VehiclePanel(nb)
        self._drv_tab = DriverPanel(nb)
        self._wh_tab  = WarehousePanel(nb)

        nb.add(self._veh_tab, text="  🚛  Vehicles  ")
        nb.add(self._drv_tab, text="  👤  Drivers   ")
        nb.add(self._wh_tab,  text="  🏭  Warehouses")

    def refresh(self):
        self._veh_tab.load_data()
        self._drv_tab.load_data()
        self._wh_tab.load_data()


# ── Vehicle Panel ─────────────────────────────────────────────────────────────
class VehiclePanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._wh_map = {}
        self._build()
        self.load_data()

    def _build(self):
        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=6)
        sess = get_session()
        if sess and sess.can("add_vehicle"):
            tk.Button(tb, text="＋ Add Vehicle", font=FONT_BTN,
                      bg=C["teal"], fg=C["white"], relief="flat",
                      command=self._open_add).pack(side="left", padx=4)
        if sess and sess.can("edit_vehicle"):
            tk.Button(tb, text="✏ Edit", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      command=self._open_edit).pack(side="left", padx=4)
        if sess and sess.can("delete_vehicle"):
            tk.Button(tb, text="🗑 Delete", font=FONT_BTN,
                      bg=C["red"], fg=C["white"], relief="flat",
                      command=self._delete).pack(side="left", padx=4)
        tk.Button(tb, text="↻", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.load_data).pack(side="left", padx=4)

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=6, pady=4)
        self._tree = make_tree(frm, VEH_COLS, height=16)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    def load_data(self):
        from app.models.fleet import get_all_warehouses
        whs = get_all_warehouses()
        self._wh_map = {w["warehouse_id"]: w["name"] for w in whs}
        self._rows   = get_all_vehicles()
        display = [
            (r["vehicle_id"], r["registration"], r["make"], r["model"],
             r["capacity_kg"], r["status"],
             r["last_maintenance"] or "—",
             r["next_maintenance"] or "—",
             r["warehouse_name"]   or "—")
            for r in self._rows
        ]
        insert_rows(self._tree, display)

    def _sel_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a vehicle.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add(self):
        VehicleForm(self, "Add Vehicle", on_save=lambda d: (add_vehicle(d), self.load_data()))

    def _open_edit(self):
        vid = self._sel_id()
        if vid is None:
            return
        row = next((r for r in self._rows if r["vehicle_id"] == vid), None)
        if row:
            VehicleForm(self, "Edit Vehicle", existing=row,
                        on_save=lambda d: (update_vehicle(vid, d), self.load_data()))

    def _delete(self):
        vid = self._sel_id()
        if vid and messagebox.askyesno("Confirm", "Delete this vehicle?"):
            delete_vehicle(vid)
            self.load_data()


# ── Driver Panel ──────────────────────────────────────────────────────────────
class DriverPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()
        self.load_data()

    def _build(self):
        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=6)
        sess = get_session()
        if sess and sess.can("add_driver"):
            tk.Button(tb, text="＋ Add Driver", font=FONT_BTN,
                      bg=C["teal"], fg=C["white"], relief="flat",
                      command=self._open_add).pack(side="left", padx=4)
        if sess and sess.can("edit_driver"):
            tk.Button(tb, text="✏ Update Status", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      command=self._update_status).pack(side="left", padx=4)
        tk.Button(tb, text="↻", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.load_data).pack(side="left", padx=4)

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=6, pady=4)
        self._tree = make_tree(frm, DRV_COLS, height=16)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    def load_data(self):
        self._rows = get_all_drivers()
        display = [
            (r["driver_id"], r["full_name"], r["license_number"],
             r["license_expiry"], r["status"], r["email"] or "—")
            for r in self._rows
        ]
        insert_rows(self._tree, display)

    def _sel_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a driver.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add(self):
        DriverForm(self, on_save=lambda ud, dd: (add_driver(ud, dd), self.load_data()))

    def _update_status(self):
        did = self._sel_id()
        if did is None:
            return
        statuses = ["available", "on_route", "off_duty", "suspended"]
        dialog   = StatusDialog(self, "Driver Status", statuses)
        self.wait_window(dialog)
        if dialog.result:
            update_driver_status(did, dialog.result)
            self.load_data()


# ── Warehouse Panel ───────────────────────────────────────────────────────────
class WarehousePanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()
        self.load_data()

    def _build(self):
        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=6)
        sess = get_session()
        if sess and sess.can("add_vehicle"):  # reuse perm
            tk.Button(tb, text="＋ Add Warehouse", font=FONT_BTN,
                      bg=C["teal"], fg=C["white"], relief="flat",
                      command=self._open_add).pack(side="left", padx=4)
            tk.Button(tb, text="✏ Edit", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      command=self._open_edit).pack(side="left", padx=4)
        tk.Button(tb, text="↻", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.load_data).pack(side="left", padx=4)

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=6, pady=4)
        self._tree = make_tree(frm, WH_COLS, height=16)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    def load_data(self):
        self._rows = get_all_warehouses()
        display = [
            (r["warehouse_id"], r["name"], r["city"], r["address"],
             r["capacity"], r["manager_name"] or "—")
            for r in self._rows
        ]
        insert_rows(self._tree, display)

    def _sel_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a warehouse.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add(self):
        WarehouseForm(self, "Add Warehouse",
                      on_save=lambda d: (add_warehouse(d), self.load_data()))

    def _open_edit(self):
        wid = self._sel_id()
        if wid is None:
            return
        row = next((r for r in self._rows if r["warehouse_id"] == wid), None)
        if row:
            WarehouseForm(self, "Edit Warehouse", existing=row,
                          on_save=lambda d: (update_warehouse(wid, d), self.load_data()))


# ── Forms ─────────────────────────────────────────────────────────────────────
class VehicleForm(tk.Toplevel):
    STATUSES = ["available", "in_use", "maintenance", "retired"]

    def __init__(self, parent, title, on_save, existing=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_save = on_save
        self._wh_map  = {}
        self._build()
        if existing:
            self._populate(existing)
        self._centre()

    def _build(self):
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text=self.title(), font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=14, pady=8).pack(fill="x")
        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack()

        fields = [("Registration *", "_reg"), ("Make *", "_make"),
                  ("Model *", "_model"), ("Capacity (kg)", "_cap"),
                  ("Last Maintenance (YYYY-MM-DD)", "_lm"),
                  ("Next Maintenance (YYYY-MM-DD)", "_nm")]
        self._vars = {}
        for i, (lbl, attr) in enumerate(fields):
            tk.Label(form, text=lbl, font=FONT_SMALL,
                     bg=C["off_white"]).grid(row=i, column=0, sticky="w", padx=4, pady=3)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=28).grid(
                row=i, column=1, sticky="ew", padx=4, pady=3)
            self._vars[attr] = var

        n = len(fields)
        tk.Label(form, text="Status", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=n, column=0, sticky="w", padx=4, pady=3)
        self._status_var = tk.StringVar(value="available")
        ttk.Combobox(form, textvariable=self._status_var,
                     values=self.STATUSES, state="readonly",
                     width=18).grid(row=n, column=1, sticky="w", padx=4, pady=3)

        tk.Label(form, text="Warehouse", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=n+1, column=0, sticky="w", padx=4, pady=3)
        self._wh_var = tk.StringVar()
        whs = get_all_warehouses()
        wh_lbls = []
        for w in whs:
            self._wh_map[w["name"]] = w["warehouse_id"]
            wh_lbls.append(w["name"])
        ttk.Combobox(form, textvariable=self._wh_var,
                     values=wh_lbls, state="readonly",
                     width=26).grid(row=n+1, column=1, sticky="w", padx=4, pady=3)

        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="💾 Save", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _populate(self, row):
        self._vars["_reg"].set(row["registration"])
        self._vars["_make"].set(row["make"])
        self._vars["_model"].set(row["model"])
        self._vars["_cap"].set(str(row["capacity_kg"]))
        self._vars["_lm"].set(row["last_maintenance"] or "")
        self._vars["_nm"].set(row["next_maintenance"] or "")
        self._status_var.set(row["status"])
        for name, wid in self._wh_map.items():
            if wid == row["warehouse_id"]:
                self._wh_var.set(name)
                break

    def _submit(self):
        if not self._vars["_reg"].get().strip():
            messagebox.showwarning("Validation", "Registration is required.", parent=self)
            return
        data = {
            "registration":   self._vars["_reg"].get().strip().upper(),
            "make":           self._vars["_make"].get().strip(),
            "model":          self._vars["_model"].get().strip(),
            "capacity_kg":    self._vars["_cap"].get() or "0",
            "last_maintenance":self._vars["_lm"].get().strip(),
            "next_maintenance":self._vars["_nm"].get().strip(),
            "status":         self._status_var.get(),
            "warehouse_id":   self._wh_map.get(self._wh_var.get()),
        }
        self._on_save(data)
        self.destroy()

    def _centre(self):
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")


class DriverForm(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Add New Driver")
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_save = on_save
        self._build()
        self._centre()

    def _build(self):
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text="Add New Driver", font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=14, pady=8).pack(fill="x")

        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack()

        def row(lbl, r):
            tk.Label(form, text=lbl, font=FONT_SMALL,
                     bg=C["off_white"]).grid(row=r, column=0, sticky="w", pady=3, padx=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=28).grid(
                row=r, column=1, sticky="ew", padx=4, pady=3)
            return var

        tk.Label(form, text="— User Account —", font=FONT_HEAD,
                 bg=C["off_white"], fg=C["navy"]).grid(
            row=0, column=0, columnspan=2, pady=(0, 6))
        self._uname  = row("Username *",   1)
        self._pwd    = row("Password *",   2)
        self._fname  = row("Full Name *",  3)
        self._email  = row("Email",        4)
        self._phone  = row("Phone",        5)

        tk.Label(form, text="— Driver Details —", font=FONT_HEAD,
                 bg=C["off_white"], fg=C["navy"]).grid(
            row=6, column=0, columnspan=2, pady=(10, 6))
        self._lic    = row("Licence No. *",7)
        self._exp    = row("Expiry (YYYY-MM-DD) *", 8)
        self._addr   = row("Address",      9)

        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="💾 Save", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _submit(self):
        if not self._uname.get().strip() or not self._pwd.get():
            messagebox.showwarning("Validation", "Username and Password are required.", parent=self)
            return
        user_data   = {"username": self._uname.get().strip(),
                       "password": self._pwd.get(),
                       "full_name":self._fname.get().strip(),
                       "email":    self._email.get().strip(),
                       "phone":    self._phone.get().strip()}
        driver_data = {"license_number": self._lic.get().strip(),
                       "license_expiry": self._exp.get().strip(),
                       "address":        self._addr.get().strip()}
        self._on_save(user_data, driver_data)
        self.destroy()

    def _centre(self):
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")


class WarehouseForm(tk.Toplevel):
    def __init__(self, parent, title, on_save, existing=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_save  = on_save
        self._mgr_map  = {}
        self._build()
        if existing:
            self._populate(existing)
        self._centre()

    def _build(self):
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text=self.title(), font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=14, pady=8).pack(fill="x")
        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack()

        def r(lbl, row_n):
            tk.Label(form, text=lbl, font=FONT_SMALL,
                     bg=C["off_white"]).grid(row=row_n, column=0, sticky="w", pady=3, padx=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=28).grid(
                row=row_n, column=1, sticky="ew", padx=4, pady=3)
            return var

        self._name    = r("Name *",    0)
        self._address = r("Address *", 1)
        self._city    = r("City *",    2)
        self._post    = r("Postcode",  3)
        self._cap     = r("Capacity",  4)

        tk.Label(form, text="Manager", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=5, column=0, sticky="w", pady=3, padx=4)
        self._mgr_var = tk.StringVar()
        users = [u for u in get_all_users() if u["role"] in ("admin", "manager")]
        mgr_labels = ["(none)"]
        for u in users:
            self._mgr_map[u["full_name"]] = u["user_id"]
            mgr_labels.append(u["full_name"])
        ttk.Combobox(form, textvariable=self._mgr_var,
                     values=mgr_labels, state="readonly",
                     width=26).grid(row=5, column=1, sticky="w", padx=4, pady=3)
        self._mgr_var.set("(none)")

        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="💾 Save", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _populate(self, row):
        self._name.set(row["name"])
        self._address.set(row["address"])
        self._city.set(row["city"])
        self._post.set(row["postcode"] or "")
        self._cap.set(str(row["capacity"]))
        for name, mid in self._mgr_map.items():
            if mid == row["manager_id"]:
                self._mgr_var.set(name)
                break

    def _submit(self):
        if not self._name.get().strip():
            messagebox.showwarning("Validation", "Name is required.", parent=self)
            return
        data = {
            "name":       self._name.get().strip(),
            "address":    self._address.get().strip(),
            "city":       self._city.get().strip(),
            "postcode":   self._post.get().strip(),
            "capacity":   self._cap.get() or "0",
            "manager_id": self._mgr_map.get(self._mgr_var.get()),
        }
        self._on_save(data)
        self.destroy()

    def _centre(self):
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")


class StatusDialog(tk.Toplevel):
    def __init__(self, parent, title, options):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self.result = None
        self._var = tk.StringVar(value=options[0])
        tk.Label(self, text="Select new status:", font=FONT_BODY,
                 bg=C["off_white"], padx=20, pady=10).pack()
        for opt in options:
            tk.Radiobutton(self, text=opt.replace("_", " ").capitalize(),
                           variable=self._var, value=opt,
                           bg=C["off_white"], font=FONT_BODY).pack(anchor="w", padx=30)
        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="Confirm", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self._confirm).pack(side="left", padx=8)
        tk.Button(btn_row, text="Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _confirm(self):
        self.result = self._var.get()
        self.destroy()
