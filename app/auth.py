"""
auth.py — Northshore Logistics Ltd
Authentication, session management, and Role-Based Access Control (RBAC).
CPS4004 – Database Systems | St Mary's University Twickenham
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.database import get_connection, verify_password

logger = logging.getLogger(__name__)

# ── Role permission matrix ───────────────────────────────────────────────────
PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "view_shipments", "add_shipment", "edit_shipment", "delete_shipment",
        "view_inventory", "add_inventory", "edit_inventory", "delete_inventory",
        "view_vehicles",  "add_vehicle",  "edit_vehicle",  "delete_vehicle",
        "view_drivers",   "add_driver",   "edit_driver",   "delete_driver",
        "view_incidents", "add_incident", "resolve_incident",
        "view_reports",   "export_reports",
        "view_users",     "add_user",     "edit_user",     "delete_user",
        "view_audit_logs",
    },
    "manager": {
        "view_shipments", "add_shipment", "edit_shipment",
        "view_inventory", "add_inventory", "edit_inventory",
        "view_vehicles",  "add_vehicle",  "edit_vehicle",
        "view_drivers",   "add_driver",   "edit_driver",
        "view_incidents", "add_incident", "resolve_incident",
        "view_reports",   "export_reports",
        "view_users",
        "view_audit_logs",
    },
    "staff": {
        "view_shipments", "add_shipment", "edit_shipment",
        "view_inventory", "edit_inventory",
        "view_vehicles",
        "view_drivers",
        "view_incidents", "add_incident",
        "view_reports",
    },
    "driver": {
        "view_shipments",
        "view_incidents", "add_incident",
    },
}


@dataclass
class Session:
    """Holds the currently logged-in user's data for the lifetime of the app."""
    user_id:   int
    username:  str
    full_name: str
    role:      str
    _perms:    set[str] = field(default_factory=set, repr=False)

    def __post_init__(self):
        self._perms = PERMISSIONS.get(self.role, set())

    def can(self, permission: str) -> bool:
        return permission in self._perms

    def require(self, permission: str) -> None:
        if not self.can(permission):
            raise PermissionError(
                f"User '{self.username}' (role: {self.role}) "
                f"lacks permission: '{permission}'"
            )


# ── Module-level session (None until login) ──────────────────────────────────
_current_session: Optional[Session] = None


def get_session() -> Optional[Session]:
    return _current_session


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (True, '') on success or (False, reason) on failure.
    Writes to audit log on both outcomes.
    """
    global _current_session
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, username, full_name, role, password_hash, salt, is_active "
            "FROM Users WHERE username = ?",
            (username.strip(),)
        ).fetchone()

        if row is None:
            logger.warning("LOGIN FAILED — unknown username: %s", username)
            return False, "Username not found."

        if not row["is_active"]:
            logger.warning("LOGIN FAILED — inactive account: %s", username)
            return False, "Account is deactivated. Contact your administrator."

        if not verify_password(password, row["password_hash"], row["salt"]):
            logger.warning("LOGIN FAILED — wrong password for: %s", username)
            _write_audit(conn, row["user_id"], "LOGIN_FAILED", description="Incorrect password.")
            conn.commit()
            return False, "Incorrect password."

        _current_session = Session(
            user_id=row["user_id"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
        )
        _write_audit(conn, row["user_id"], "LOGIN_SUCCESS", description="User logged in.")
        conn.commit()
        logger.info("LOGIN SUCCESS — %s (%s)", username, row["role"])
        return True, ""

    except Exception as exc:
        logger.error("Login error: %s", exc)
        return False, "An unexpected error occurred."
    finally:
        conn.close()


def logout() -> None:
    global _current_session
    if _current_session:
        conn = get_connection()
        try:
            _write_audit(conn, _current_session.user_id, "LOGOUT",
                         description="User logged out.")
            conn.commit()
        finally:
            conn.close()
        logger.info("LOGOUT — %s", _current_session.username)
    _current_session = None


def _write_audit(conn, user_id: int, action: str,
                 table_name: str = None, record_id: int = None,
                 description: str = None) -> None:
    conn.execute(
        "INSERT INTO AuditLogs (user_id,action,table_name,record_id,description) "
        "VALUES (?,?,?,?,?)",
        (user_id, action, table_name, record_id, description)
    )


def write_audit_log(action: str, table_name: str = None,
                    record_id: int = None, description: str = None) -> None:
    """Public helper — write an audit entry for the current session."""
    sess = get_session()
    uid = sess.user_id if sess else None
    conn = get_connection()
    try:
        _write_audit(conn, uid, action, table_name, record_id, description)
        conn.commit()
    finally:
        conn.close()
