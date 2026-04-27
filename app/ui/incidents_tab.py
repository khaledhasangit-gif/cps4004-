"""
ui/incidents_tab.py — Northshore Logistics Ltd
Incident reporting, tracking, and resolution UI.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.reports import get_all_incidents, add_incident, resolve_incident
from app.auth import get_session
from app.ui.styles import (C, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
                            make_tree, insert_rows)
from app.models.shipments import get_warehouses  # reuse to get shipment list

INCIDENT_TYPES = ["delay", "route_change", "damaged", "failed_delivery", "other"]

COLUMNS = [
    ("id",       "ID",         45),
    ("ref",      "Shipment",  120),
    ("type",     "Type",      110),
    ("desc",     "Description",230),
    ("reporter", "Reported By",140),
    ("reported", "Reported",  130),
    ("resolved", "Resolved",  130),
]


class IncidentsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = []
        self._build()
        self.load_data()

    def _build(self):
        hdr = tk.Frame(self, bg=C["navy"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚠  Incident Management",
                 font=FONT_HEAD, fg=C["teal"], bg=C["navy"]).pack(side="left")

        tb = tk.Frame(self, bg=C["off_white"], pady=6)
        tb.pack(fill="x", padx=10)

        sess = get_session()
        if sess and sess.can("add_incident"):
            tk.Button(tb, text="＋ Report Incident", font=FONT_BTN,
                      bg=C["red"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._open_add).pack(side="left", padx=4)
        if sess and sess.can("resolve_incident"):
            tk.Button(tb, text="✔ Resolve", font=FONT_BTN,
                      bg=C["green"], fg=C["white"], relief="flat",
                      cursor="hand2", padx=10, pady=4,
                      command=self._resolve).pack(side="left", padx=4)

        # Filter
        tk.Label(tb, text="Show:", font=FONT_SMALL,
                 bg=C["off_white"]).pack(side="left", padx=(14, 2))
        self._filter_var = tk.StringVar(value="All")
        ttk.Combobox(tb, textvariable=self._filter_var,
                     values=["All", "Open", "Resolved"],
                     state="readonly", width=10).pack(side="left", padx=4)
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())

        tk.Button(tb, text="↻", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.load_data).pack(side="left", padx=4)

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=10, pady=6)
        self._tree = make_tree(frm, COLUMNS, height=18)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # Detail pane
        detail_frame = tk.Frame(self, bg=C["white"], padx=14, pady=8)
        detail_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(detail_frame, text="Resolution Notes:", font=FONT_SMALL,
                 fg=C["navy"], bg=C["white"]).pack(anchor="w")
        self._detail_text = tk.Text(detail_frame, height=3, font=FONT_SMALL,
                                    bg=C["off_white"], relief="flat", state="disabled")
        self._detail_text.pack(fill="x")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        self._status_var = tk.StringVar()
        tk.Label(self, textvariable=self._status_var, font=FONT_SMALL,
                 bg=C["off_white"], fg=C["mid_grey"], anchor="w").pack(
            fill="x", padx=14, pady=2)

    def load_data(self):
        self._rows = get_all_incidents()
        self._apply_filter()

    def _apply_filter(self):
        f = self._filter_var.get()
        if f == "Open":
            visible = [r for r in self._rows if r["resolved_at"] is None]
        elif f == "Resolved":
            visible = [r for r in self._rows if r["resolved_at"] is not None]
        else:
            visible = self._rows

        display = [
            (r["incident_id"], r["shipment_ref"], r["incident_type"],
             r["description"][:60] + ("…" if len(r["description"]) > 60 else ""),
             r["reporter_name"] or "—",
             r["reported_at"][:16],
             r["resolved_at"][:16] if r["resolved_at"] else "Open")
            for r in visible
        ]
        insert_rows(self._tree, display)
        open_count = sum(1 for r in self._rows if r["resolved_at"] is None)
        self._status_var.set(
            f"{len(visible)} shown   |   {open_count} open incident(s)"
        )

    def _on_select(self, _):
        sel = self._tree.selection()
        if not sel:
            return
        iid = self._tree.item(sel[0])["values"][0]
        row = next((r for r in self._rows if r["incident_id"] == iid), None)
        if row:
            self._detail_text.configure(state="normal")
            self._detail_text.delete("1.0", "end")
            self._detail_text.insert(
                "1.0",
                f"Description: {row['description']}\n"
                f"Resolution:  {row['resolution_notes'] or '—'}"
            )
            self._detail_text.configure(state="disabled")

    def _sel_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an incident.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add(self):
        IncidentForm(self, on_save=self._save_new)

    def _save_new(self, data):
        try:
            add_incident(data)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _resolve(self):
        iid = self._sel_id()
        if iid is None:
            return
        row = next((r for r in self._rows if r["incident_id"] == iid), None)
        if row and row["resolved_at"]:
            messagebox.showinfo("Info", "This incident is already resolved.")
            return
        ResolveDialog(self, iid, on_resolve=lambda notes: (
            resolve_incident(iid, notes), self.load_data()
        ))


class IncidentForm(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Report Incident")
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_save   = on_save
        self._shp_map   = {}
        self._build()
        self._centre()

    def _build(self):
        from app.database import get_connection
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text="Report New Incident", font=FONT_HEAD,
                 bg=C["navy"], fg=C["white"], padx=14, pady=8).pack(fill="x")
        form = tk.Frame(self, bg=C["off_white"], padx=20, pady=12)
        form.pack()

        # Shipment selector
        tk.Label(form, text="Shipment *", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self._shp_var = tk.StringVar()
        conn = get_connection()
        rows = conn.execute(
            "SELECT shipment_id, shipment_ref FROM Shipments ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        shp_labels = []
        for r in rows:
            label = r["shipment_ref"]
            self._shp_map[label] = r["shipment_id"]
            shp_labels.append(label)
        ttk.Combobox(form, textvariable=self._shp_var,
                     values=shp_labels, state="readonly",
                     width=28).grid(row=0, column=1, padx=4, pady=4)

        # Type
        tk.Label(form, text="Incident Type *", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self._type_var = tk.StringVar(value=INCIDENT_TYPES[0])
        ttk.Combobox(form, textvariable=self._type_var,
                     values=INCIDENT_TYPES, state="readonly",
                     width=28).grid(row=1, column=1, padx=4, pady=4)

        # Description
        tk.Label(form, text="Description *", font=FONT_SMALL,
                 bg=C["off_white"]).grid(row=2, column=0, sticky="nw", padx=4, pady=4)
        self._desc = tk.Text(form, height=5, width=40, font=FONT_BODY, relief="flat",
                             bg=C["white"])
        self._desc.grid(row=2, column=1, padx=4, pady=4)

        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="💾 Submit", font=FONT_BTN,
                  bg=C["red"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)

    def _submit(self):
        shp_label = self._shp_var.get()
        desc      = self._desc.get("1.0", "end").strip()
        if not shp_label or not desc:
            messagebox.showwarning("Validation",
                                   "Shipment and description are required.", parent=self)
            return
        data = {
            "shipment_id":   self._shp_map[shp_label],
            "incident_type": self._type_var.get(),
            "description":   desc,
        }
        self._on_save(data)
        self.destroy()

    def _centre(self):
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")


class ResolveDialog(tk.Toplevel):
    def __init__(self, parent, incident_id, on_resolve):
        super().__init__(parent)
        self.title("Resolve Incident")
        self.resizable(False, False)
        self.configure(bg=C["off_white"])
        self.grab_set()
        self._on_resolve = on_resolve
        tk.Frame(self, bg=C["navy"], height=4).pack(fill="x")
        tk.Label(self, text=f"Resolve Incident #{incident_id}",
                 font=FONT_HEAD, bg=C["navy"], fg=C["white"],
                 padx=14, pady=8).pack(fill="x")
        tk.Label(self, text="Resolution Notes:", font=FONT_BODY,
                 bg=C["off_white"], padx=20).pack(anchor="w", pady=(10, 2))
        self._notes = tk.Text(self, height=5, width=50, font=FONT_BODY,
                              bg=C["white"], relief="flat")
        self._notes.pack(padx=20, pady=4)
        btn_row = tk.Frame(self, bg=C["off_white"], pady=10)
        btn_row.pack()
        tk.Button(btn_row, text="✔ Resolve", font=FONT_BTN,
                  bg=C["green"], fg=C["white"], relief="flat",
                  command=self._submit).pack(side="left", padx=8)
        tk.Button(btn_row, text="✕ Cancel", font=FONT_BTN,
                  bg=C["mid_grey"], fg=C["white"], relief="flat",
                  command=self.destroy).pack(side="left", padx=8)
        self.update_idletasks()
        w, h   = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _submit(self):
        notes = self._notes.get("1.0", "end").strip()
        self._on_resolve(notes or "Resolved.")
        self.destroy()
