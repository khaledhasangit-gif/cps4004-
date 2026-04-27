"""
main.py — Northshore Logistics Ltd
Application entry point.
Initialises the database then launches Login → Main Window.
CPS4004 – Database Systems | St Mary's University Twickenham

Usage:
    python app/main.py
"""

import sys
import os

# ── Ensure the project root is on the path so all imports resolve ─────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import messagebox

from app.database import initialise_database
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow


def main():
    # ── Step 1: Initialise database ───────────────────────────────────────────
    try:
        initialise_database()
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Error",
            f"Failed to initialise the database:\n\n{exc}\n\n"
            "Ensure you have write permission to the 'data/' folder."
        )
        root.destroy()
        sys.exit(1)

    # ── Step 2: Launch login window ───────────────────────────────────────────
    root = tk.Tk()
    root.withdraw()   # hide the root — login dialog is a Toplevel

    def on_login_success():
        root.destroy()
        app = MainWindow()
        app.mainloop()

    login = LoginWindow(root, on_success=on_login_success)
    root.mainloop()


if __name__ == "__main__":
    main()
