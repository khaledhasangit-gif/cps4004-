"""
ui/shipments_tab.py — Northshore Logistics Ltd
Full CRUD interface for Shipments and Deliveries.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.shipments import (
    get_all_shipments, add_shipment, update_shipment, delete_shipment,
    get_shipment_by_id, get_drivers_available,
    get_vehicles_available, get_warehouses
)
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows, status_badge_colour)

STATUS_OPTIONS  = ["pending", "in_transit", "delivered", "delayed", "returned"]
PAYMENT_OPTIONS = ["pending", "paid", "overdue"]

COLUMNS = [
    ("ref",       "Ref",           110),
    ("order",     "Order No.",      90),
    ("sender",    "Sender",        140),
    ("receiver",  "Receiver",      140),
    ("items",     "Items",         160),
    ("weight",    "Kg",             55),
    ("cost",      "Cost £",         70),
    ("pay",       "Payment",        80),
    ("status",    "Status",         90),
    ("warehouse", "Warehouse",     120),
    ("driver",    "Driver",        120),
    ("created",   "Created",       130),
]


class ShipmentsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()
        self.load_data()

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # Header bar
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📦  Shipment Management",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        # Toolbar
        toolbar = tk.Frame(self, bg=C["off_white"], pady=6)
        toolbar.pack(fill="x", padx=10)

        # Filter
        tk.Label(toolbar, text="Filter by status:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=(4, 2))
        self._filter_var = tk.StringVar(value="All")
        filter_cb = ttk.Combobox(toolbar, textvariable=self._filter_var,
                                  values=["All"] + STATUS_OPTIONS,
                                  state="readonly", width=14)
        filter_cb.pack(side="left", padx=4)
        filter_cb.bind("<<ComboboxSelected>>", lambda _: self.load_data())

        # Search
        tk.Label(toolbar, text="Search:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=(14, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_search())
        ttk.Entry(toolbar, textvariable=self._search_var, width=20).pack(side="left", padx=4)

        # Buttons — right side
        sess = get_session()
        if sess and sess.can("add_shipment"):
            tk.Button(toolbar, text="＋  New Shipment", font=FONT_BTN,
                      bg=C["teal"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._open_add).pack(side="right", padx=4)
        if sess and sess.can("edit_shipment"):
            tk.Button(toolbar, text="✏  Edit", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._open_edit).pack(side="right", padx=4)
        if sess and sess.can("delete_shipment"):
            tk.Button(toolbar, text="🗑  Delete", font=FONT_BTN,
                      bg=C["red"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._delete).pack(side="right", padx=4)
        tk.Button(toolbar, text="↻  Refresh", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=8, pady=4,
                  command=self.load_data).pack(side="right", padx=4)

        # Treeview
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=6)
        self._tree = make_tree(frame, COLUMNS, height=18)
        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda _: self._open_edit())

        # Status bar
        self._status_var = tk.StringVar(value="Loading …")
        tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                 bg=C["off_white"], fg=C["mid_grey"], anchor="w").pack(
            fill="x", padx=14, pady=2)

    # ── Data ─────────────────────────────────────────────────────────────────
    def load_data(self):
        flt = self._filter_var.get()
        self._rows = get_all_shipments(None if flt == "All" else flt)
        self._apply_search()

    def _apply_search(self):
        term = self._search_var.get().lower()
        visible = [
            r for r in self._rows
            if not term or any(term in str(v).lower() for v in r)
        ]
        display = [
            (r["shipment_ref"], r["order_number"],
             r["sender_name"], r["receiver_name"],
             r["item_description"], f'{r["weight_kg"]:.1f}',
             f'£{(r["transport_cost"]+r["surcharge"]):.2f}',
             r["payment_status"], r["status"],
             r["warehouse_name"] or "—",
             r["driver_name"]    or "—",
             r["created_at"][:16])
            for r in visible
        ]
        insert_rows(self._tree, display)
        self._status_var.set(f"{len(visible)} record(s) shown")

    def _selected_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a shipment first.")
            return None
        ref = self._tree.item(sel[0])["values"][0]
        for r in self._rows:
            if r["shipment_ref"] == ref:
                return r["shipment_id"]
        return None

    # ── CRUD dialogs ─────────────────────────────────────────────────────────
    def _open_add(self):
        ShipmentForm(self, title="New Shipment", on_save=self._save_new)

    def _open_edit(self):
        sid = self._selected_id()
        if sid is None:
            return
        data = get_shipment_by_id(sid)
        ShipmentForm(self, title="Edit Shipment", existing=data,
                     on_save=lambda d: self._save_edit(sid, d))

    def _save_new(self, data: dict):
        try:
            add_shipment(data)
            self.load_data()
            messagebox.showinfo("Success", "Shipment added successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_edit(self, sid: int, data: dict):
        try:
            update_shipment(sid, data)
            self.load_data()
            messagebox.showinfo("Success", "Shipment updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        sid = self._selected_id()
        if sid is None:
            return
        if messagebox.askyesno("Confirm Delete",
                               "Permanently delete this shipment?"):
            delete_shipment(sid)
            self.load_data()


# ── Shipment Form Dialog ──────────────────────────────────────────────────────
class ShipmentForm(tk.Toplevel):
    def __init__(self, parent, title: str, on_save, existing=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_save = on_save
        self._existing = existing
        self._driver_map  = {}
        self._vehicle_map = {}
        self._wh_map      = {}
        self._build()
        if existing:
            self._populate(existing)
        self._centre()

    def _build(self):
        # Title
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text=self.title(), font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=16, pady=8).pack(fill="x")

        # Form grid
        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack(fill="both")

        def lbl(text, r, c=0):
            tk.Label(form, text=text, font=FONT_SMALL,
                     fg=C["dark_grey"], bg=C["off_white"]).grid(
                row=r, column=c, sticky="w", pady=3, padx=4)

        def ent(r, c=1, width=30):
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=width).grid(
                row=r, column=c, sticky="ew", padx=4, pady=3)
            return var

        lbl("Order Number *",   0);  self._order     = ent(0)
        lbl("Sender Name *",    1);  self._sname     = ent(1)
        lbl("Sender Address *", 2);  self._saddr     = ent(2)
        lbl("Receiver Name *",  3);  self._rname     = ent(3)
        lbl("Receiver Address*",4);  self._raddr     = ent(4)
        lbl("Item Description*",5);  self._items     = ent(5)
        lbl("Weight (kg)",      6);  self._weight    = ent(6, width=12)
        lbl("Transport Cost £", 7);  self._cost      = ent(7, width=12)
        lbl("Surcharge £",      8);  self._surcharge = ent(8, width=12)

        # Status combos
        lbl("Payment Status",   9)
        self._pay_var = tk.StringVar(value="pending")
        ttk.Combobox(form, textvariable=self._pay_var,
                     values=PAYMENT_OPTIONS, state="readonly",
                     width=18).grid(row=9, column=1, sticky="w", padx=4, pady=3)

        lbl("Shipment Status",  10)
        self._status_var = tk.StringVar(value="pending")
        ttk.Combobox(form, textvariable=self._status_var,
                     values=STATUS_OPTIONS, state="readonly",
                     width=18).grid(row=10, column=1, sticky="w", padx=4, pady=3)

        # Warehouse
        lbl("Warehouse",        11)
        self._wh_var = tk.StringVar()
        warehouses = get_warehouses()
        wh_labels  = []
        for w in warehouses:
            label = w["name"]
            self._wh_map[label] = w["warehouse_id"]
            wh_labels.append(label)
        ttk.Combobox(form, textvariable=self._wh_var,
                     values=wh_labels, state="readonly",
                     width=28).grid(row=11, column=1, sticky="w", padx=4, pady=3)

        # Driver
        lbl("Driver",           12)
        self._drv_var = tk.StringVar()
        drivers   = get_drivers_available()
        drv_labels= ["(none)"]
        for d in drivers:
            label = d["full_name"]
            self._driver_map[label] = d["driver_id"]
            drv_labels.append(label)
        ttk.Combobox(form, textvariable=self._drv_var,
                     values=drv_labels, state="readonly",
                     width=28).grid(row=12, column=1, sticky="w", padx=4, pady=3)
        self._drv_var.set("(none)")

        # Vehicle
        lbl("Vehicle",          13)
        self._veh_var = tk.StringVar()
        vehicles  = get_vehicles_available()
        veh_labels= ["(none)"]
        for v in vehicles:
            label = v["label"]
            self._vehicle_map[label] = v["vehicle_id"]
            veh_labels.append(label)
        ttk.Combobox(form, textvariable=self._veh_var,
                     values=veh_labels, state="readonly",
                     width=28).grid(row=13, column=1, sticky="w", padx=4, pady=3)
        self._veh_var.set("(none)")

        lbl("Scheduled Date",   14)
        self._sched = ent(14, width=16)
        tk.Label(form, text="(YYYY-MM-DD)", font=("Helvetica", 8),
                 fg=C["mid_grey"], bg=C["off_white"]).grid(
            row=14, column=2, sticky="w")

        lbl("Route Details",    15)
        self._route = ent(15)

        # Buttons
        btn_row = tk.Frame(self, bg=C["off_white"], pady=12)
        btn_row.pack()
        tk.Button(btn_row, text="💾  Save", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=16, pady=6,
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕  Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=16, pady=6,
                  command=self.destroy).pack(side="left", padx=8)

    def _populate(self, row):
        self._order.set(row["order_number"])
        self._sname.set(row["sender_name"])
        self._saddr.set(row["sender_address"])
        self._rname.set(row["receiver_name"])
        self._raddr.set(row["receiver_address"])
        self._items.set(row["item_description"])
        self._weight.set(str(row["weight_kg"]))
        self._cost.set(str(row["transport_cost"]))
        self._surcharge.set(str(row["surcharge"]))
        self._pay_var.set(row["payment_status"])
        self._status_var.set(row["status"])

    def _submit(self):
        order = self._order.get().strip()
        if not order:
            messagebox.showwarning("Validation", "Order Number is required.", parent=self)
            return

        drv_label = self._drv_var.get()
        veh_label = self._veh_var.get()
        wh_label  = self._wh_var.get()

        data = {
            "order_number":    order,
            "sender_name":     self._sname.get().strip(),
            "sender_address":  self._saddr.get().strip(),
            "receiver_name":   self._rname.get().strip(),
            "receiver_address":self._raddr.get().strip(),
            "item_description":self._items.get().strip(),
            "weight_kg":       self._weight.get()    or "0",
            "transport_cost":  self._cost.get()      or "0",
            "surcharge":       self._surcharge.get() or "0",
            "payment_status":  self._pay_var.get(),
            "status":          self._status_var.get(),
            "warehouse_id":    self._wh_map.get(wh_label),
            "driver_id":       self._driver_map.get(drv_label),
            "vehicle_id":      self._vehicle_map.get(veh_label),
            "scheduled_date":  self._sched.get().strip(),
            "route_details":   self._route.get().strip(),
        }
        self._on_save(data)
        self.destroy()

    def _centre(self):
        self.update_idletasks()
        w, h  = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
