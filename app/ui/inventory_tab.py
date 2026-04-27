"""
ui/inventory_tab.py — Northshore Logistics Ltd
Inventory management UI: view, add, edit, delete, adjust stock.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.models.inventory import (
    get_all_inventory, get_low_stock, add_item,
    update_item, delete_item, adjust_stock
)
from app.models.fleet import get_all_warehouses
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows)

COLUMNS = [
    ("id",       "ID",            45),
    ("name",     "Item Name",    180),
    ("sku",      "SKU",          100),
    ("qty",      "Qty",           60),
    ("reorder",  "Reorder Lvl",   90),
    ("price",    "Unit Price £",  100),
    ("location", "Location",     120),
    ("warehouse","Warehouse",    160),
    ("updated",  "Last Updated", 130),
]


class InventoryTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._wh_map = {}
        self._build()
        self.load_data()

    def _build(self):
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📦  Inventory Management",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        # Toolbar
        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=10)

        sess = get_session()

        tk.Label(tb, text="Warehouse:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=4)
        self._wh_var = tk.StringVar(value="All")
        self._wh_cb  = ttk.Combobox(tb, textvariable=self._wh_var,
                                     state="readonly", width=22)
        self._wh_cb.pack(side="left", padx=4)
        self._wh_cb.bind("<<ComboboxSelected>>", lambda _: self.load_data())

        tk.Label(tb, text="Search:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=(12, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        ttk.Entry(tb, textvariable=self._search_var, width=20).pack(side="left", padx=4)

        if sess and sess.can("add_inventory"):
            tk.Button(tb, text="＋ Add Item", font=FONT_BTN,
                      bg=C["teal"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=8, pady=4,
                      command=self._open_add).pack(side="right", padx=4)
        if sess and sess.can("edit_inventory"):
            tk.Button(tb, text="＋/− Stock", font=FONT_BTN,
                      bg=C["blue_lt"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=8, pady=4,
                      command=self._adjust).pack(side="right", padx=4)
            tk.Button(tb, text="✏ Edit", font=FONT_BTN,
                      bg=C["navy_lt"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=8, pady=4,
                      command=self._open_edit).pack(side="right", padx=4)
        if sess and sess.can("delete_inventory"):
            tk.Button(tb, text="🗑 Delete", font=FONT_BTN,
                      bg=C["red"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=8, pady=4,
                      command=self._delete).pack(side="right", padx=4)

        tk.Button(tb, text="⚠ Low Stock", font=FONT_BTN,
                  bg=C["amber"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=8, pady=4,
                  command=self._show_low_stock).pack(side="right", padx=4)
        tk.Button(tb, text="↻", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  cursor="hand2", padx=8, pady=4,
                  command=self.load_data).pack(side="right", padx=4)

        # Treeview
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=6)
        self._tree = make_tree(frm, COLUMNS, height=18)
        vsb = ttk.Scrollbar(frm, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frm, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        self._status_var = tk.StringVar()
        tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                 bg=C["off_white"], fg=C["mid_grey"], anchor="w").pack(
            fill="x", padx=14, pady=2)

    def load_data(self):
        # Populate warehouse filter
        warehouses = get_all_warehouses()
        wh_names   = ["All"] + [w["name"] for w in warehouses]
        self._wh_cb["values"] = wh_names
        self._wh_map = {"All": None}
        for w in warehouses:
            self._wh_map[w["name"]] = w["warehouse_id"]

        wh_id = self._wh_map.get(self._wh_var.get())
        self._rows = get_all_inventory(wh_id)
        self._filter()

    def _filter(self):
        term = self._search_var.get().lower()
        visible = [r for r in self._rows
                   if not term or any(term in str(v).lower() for v in r)]
        display = [
            (r["item_id"], r["item_name"], r["sku"],
             r["quantity"], r["reorder_level"],
             f'£{r["unit_price"]:.2f}',
             r["location_in_wh"] or "—",
             r["warehouse_name"],
             r["last_updated"][:16])
            for r in visible
        ]
        insert_rows(self._tree, display)
        low = sum(1 for r in visible if r["quantity"] <= r["reorder_level"])
        self._status_var.set(
            f"{len(visible)} item(s) shown   |   ⚠ {low} below reorder level"
        )

    def _selected_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an item first.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add(self):
        ItemForm(self, "Add Item", on_save=self._save_new)

    def _open_edit(self):
        iid = self._selected_id()
        if iid is None:
            return
        row = next((r for r in self._rows if r["item_id"] == iid), None)
        if row:
            ItemForm(self, "Edit Item", existing=row,
                     on_save=lambda d: self._save_edit(iid, d))

    def _save_new(self, data):
        try:
            add_item(data)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_edit(self, iid, data):
        try:
            update_item(iid, data)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        iid = self._selected_id()
        if iid and messagebox.askyesno("Confirm", "Delete this item?"):
            delete_item(iid)
            self.load_data()

    def _adjust(self):
        iid = self._selected_id()
        if iid is None:
            return
        delta_str = simpledialog.askstring(
            "Adjust Stock",
            "Enter quantity change (positive to add, negative to remove):",
            parent=self
        )
        if delta_str is None:
            return
        try:
            delta = int(delta_str)
            reason = simpledialog.askstring("Reason", "Reason for adjustment:", parent=self) or ""
            adjust_stock(iid, delta, reason)
            self.load_data()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer.")

    def _show_low_stock(self):
        rows = get_low_stock()
        win  = tk.Toplevel(self)
        win.title("⚠  Low Stock Items")
        win.configure(bg=C["off_white"])
        tk.Label(win, text=f"⚠  {len(rows)} item(s) at or below reorder level",
                 font=FONT_HEAD, fg=C["red"], bg=C["off_white"],
                 padx=16, pady=10).pack()
        tree = make_tree(win, COLUMNS, height=min(len(rows) + 2, 15))
        tree.pack(padx=10, pady=6, fill="both", expand=True)
        display = [
            (r["item_id"], r["item_name"], r["sku"],
             r["quantity"], r["reorder_level"],
             f'£{r["unit_price"]:.2f}',
             r["location_in_wh"] or "—",
             r["warehouse_name"],
             r["last_updated"][:16])
            for r in rows
        ]
        insert_rows(tree, display)


class ItemForm(tk.Toplevel):
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
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text=self.title(), font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=14, pady=8).pack(fill="x")
        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack()

        def r(label, row):
            tk.Label(form, text=label, font=FONT_SMALL,
                     bg=C["off_white"]).grid(row=row, column=0, sticky="w", pady=3, padx=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=28).grid(
                row=row, column=1, sticky="ew", padx=4, pady=3)
            return var

        self._name   = r("Item Name *",   0)
        self._sku    = r("SKU *",          1)
        self._qty    = r("Quantity",       2)
        self._reorder= r("Reorder Level",  3)
        self._price  = r("Unit Price £",   4)
        self._loc    = r("Location in WH", 5)

        tk.Label(form, text="Warehouse *", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=6, column=0, sticky="w", pady=3, padx=4)
        self._wh_var = tk.StringVar()
        warehouses   = get_all_warehouses()
        wh_labels    = []
        for w in warehouses:
            self._wh_map[w["name"]] = w["warehouse_id"]
            wh_labels.append(w["name"])
        ttk.Combobox(form, textvariable=self._wh_var,
                     values=wh_labels, state="readonly",
                     width=26).grid(row=6, column=1, sticky="w", padx=4, pady=3)

        btn_row = tk.Frame(self, bg=C["off_white"], pady=12)
        btn_row.pack()
        tk.Button(btn_row, text="💾 Save", font=FONT_BTN,
                  bg=C["teal"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _populate(self, row):
        self._name.set(row["item_name"])
        self._sku.set(row["sku"])
        self._qty.set(str(row["quantity"]))
        self._reorder.set(str(row["reorder_level"]))
        self._price.set(str(row["unit_price"]))
        self._loc.set(row["location_in_wh"] or "")
        # Find warehouse name
        for name, wid in self._wh_map.items():
            if wid == row["warehouse_id"]:
                self._wh_var.set(name)
                break

    def _submit(self):
        if not self._name.get().strip() or not self._sku.get().strip():
            messagebox.showwarning("Validation", "Item Name and SKU are required.", parent=self)
            return
        data = {
            "item_name":    self._name.get().strip(),
            "sku":          self._sku.get().strip().upper(),
            "quantity":     self._qty.get() or "0",
            "reorder_level":self._reorder.get() or "10",
            "unit_price":   self._price.get() or "0",
            "location_in_wh":self._loc.get().strip(),
            "warehouse_id": self._wh_map.get(self._wh_var.get()),
        }
        self._on_save(data)
        self.destroy()
