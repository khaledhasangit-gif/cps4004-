"""
models/inventory.py — Northshore Logistics Ltd
CRUD operations for Inventory management.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import sqlite3
from datetime import datetime
from app.database import get_connection
from app.auth import write_audit_log


def get_all_inventory(warehouse_id: int = None) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        if warehouse_id:
            return conn.execute(
                """SELECT i.*, w.name AS warehouse_name
                   FROM Inventory i
                   JOIN Warehouses w ON i.warehouse_id = w.warehouse_id
                   WHERE i.warehouse_id = ?
                   ORDER BY i.item_name""", (warehouse_id,)
            ).fetchall()
        return conn.execute(
            """SELECT i.*, w.name AS warehouse_name
               FROM Inventory i
               JOIN Warehouses w ON i.warehouse_id = w.warehouse_id
               ORDER BY w.name, i.item_name"""
        ).fetchall()
    finally:
        conn.close()


def get_low_stock() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT i.*, w.name AS warehouse_name
               FROM Inventory i
               JOIN Warehouses w ON i.warehouse_id = w.warehouse_id
               WHERE i.quantity <= i.reorder_level
               ORDER BY i.quantity ASC"""
        ).fetchall()
    finally:
        conn.close()


def add_item(data: dict) -> int:
    conn = get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            """INSERT INTO Inventory
               (item_name, sku, quantity, reorder_level, unit_price,
                warehouse_id, location_in_wh, last_updated)
               VALUES (?,?,?,?,?,?,?,?)""",
            (data["item_name"], data["sku"],
             int(data.get("quantity", 0)),
             int(data.get("reorder_level", 10)),
             float(data.get("unit_price", 0.0)),
             data["warehouse_id"],
             data.get("location_in_wh", ""),
             now)
        )
        conn.commit()
        write_audit_log("ADD_INVENTORY", "Inventory", cur.lastrowid,
                        f"Added item: {data['item_name']} (SKU: {data['sku']})")
        return cur.lastrowid
    finally:
        conn.close()


def update_item(item_id: int, data: dict) -> None:
    conn = get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """UPDATE Inventory SET
               item_name=?, sku=?, quantity=?, reorder_level=?,
               unit_price=?, warehouse_id=?, location_in_wh=?, last_updated=?
               WHERE item_id=?""",
            (data["item_name"], data["sku"],
             int(data.get("quantity", 0)),
             int(data.get("reorder_level", 10)),
             float(data.get("unit_price", 0.0)),
             data["warehouse_id"],
             data.get("location_in_wh", ""),
             now, item_id)
        )
        conn.commit()
        write_audit_log("UPDATE_INVENTORY", "Inventory", item_id,
                        f"Updated item ID {item_id}")
    finally:
        conn.close()


def delete_item(item_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM Inventory WHERE item_id=?", (item_id,))
        conn.commit()
        write_audit_log("DELETE_INVENTORY", "Inventory", item_id,
                        f"Deleted item ID {item_id}")
    finally:
        conn.close()


def adjust_stock(item_id: int, delta: int, reason: str = "") -> None:
    """Add or subtract stock quantity."""
    conn = get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE Inventory SET quantity = quantity + ?, last_updated=? WHERE item_id=?",
            (delta, now, item_id)
        )
        conn.commit()
        write_audit_log("ADJUST_STOCK", "Inventory", item_id,
                        f"Stock adjusted by {delta:+d}. Reason: {reason}")
    finally:
        conn.close()
