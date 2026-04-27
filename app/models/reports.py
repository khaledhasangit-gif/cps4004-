"""
models/reports.py — Northshore Logistics Ltd
Incident management and report generation using pandas.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from app.database import get_connection
from app.auth import get_session, write_audit_log

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Incidents ────────────────────────────────────────────────────────────────
def get_all_incidents() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT i.*, s.shipment_ref, u.full_name AS reporter_name
               FROM Incidents i
               JOIN Shipments s ON i.shipment_id = s.shipment_id
               LEFT JOIN Users u ON i.reported_by = u.user_id
               ORDER BY i.reported_at DESC"""
        ).fetchall()
    finally:
        conn.close()


def add_incident(data: dict) -> int:
    sess = get_session()
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO Incidents
               (shipment_id, reported_by, incident_type, description, reported_at)
               VALUES (?,?,?,?,?)""",
            (data["shipment_id"],
             sess.user_id if sess else None,
             data["incident_type"],
             data["description"],
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        write_audit_log("ADD_INCIDENT", "Incidents", cur.lastrowid,
                        f"Incident: {data['incident_type']} for shipment {data['shipment_id']}")
        return cur.lastrowid
    finally:
        conn.close()


def resolve_incident(incident_id: int, notes: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE Incidents SET resolved_at=?, resolution_notes=? WHERE incident_id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes, incident_id)
        )
        conn.commit()
        write_audit_log("RESOLVE_INCIDENT", "Incidents", incident_id,
                        f"Incident resolved: {notes[:60]}")
    finally:
        conn.close()


# ── Dashboard summary ────────────────────────────────────────────────────────
def get_dashboard_stats() -> dict:
    conn = get_connection()
    try:
        stats = {}

        row = conn.execute("SELECT COUNT(*) FROM Shipments").fetchone()
        stats["total_shipments"] = row[0]

        for status in ("pending", "in_transit", "delivered", "delayed", "returned"):
            row = conn.execute(
                "SELECT COUNT(*) FROM Shipments WHERE status=?", (status,)
            ).fetchone()
            stats[f"shipments_{status}"] = row[0]

        row = conn.execute("SELECT COUNT(*) FROM Vehicles WHERE status='available'").fetchone()
        stats["vehicles_available"] = row[0]

        row = conn.execute("SELECT COUNT(*) FROM Drivers WHERE status='available'").fetchone()
        stats["drivers_available"] = row[0]

        row = conn.execute(
            "SELECT COUNT(*) FROM Inventory WHERE quantity <= reorder_level"
        ).fetchone()
        stats["low_stock_count"] = row[0]

        row = conn.execute(
            "SELECT COUNT(*) FROM Incidents WHERE resolved_at IS NULL"
        ).fetchone()
        stats["open_incidents"] = row[0]

        row = conn.execute(
            "SELECT COALESCE(SUM(transport_cost + surcharge),0) FROM Shipments"
        ).fetchone()
        stats["total_revenue"] = round(row[0], 2)

        row = conn.execute(
            "SELECT COALESCE(SUM(transport_cost + surcharge),0) FROM Shipments "
            "WHERE payment_status='overdue'"
        ).fetchone()
        stats["overdue_amount"] = round(row[0], 2)

        return stats
    finally:
        conn.close()


# ── Shipment status report ────────────────────────────────────────────────────
def report_shipment_status() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """SELECT s.shipment_ref, s.order_number, s.sender_name, s.receiver_name,
                      s.item_description, s.weight_kg,
                      (s.transport_cost + s.surcharge) AS total_cost,
                      s.payment_status, s.status,
                      w.name AS warehouse,
                      u.full_name AS driver,
                      s.created_at
               FROM Shipments s
               LEFT JOIN Warehouses w ON s.warehouse_id = w.warehouse_id
               LEFT JOIN Drivers d    ON s.driver_id    = d.driver_id
               LEFT JOIN Users u      ON d.user_id      = u.user_id
               ORDER BY s.created_at DESC""",
            conn
        )
        return df
    finally:
        conn.close()


# ── Vehicle utilisation ───────────────────────────────────────────────────────
def report_vehicle_utilisation() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """SELECT v.registration, v.make || ' ' || v.model AS vehicle,
                      v.capacity_kg, v.status,
                      COUNT(s.shipment_id) AS total_shipments,
                      COALESCE(SUM(s.weight_kg),0) AS total_weight_kg,
                      w.name AS home_warehouse
               FROM Vehicles v
               LEFT JOIN Shipments s  ON s.vehicle_id = v.vehicle_id
               LEFT JOIN Warehouses w ON v.warehouse_id = w.warehouse_id
               GROUP BY v.vehicle_id
               ORDER BY total_shipments DESC""",
            conn
        )
        return df
    finally:
        conn.close()


# ── Warehouse activity ────────────────────────────────────────────────────────
def report_warehouse_activity() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """SELECT w.name AS warehouse, w.city,
                      COUNT(DISTINCT s.shipment_id) AS total_shipments,
                      COUNT(DISTINCT i.item_id)     AS inventory_lines,
                      COALESCE(SUM(i.quantity),0)   AS total_stock,
                      COUNT(DISTINCT v.vehicle_id)  AS vehicles_assigned
               FROM Warehouses w
               LEFT JOIN Shipments s  ON s.warehouse_id = w.warehouse_id
               LEFT JOIN Inventory i  ON i.warehouse_id = w.warehouse_id
               LEFT JOIN Vehicles v   ON v.warehouse_id = w.warehouse_id
               GROUP BY w.warehouse_id
               ORDER BY w.name""",
            conn
        )
        return df
    finally:
        conn.close()


# ── Driver performance ────────────────────────────────────────────────────────
def report_driver_performance() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """SELECT u.full_name AS driver,
                      d.license_number, d.status,
                      COUNT(s.shipment_id)                                  AS total_assigned,
                      SUM(CASE WHEN s.status='delivered' THEN 1 ELSE 0 END) AS delivered,
                      SUM(CASE WHEN s.status='delayed'   THEN 1 ELSE 0 END) AS delayed,
                      SUM(CASE WHEN s.status='returned'  THEN 1 ELSE 0 END) AS returned
               FROM Drivers d
               JOIN Users u ON d.user_id = u.user_id
               LEFT JOIN Shipments s ON s.driver_id = d.driver_id
               GROUP BY d.driver_id
               ORDER BY delivered DESC""",
            conn
        )
        return df
    finally:
        conn.close()


# ── Export CSV ────────────────────────────────────────────────────────────────
def export_report_csv(df: pd.DataFrame, report_name: str) -> str:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"{report_name}_{ts}.csv")
    df.to_csv(path, index=False)
    write_audit_log("EXPORT_REPORT", description=f"Exported: {path}")
    return path


# ── Audit log viewer ──────────────────────────────────────────────────────────
def get_audit_logs(limit: int = 200) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT a.*, u.username
               FROM AuditLogs a
               LEFT JOIN Users u ON a.user_id = u.user_id
               ORDER BY a.timestamp DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    finally:
        conn.close()


# ── User management ───────────────────────────────────────────────────────────
def get_all_users() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT user_id, username, full_name, role, email, is_active, created_at "
            "FROM Users ORDER BY role, full_name"
        ).fetchall()
    finally:
        conn.close()


def toggle_user_active(user_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE Users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END "
            "WHERE user_id=?", (user_id,)
        )
        conn.commit()
        write_audit_log("TOGGLE_USER", "Users", user_id)
    finally:
        conn.close()
