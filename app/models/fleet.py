"""
models/fleet.py — Northshore Logistics Ltd
CRUD for Vehicles, Drivers, and Warehouses.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import sqlite3
from app.database import get_connection
from app.auth import write_audit_log


# ── Vehicles ─────────────────────────────────────────────────────────────────
def get_all_vehicles() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT v.*, w.name AS warehouse_name
               FROM Vehicles v
               LEFT JOIN Warehouses w ON v.warehouse_id = w.warehouse_id
               ORDER BY v.registration"""
        ).fetchall()
    finally:
        conn.close()


def add_vehicle(data: dict) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO Vehicles
               (registration, make, model, capacity_kg, status,
                last_maintenance, next_maintenance, warehouse_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (data["registration"], data["make"], data["model"],
             float(data.get("capacity_kg", 0)),
             data.get("status", "available"),
             data.get("last_maintenance", ""),
             data.get("next_maintenance", ""),
             data.get("warehouse_id"))
        )
        conn.commit()
        write_audit_log("ADD_VEHICLE", "Vehicles", cur.lastrowid,
                        f"Added vehicle: {data['registration']}")
        return cur.lastrowid
    finally:
        conn.close()


def update_vehicle(vehicle_id: int, data: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE Vehicles SET registration=?, make=?, model=?,
               capacity_kg=?, status=?, last_maintenance=?,
               next_maintenance=?, warehouse_id=?
               WHERE vehicle_id=?""",
            (data["registration"], data["make"], data["model"],
             float(data.get("capacity_kg", 0)),
             data.get("status", "available"),
             data.get("last_maintenance", ""),
             data.get("next_maintenance", ""),
             data.get("warehouse_id"), vehicle_id)
        )
        conn.commit()
        write_audit_log("UPDATE_VEHICLE", "Vehicles", vehicle_id,
                        f"Updated vehicle ID {vehicle_id}")
    finally:
        conn.close()


def delete_vehicle(vehicle_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM Vehicles WHERE vehicle_id=?", (vehicle_id,))
        conn.commit()
        write_audit_log("DELETE_VEHICLE", "Vehicles", vehicle_id)
    finally:
        conn.close()


# ── Drivers ──────────────────────────────────────────────────────────────────
def get_all_drivers() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT d.*, u.full_name, u.email, u.username, u.is_active
               FROM Drivers d
               JOIN Users u ON d.user_id = u.user_id
               ORDER BY u.full_name"""
        ).fetchall()
    finally:
        conn.close()


def update_driver_status(driver_id: int, status: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE Drivers SET status=? WHERE driver_id=?", (status, driver_id)
        )
        conn.commit()
        write_audit_log("UPDATE_DRIVER_STATUS", "Drivers", driver_id,
                        f"Status changed to: {status}")
    finally:
        conn.close()


def add_driver(user_data: dict, driver_data: dict) -> int:
    """Create a new user account with 'driver' role, then a Driver record."""
    from app.database import hash_password
    conn = get_connection()
    try:
        pw_hash, salt = hash_password(user_data["password"])
        cur_u = conn.execute(
            "INSERT INTO Users (username,password_hash,salt,role,full_name,email,phone) "
            "VALUES (?,?,?,?,?,?,?)",
            (user_data["username"], pw_hash, salt, "driver",
             user_data["full_name"], user_data.get("email", ""),
             user_data.get("phone", ""))
        )
        uid = cur_u.lastrowid
        cur_d = conn.execute(
            "INSERT INTO Drivers (user_id,license_number,license_expiry,phone,address,status) "
            "VALUES (?,?,?,?,?,?)",
            (uid, driver_data["license_number"], driver_data["license_expiry"],
             driver_data.get("phone", ""), driver_data.get("address", ""),
             "available")
        )
        conn.commit()
        write_audit_log("ADD_DRIVER", "Drivers", cur_d.lastrowid,
                        f"New driver: {user_data['full_name']}")
        return cur_d.lastrowid
    finally:
        conn.close()


# ── Warehouses ────────────────────────────────────────────────────────────────
def get_all_warehouses() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT w.*, u.full_name AS manager_name
               FROM Warehouses w
               LEFT JOIN Users u ON w.manager_id = u.user_id
               ORDER BY w.name"""
        ).fetchall()
    finally:
        conn.close()


def add_warehouse(data: dict) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO Warehouses (name,address,city,postcode,capacity,manager_id) "
            "VALUES (?,?,?,?,?,?)",
            (data["name"], data["address"], data["city"],
             data.get("postcode", ""), int(data.get("capacity", 0)),
             data.get("manager_id"))
        )
        conn.commit()
        write_audit_log("ADD_WAREHOUSE", "Warehouses", cur.lastrowid,
                        f"Added warehouse: {data['name']}")
        return cur.lastrowid
    finally:
        conn.close()


def update_warehouse(warehouse_id: int, data: dict) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE Warehouses SET name=?,address=?,city=?,postcode=?,
               capacity=?,manager_id=? WHERE warehouse_id=?""",
            (data["name"], data["address"], data["city"],
             data.get("postcode", ""), int(data.get("capacity", 0)),
             data.get("manager_id"), warehouse_id)
        )
        conn.commit()
        write_audit_log("UPDATE_WAREHOUSE", "Warehouses", warehouse_id)
    finally:
        conn.close()
