"""
models/shipments.py — Northshore Logistics Ltd
All CRUD operations for Shipments and Deliveries.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import sqlite3
from datetime import datetime
from app.database import get_connection
from app.auth import get_session, write_audit_log


def generate_ref() -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM Shipments").fetchone()
        n = row[0] + 1
        return f"SHP-{datetime.now().year}-{n:04d}"
    finally:
        conn.close()


def get_all_shipments(status_filter: str = None) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        if status_filter and status_filter != "All":
            return conn.execute(
                """SELECT s.*, w.name AS warehouse_name,
                          u.full_name AS driver_name, v.registration
                   FROM Shipments s
                   LEFT JOIN Warehouses w ON s.warehouse_id = w.warehouse_id
                   LEFT JOIN Drivers d    ON s.driver_id    = d.driver_id
                   LEFT JOIN Users u      ON d.user_id      = u.user_id
                   LEFT JOIN Vehicles v   ON s.vehicle_id   = v.vehicle_id
                   WHERE s.status = ?
                   ORDER BY s.created_at DESC""",
                (status_filter,)
            ).fetchall()
        return conn.execute(
            """SELECT s.*, w.name AS warehouse_name,
                      u.full_name AS driver_name, v.registration
               FROM Shipments s
               LEFT JOIN Warehouses w ON s.warehouse_id = w.warehouse_id
               LEFT JOIN Drivers d    ON s.driver_id    = d.driver_id
               LEFT JOIN Users u      ON d.user_id      = u.user_id
               LEFT JOIN Vehicles v   ON s.vehicle_id   = v.vehicle_id
               ORDER BY s.created_at DESC"""
        ).fetchall()
    finally:
        conn.close()


def get_shipment_by_id(shipment_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM Shipments WHERE shipment_id = ?", (shipment_id,)
        ).fetchone()
    finally:
        conn.close()


def add_shipment(data: dict) -> int:
    sess = get_session()
    conn = get_connection()
    try:
        ref = generate_ref()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            """INSERT INTO Shipments
               (shipment_ref, order_number, sender_name, sender_address,
                receiver_name, receiver_address, item_description, weight_kg,
                transport_cost, surcharge, payment_status, status,
                warehouse_id, vehicle_id, driver_id, created_by, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ref, data["order_number"], data["sender_name"], data["sender_address"],
             data["receiver_name"], data["receiver_address"], data["item_description"],
             float(data.get("weight_kg", 0)),
             float(data.get("transport_cost", 0)),
             float(data.get("surcharge", 0)),
             data.get("payment_status", "pending"),
             data.get("status", "pending"),
             data.get("warehouse_id"), data.get("vehicle_id"), data.get("driver_id"),
             sess.user_id if sess else None, now, now)
        )
        shp_id = cur.lastrowid

        # Auto-create delivery record
        conn.execute(
            "INSERT INTO Deliveries (shipment_id, driver_id, vehicle_id, route_details, "
            "scheduled_date, delivery_status) VALUES (?,?,?,?,?,?)",
            (shp_id, data.get("driver_id"), data.get("vehicle_id"),
             data.get("route_details", "TBD"),
             data.get("scheduled_date", ""),
             "pending")
        )
        conn.commit()
        write_audit_log("ADD_SHIPMENT", "Shipments", shp_id,
                        f"New shipment created: {ref}")
        return shp_id
    finally:
        conn.close()


def update_shipment(shipment_id: int, data: dict) -> None:
    conn = get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """UPDATE Shipments SET
               order_number=?, sender_name=?, sender_address=?,
               receiver_name=?, receiver_address=?, item_description=?,
               weight_kg=?, transport_cost=?, surcharge=?,
               payment_status=?, status=?, warehouse_id=?,
               vehicle_id=?, driver_id=?, updated_at=?
               WHERE shipment_id=?""",
            (data["order_number"], data["sender_name"], data["sender_address"],
             data["receiver_name"], data["receiver_address"], data["item_description"],
             float(data.get("weight_kg", 0)),
             float(data.get("transport_cost", 0)),
             float(data.get("surcharge", 0)),
             data.get("payment_status", "pending"),
             data.get("status", "pending"),
             data.get("warehouse_id"), data.get("vehicle_id"),
             data.get("driver_id"), now, shipment_id)
        )
        # Sync delivery record
        conn.execute(
            """UPDATE Deliveries SET driver_id=?, vehicle_id=?,
               route_details=?, scheduled_date=?, delivery_status=?
               WHERE shipment_id=?""",
            (data.get("driver_id"), data.get("vehicle_id"),
             data.get("route_details", "TBD"),
             data.get("scheduled_date", ""),
             _map_delivery_status(data.get("status", "pending")),
             shipment_id)
        )
        conn.commit()
        write_audit_log("UPDATE_SHIPMENT", "Shipments", shipment_id,
                        f"Status → {data.get('status')}")
    finally:
        conn.close()


def delete_shipment(shipment_id: int) -> None:
    conn = get_connection()
    try:
        ref_row = conn.execute(
            "SELECT shipment_ref FROM Shipments WHERE shipment_id=?", (shipment_id,)
        ).fetchone()
        ref = ref_row["shipment_ref"] if ref_row else str(shipment_id)
        conn.execute("DELETE FROM Shipments WHERE shipment_id=?", (shipment_id,))
        conn.commit()
        write_audit_log("DELETE_SHIPMENT", "Shipments", shipment_id,
                        f"Deleted shipment: {ref}")
    finally:
        conn.close()


def _map_delivery_status(shipment_status: str) -> str:
    mapping = {
        "pending": "pending", "in_transit": "in_transit",
        "delivered": "delivered", "delayed": "in_transit",
        "returned": "failed",
    }
    return mapping.get(shipment_status, "pending")


def get_drivers_available() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT d.driver_id, u.full_name
               FROM Drivers d JOIN Users u ON d.user_id = u.user_id
               WHERE d.status IN ('available','on_route')
               ORDER BY u.full_name"""
        ).fetchall()
    finally:
        conn.close()


def get_vehicles_available() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT vehicle_id, registration || ' – ' || make || ' ' || model AS label
               FROM Vehicles WHERE status IN ('available','in_use')
               ORDER BY registration"""
        ).fetchall()
    finally:
        conn.close()


def get_warehouses() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT warehouse_id, name FROM Warehouses ORDER BY name"
        ).fetchall()
    finally:
        conn.close()
