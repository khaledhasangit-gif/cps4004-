"""
ui/styles.py — Northshore Logistics Ltd
Centralised colour palette, fonts, and widget factory helpers.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk

# ── Colour palette ───────────────────────────────────────────────────────────
C = {
    "navy":      "#1a2e4a",
    "navy_mid":  "#243d5e",
    "navy_lt":   "#2e5080",
    "teal":      "#1abc9c",
    "teal_dk":   "#16a085",
    "white":     "#ffffff",
    "off_white": "#f4f6f9",
    "light_grey":"#dfe6e9",
    "mid_grey":  "#95a5a6",
    "dark_grey": "#2d3436",
    "red":       "#e74c3c",
    "amber":     "#f39c12",
    "green":     "#27ae60",
    "blue_lt":   "#3498db",
    "row_even":  "#f8fafc",
    "row_odd":   "#eaf0fb",
}

FONT_TITLE  = ("Helvetica", 18, "bold")
FONT_HEAD   = ("Helvetica", 12, "bold")
FONT_BODY   = ("Helvetica", 10)
FONT_SMALL  = ("Helvetica",  9)
FONT_BTN    = ("Helvetica", 10, "bold")
FONT_STAT   = ("Helvetica", 22, "bold")


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Apply a consistent ttk theme to the whole application."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # Notebook tabs
    style.configure("TNotebook",             background=C["navy"])
    style.configure("TNotebook.Tab",
                    background=C["navy_mid"], foreground=C["white"],
                    padding=[14, 6], font=FONT_BTN)
    style.map("TNotebook.Tab",
              background=[("selected", C["teal"]), ("active", C["navy_lt"])],
              foreground=[("selected", C["white"])])

    # Treeview (tables)
    style.configure("Treeview",
                    background=C["white"], foreground=C["dark_grey"],
                    fieldbackground=C["white"], rowheight=26, font=FONT_BODY)
    style.configure("Treeview.Heading",
                    background=C["navy"], foreground=C["white"],
                    font=FONT_BTN, relief="flat")
    style.map("Treeview", background=[("selected", C["teal"])])

    # Buttons
    style.configure("TButton",
                    background=C["navy_lt"], foreground=C["white"],
                    font=FONT_BTN, padding=[8, 4])
    style.map("TButton",
              background=[("active", C["teal"]), ("pressed", C["teal_dk"])])

    style.configure("Action.TButton",
                    background=C["teal"], foreground=C["white"],
                    font=FONT_BTN, padding=[10, 5])
    style.map("Action.TButton",
              background=[("active", C["teal_dk"])])

    style.configure("Danger.TButton",
                    background=C["red"], foreground=C["white"],
                    font=FONT_BTN, padding=[8, 4])
    style.map("Danger.TButton",
              background=[("active", "#c0392b")])

    style.configure("Success.TButton",
                    background=C["green"], foreground=C["white"],
                    font=FONT_BTN, padding=[8, 4])

    # Labels
    style.configure("TLabel",   background=C["off_white"], font=FONT_BODY)
    style.configure("H1.TLabel",background=C["navy"],      foreground=C["white"],
                    font=FONT_TITLE, padding=[10, 6])
    style.configure("Head.TLabel", font=FONT_HEAD, foreground=C["navy"])
    style.configure("Stat.TLabel", font=FONT_STAT, foreground=C["teal"],
                    background=C["white"])
    style.configure("StatSub.TLabel", font=FONT_SMALL, foreground=C["mid_grey"],
                    background=C["white"])

    # Frames
    style.configure("Card.TFrame",  background=C["white"],     relief="ridge")
    style.configure("Header.TFrame",background=C["navy"])
    style.configure("TFrame",       background=C["off_white"])

    # Entry / Combobox
    style.configure("TEntry",    font=FONT_BODY, padding=[4, 4])
    style.configure("TCombobox", font=FONT_BODY)

    # Scrollbar
    style.configure("TScrollbar", background=C["light_grey"],
                    troughcolor=C["off_white"])

    return style


def make_tree(parent, columns: list[tuple], height: int = 15) -> ttk.Treeview:
    """Factory: build a Treeview with alternating row colours."""
    col_ids = [c[0] for c in columns]
    tree    = ttk.Treeview(parent, columns=col_ids, show="headings", height=height)
    for cid, label, width in columns:
        tree.heading(cid, text=label)
        tree.column(cid, width=width, minwidth=50)
    tree.tag_configure("even", background=C["row_even"])
    tree.tag_configure("odd",  background=C["row_odd"])
    return tree


def insert_rows(tree: ttk.Treeview, rows) -> None:
    """Clear tree and re-populate with alternating row tags."""
    for item in tree.get_children():
        tree.delete(item)
    for i, row in enumerate(rows):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=list(row), tags=(tag,))


def labelled_entry(parent, label: str, row: int, col: int = 0,
                   width: int = 28, **kw) -> tk.StringVar:
    var = tk.StringVar()
    ttk.Label(parent, text=label, font=FONT_BODY).grid(
        row=row, column=col, sticky="w", padx=6, pady=3)
    ttk.Entry(parent, textvariable=var, width=width, **kw).grid(
        row=row, column=col + 1, sticky="ew", padx=6, pady=3)
    return var


def labelled_combo(parent, label: str, row: int, col: int = 0,
                   values: list = None, width: int = 26) -> tk.StringVar:
    var = tk.StringVar()
    ttk.Label(parent, text=label, font=FONT_BODY).grid(
        row=row, column=col, sticky="w", padx=6, pady=3)
    cb = ttk.Combobox(parent, textvariable=var, values=values or [],
                      width=width, state="readonly")
    cb.grid(row=row, column=col + 1, sticky="ew", padx=6, pady=3)
    return var


def status_badge_colour(status: str) -> str:
    mapping = {
        "delivered":  C["green"],  "available":  C["green"],
        "in_transit": C["blue_lt"],"on_route":   C["blue_lt"],
        "pending":    C["amber"],  "off_duty":   C["amber"],
        "delayed":    C["red"],    "returned":   C["red"],
        "maintenance":C["amber"],  "overdue":    C["red"],
        "paid":       C["green"],  "failed":     C["red"],
        "suspended":  C["red"],    "retired":    C["mid_grey"],
    }
    return mapping.get(status.lower() if status else "", C["mid_grey"])
