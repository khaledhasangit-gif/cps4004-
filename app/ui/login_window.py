"""
ui/login_window.py — Northshore Logistics Ltd
Login screen with credential validation.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import tkinter as tk
from tkinter import ttk, messagebox
from app.auth import login
from app.ui.styles import C, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL


class LoginWindow(tk.Toplevel):
    """Standalone login dialog. Calls on_success() when login succeeds."""

    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success  = on_success
        self.title("Northshore Logistics — Login")
        self.resizable(False, False)
        self.configure(bg=C["navy"])
        self.grab_set()
        self._build()
        self._centre()
        self.bind("<Return>", lambda _: self._attempt_login())

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["navy"], padx=40, pady=30)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚚  NORTHSHORE LOGISTICS",
                 font=FONT_TITLE, fg=C["teal"], bg=C["navy"]).pack()
        tk.Label(hdr, text="Database Management System",
                 font=FONT_BODY, fg=C["light_grey"], bg=C["navy"]).pack()

        # Card
        card = tk.Frame(self, bg=C["white"], padx=40, pady=30)
        card.pack(fill="both", padx=30, pady=(0, 30))

        tk.Label(card, text="Sign In", font=FONT_HEAD,
                 fg=C["navy"], bg=C["white"]).grid(row=0, column=0,
                                                    columnspan=2, pady=(0, 16))

        tk.Label(card, text="Username:", font=FONT_BODY,
                 fg=C["dark_grey"], bg=C["white"]).grid(row=1, column=0,
                                                         sticky="w", pady=5)
        self._user_var = tk.StringVar()
        user_entry = ttk.Entry(card, textvariable=self._user_var, width=28,
                               font=FONT_BODY)
        user_entry.grid(row=1, column=1, padx=(8, 0), pady=5)
        user_entry.focus_set()

        tk.Label(card, text="Password:", font=FONT_BODY,
                 fg=C["dark_grey"], bg=C["white"]).grid(row=2, column=0,
                                                         sticky="w", pady=5)
        self._pass_var = tk.StringVar()
        ttk.Entry(card, textvariable=self._pass_var, show="•", width=28,
                  font=FONT_BODY).grid(row=2, column=1, padx=(8, 0), pady=5)

        # Error label
        self._err_var = tk.StringVar()
        tk.Label(card, textvariable=self._err_var, font=FONT_SMALL,
                 fg=C["red"], bg=C["white"]).grid(row=3, column=0,
                                                   columnspan=2, pady=(6, 0))

        # Login button
        btn = tk.Button(card, text="LOGIN", font=FONT_BTN,
                        bg=C["teal"], fg=C["white"], relief="flat",
                        activebackground=C["teal_dk"], activeforeground=C["white"],
                        cursor="hand2", padx=20, pady=8,
                        command=self._attempt_login)
        btn.grid(row=4, column=0, columnspan=2, pady=(16, 4))

        # Demo hint
        hint = (
            "Demo accounts:\n"
            "admin / Admin2024!    manager1 / Manager2024!\n"
            "staff1 / Staff2024!   driver1 / Driver2024!"
        )
        tk.Label(card, text=hint, font=("Helvetica", 8),
                 fg=C["mid_grey"], bg=C["white"], justify="left").grid(
            row=5, column=0, columnspan=2, pady=(10, 0))

    # ── Behaviour ─────────────────────────────────────────────────────────────
    def _attempt_login(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get()
        if not username or not password:
            self._err_var.set("Please enter both username and password.")
            return
        ok, reason = login(username, password)
        if ok:
            self.destroy()
            self.on_success()
        else:
            self._err_var.set(reason)
            self._pass_var.set("")

    def _centre(self):
        self.update_idletasks()
        w, h  = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
