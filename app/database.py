"""
database.py — Northshore Logistics Ltd
Handles all SQLite3 connection management, schema creation,
index creation, and initial seed data.
CPS4004 – Database Systems | St Mary's University Twickenham
"""

import sqlite3
import hashlib
import secrets
import logging
import os
from datetime import datetime, date, timedelta

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(BASE_DIR, "data", "northshore.db")
LOG_PATH  = os.path.join(BASE_DIR, "logs", "audit.log")

# ── Module-level logger ──────────────────────────────────────────────────────
os.makedirs(os.path.dirname(DB_PATH),  exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Connection factory ───────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with FK enforcement."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")   # better concurrent reads
    conn.row_factory = sqlite3.Row               # dict-like row access
    return conn


# ── Schema DDL ───────────────────────────────────────────────────────────────
SCHEMA_SQL = """
-- ── 1. Users (RBAC) ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    salt           TEXT    NOT NULL,
    role           TEXT    NOT NULL CHECK(role IN ('admin','manager','staff','driver')),
    full_name      TEXT    NOT NULL,
    email          TEXT    UNIQUE,
    phone          TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── 2. Warehouses ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Warehouses (
    warehouse_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    address       TEXT    NOT NULL,
    city          TEXT    NOT NULL,
    postcode      TEXT,
    capacity      INTEGER NOT NULL DEFAULT 0,
    manager_id    INTEGER REFERENCES Users(user_id) ON DELETE SET NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── 3. Inventory ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Inventory (
    item_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name         TEXT    NOT NULL,
    sku               TEXT    NOT NULL UNIQUE,
    quantity          INTEGER NOT NULL DEFAULT 0,
    reorder_level     INTEGER NOT NULL DEFAULT 10,
    unit_price        REAL    NOT NULL DEFAULT 0.0,
    warehouse_id      INTEGER NOT NULL REFERENCES Warehouses(warehouse_id) ON DELETE CASCADE,
    location_in_wh    TEXT,
    last_updated      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── 4. Vehicles ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Vehicles (
    vehicle_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    registration     TEXT    NOT NULL UNIQUE,
    make             TEXT    NOT NULL,
    model            TEXT    NOT NULL,
    capacity_kg      REAL    NOT NULL DEFAULT 0.0,
    status           TEXT    NOT NULL DEFAULT 'available'
                             CHECK(status IN ('available','in_use','maintenance','retired')),
    last_maintenance TEXT,
    next_maintenance TEXT,
    warehouse_id     INTEGER REFERENCES Warehouses(warehouse_id) ON DELETE SET NULL
);

-- ── 5. Drivers ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Drivers (
    driver_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES Users(user_id) ON DELETE CASCADE,
    license_number  TEXT    NOT NULL UNIQUE,
    license_expiry  TEXT    NOT NULL,
    phone           TEXT,
    address         TEXT,
    status          TEXT    NOT NULL DEFAULT 'available'
                            CHECK(status IN ('available','on_route','off_duty','suspended'))
);

-- ── 6. Shipments ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Shipments (
    shipment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_ref     TEXT    NOT NULL UNIQUE,
    order_number     TEXT    NOT NULL,
    sender_name      TEXT    NOT NULL,
    sender_address   TEXT    NOT NULL,
    receiver_name    TEXT    NOT NULL,
    receiver_address TEXT    NOT NULL,
    item_description TEXT    NOT NULL,
    weight_kg        REAL    NOT NULL DEFAULT 0.0,
    transport_cost   REAL    NOT NULL DEFAULT 0.0,
    surcharge        REAL    NOT NULL DEFAULT 0.0,
    payment_status   TEXT    NOT NULL DEFAULT 'pending'
                             CHECK(payment_status IN ('paid','pending','overdue')),
    status           TEXT    NOT NULL DEFAULT 'pending'
                             CHECK(status IN ('pending','in_transit','delivered','delayed','returned')),
    warehouse_id     INTEGER REFERENCES Warehouses(warehouse_id) ON DELETE SET NULL,
    vehicle_id       INTEGER REFERENCES Vehicles(vehicle_id)     ON DELETE SET NULL,
    driver_id        INTEGER REFERENCES Drivers(driver_id)       ON DELETE SET NULL,
    created_by       INTEGER REFERENCES Users(user_id)           ON DELETE SET NULL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── 7. Deliveries ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Deliveries (
    delivery_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id         INTEGER NOT NULL UNIQUE REFERENCES Shipments(shipment_id) ON DELETE CASCADE,
    driver_id           INTEGER REFERENCES Drivers(driver_id)  ON DELETE SET NULL,
    vehicle_id          INTEGER REFERENCES Vehicles(vehicle_id) ON DELETE SET NULL,
    route_details       TEXT,
    scheduled_date      TEXT,
    actual_delivery_date TEXT,
    delivery_status     TEXT    NOT NULL DEFAULT 'pending'
                                CHECK(delivery_status IN ('pending','in_transit','delivered','failed')),
    notes               TEXT
);

-- ── 8. Incidents ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Incidents (
    incident_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id     INTEGER NOT NULL REFERENCES Shipments(shipment_id) ON DELETE CASCADE,
    reported_by     INTEGER REFERENCES Users(user_id) ON DELETE SET NULL,
    incident_type   TEXT    NOT NULL
                            CHECK(incident_type IN ('delay','route_change','damaged','failed_delivery','other')),
    description     TEXT    NOT NULL,
    reported_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT,
    resolution_notes TEXT
);

-- ── 9. AuditLogs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS AuditLogs (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES Users(user_id) ON DELETE SET NULL,
    action      TEXT    NOT NULL,
    table_name  TEXT,
    record_id   INTEGER,
    description TEXT,
    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# ── Index DDL ────────────────────────────────────────────────────────────────
INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse   ON Inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_inventory_sku         ON Inventory(sku);
CREATE INDEX IF NOT EXISTS idx_vehicles_status       ON Vehicles(status);
CREATE INDEX IF NOT EXISTS idx_vehicles_warehouse    ON Vehicles(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_drivers_status        ON Drivers(status);
CREATE INDEX IF NOT EXISTS idx_shipments_status      ON Shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_warehouse   ON Shipments(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_shipments_driver      ON Shipments(driver_id);
CREATE INDEX IF NOT EXISTS idx_shipments_created_at  ON Shipments(created_at);
CREATE INDEX IF NOT EXISTS idx_shipments_ref         ON Shipments(shipment_ref);
CREATE INDEX IF NOT EXISTS idx_deliveries_shipment   ON Deliveries(shipment_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_driver     ON Deliveries(driver_id);
CREATE INDEX IF NOT EXISTS idx_incidents_shipment    ON Incidents(shipment_id);
CREATE INDEX IF NOT EXISTS idx_auditlogs_user        ON AuditLogs(user_id);
CREATE INDEX IF NOT EXISTS idx_auditlogs_timestamp   ON AuditLogs(timestamp);
"""


# ── Password utilities ───────────────────────────────────────────────────────
def hash_password(password: str) -> tuple[str, str]:
    """Return (hash_hex, salt_hex) using SHA-256 + random salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return pw_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a plain password against stored hash+salt."""
    check = hashlib.sha256((salt + password).encode()).hexdigest()
    return check == stored_hash


# ── Initialise DB ────────────────────────────────────────────────────────────
def initialise_database() -> None:
    """Create all tables, indexes and seed data if the DB is fresh."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executescript(SCHEMA_SQL)
        cur.executescript(INDEXES_SQL)
        conn.commit()
        _seed_if_empty(conn)
        logger.info("Database initialised successfully.")
    except sqlite3.Error as exc:
        logger.error("Database initialisation failed: %s", exc)
        raise
    finally:
        conn.close()


# ── Seed data ────────────────────────────────────────────────────────────────
def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Populate default rows only when the database is brand new."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Users")
    if cur.fetchone()[0] > 0:
        return   # already seeded

    logger.info("Seeding fresh database …")

    # ── Users ────────────────────────────────────────────────────────────────
    users = [
        ("admin",    "Admin2024!",  "admin",   "System Administrator",  "admin@northshore.co.uk"),
        ("manager1", "Manager2024!", "manager", "Sarah Thompson",        "s.thompson@northshore.co.uk"),
        ("manager2", "Manager2024!", "manager", "David Clarke",          "d.clarke@northshore.co.uk"),
        ("staff1",   "Staff2024!",   "staff",   "Emma Wilson",           "e.wilson@northshore.co.uk"),
        ("staff2",   "Staff2024!",   "staff",   "James Brown",           "j.brown@northshore.co.uk"),
        ("driver1",  "Driver2024!",  "driver",  "Michael Ford",          "m.ford@northshore.co.uk"),
        ("driver2",  "Driver2024!",  "driver",  "Lisa Chen",             "l.chen@northshore.co.uk"),
        ("driver3",  "Driver2024!",  "driver",  "Robert Nash",           "r.nash@northshore.co.uk"),
    ]
    user_ids = {}
    for uname, pwd, role, fullname, email in users:
        pw_hash, salt = hash_password(pwd)
        cur.execute(
            "INSERT INTO Users (username,password_hash,salt,role,full_name,email) "
            "VALUES (?,?,?,?,?,?)",
            (uname, pw_hash, salt, role, fullname, email)
        )
        user_ids[uname] = cur.lastrowid

    # ── Warehouses ───────────────────────────────────────────────────────────
    warehouses = [
        ("London Central Hub",    "45 Commerce Road",    "London",     "EC1A 1BB", 5000, user_ids["manager1"]),
        ("Birmingham North Depot","12 Logistics Way",    "Birmingham", "B1 1BB",   3500, user_ids["manager2"]),
        ("Manchester West Hub",   "78 Distribution Lane","Manchester", "M1 1AA",   4000, user_ids["manager1"]),
    ]
    wh_ids = {}
    for name, addr, city, pc, cap, mgr in warehouses:
        cur.execute(
            "INSERT INTO Warehouses (name,address,city,postcode,capacity,manager_id) "
            "VALUES (?,?,?,?,?,?)",
            (name, addr, city, pc, cap, mgr)
        )
        wh_ids[name] = cur.lastrowid

    wh1 = wh_ids["London Central Hub"]
    wh2 = wh_ids["Birmingham North Depot"]
    wh3 = wh_ids["Manchester West Hub"]

    # ── Inventory ────────────────────────────────────────────────────────────
    items = [
        ("Cardboard Box (Small)",  "SKU-001", 500, 50, 0.50, wh1, "Aisle A1"),
        ("Cardboard Box (Large)",  "SKU-002", 300, 30, 0.80, wh1, "Aisle A2"),
        ("Bubble Wrap Roll 50m",   "SKU-003", 120, 20, 4.99, wh2, "Aisle B1"),
        ("Pallet Shrink Wrap",     "SKU-004",  80, 15, 9.99, wh2, "Aisle B2"),
        ("Parcel Tape 48mm",       "SKU-005", 600, 100,0.99, wh3, "Aisle C1"),
        ("Fragile Stickers (100)", "SKU-006", 200, 40, 1.49, wh1, "Aisle A3"),
        ("Foam Padding Sheet",     "SKU-007",  90, 20, 2.99, wh3, "Aisle C2"),
        ("Wooden Pallet",          "SKU-008",  50,  5,12.00, wh2, "Yard B"),
    ]
    for name, sku, qty, reorder, price, wid, loc in items:
        cur.execute(
            "INSERT INTO Inventory (item_name,sku,quantity,reorder_level,unit_price,warehouse_id,location_in_wh) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, sku, qty, reorder, price, wid, loc)
        )

    # ── Vehicles ─────────────────────────────────────────────────────────────
    vehicles = [
        ("LN21 ABC", "Ford",   "Transit 350",  1200, "available",  "2024-01-15", "2025-01-15", wh1),
        ("LN21 XYZ", "Vauxhall","Movano L3H2", 1500, "available",  "2024-03-20", "2025-03-20", wh1),
        ("BM22 DEF", "Mercedes","Sprinter 516", 2500, "in_use",    "2024-02-10", "2025-02-10", wh2),
        ("BM22 GHI", "Ford",   "Custom 340",   1000, "maintenance","2023-11-01", "2024-11-01", wh2),
        ("MC23 JKL", "Renault","Master L3H2",  1400, "available",  "2024-04-05", "2025-04-05", wh3),
        ("MC23 MNO", "VW",     "Crafter 35",   1800, "available",  "2024-04-01", "2025-04-01", wh3),
    ]
    veh_ids = []
    for reg, make, model, cap, status, lm, nm, wid in vehicles:
        cur.execute(
            "INSERT INTO Vehicles (registration,make,model,capacity_kg,status,last_maintenance,next_maintenance,warehouse_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (reg, make, model, cap, status, lm, nm, wid)
        )
        veh_ids.append(cur.lastrowid)

    # ── Drivers ──────────────────────────────────────────────────────────────
    drivers_data = [
        (user_ids["driver1"], "DL-UK-001234", "2027-06-30", "07700900001", "12 Oak Street, London"),
        (user_ids["driver2"], "DL-UK-005678", "2026-12-31", "07700900002", "34 Elm Road, Birmingham"),
        (user_ids["driver3"], "DL-UK-009012", "2028-03-15", "07700900003", "56 Pine Ave, Manchester"),
    ]
    drv_ids = []
    for uid, lic, exp, phone, addr in drivers_data:
        cur.execute(
            "INSERT INTO Drivers (user_id,license_number,license_expiry,phone,address) "
            "VALUES (?,?,?,?,?)",
            (uid, lic, exp, phone, addr)
        )
        drv_ids.append(cur.lastrowid)

    # ── Shipments ────────────────────────────────────────────────────────────
    today = date.today()
    shipments = [
        ("SHP-2024-001","ORD-10001","Acme Corp","1 High St, London","Beta Ltd","5 Low Rd, Leeds",
         "Office Furniture",  85.0, 120.00, 10.00,"paid",     "delivered", wh1, veh_ids[0], drv_ids[0], user_ids["staff1"]),
        ("SHP-2024-002","ORD-10002","TechStart","22 King St, Manchester","DataCo","9 Queen Rd, Bristol",
         "Server Equipment",  40.0, 95.00,  0.00, "paid",     "delivered", wh3, veh_ids[4], drv_ids[2], user_ids["staff1"]),
        ("SHP-2024-003","ORD-10003","BuildCo",  "8 Park Ave, Birmingham","FixIt Ltd","3 New St, Coventry",
         "Construction Tools",120.0,145.00, 15.00,"pending",  "in_transit",wh2, veh_ids[2], drv_ids[1], user_ids["staff2"]),
        ("SHP-2024-004","ORD-10004","MedSupply","14 Heath Rd, London","GreenCross","7 Well Rd, Oxford",
         "Medical Supplies",   22.0, 75.00, 5.00, "pending",  "pending",   wh1, None,       None,       user_ids["staff2"]),
        ("SHP-2024-005","ORD-10005","RetailX",  "33 Market St, Leeds","FashionY","11 Style Ave, London",
         "Clothing (Seasonal)",60.0, 88.00, 0.00, "overdue",  "delayed",   wh3, veh_ids[5], drv_ids[2], user_ids["staff1"]),
        ("SHP-2024-006","ORD-10006","FoodCo",   "2 Farm Rd, Birmingham","Deli Ltd","6 Taste St, Nottm",
         "Food Products (Dry)",200.0,180.00,20.00,"paid",     "delivered", wh2, veh_ids[1], drv_ids[0], user_ids["staff2"]),
    ]
    shp_ids = []
    for row in shipments:
        cur.execute(
            "INSERT INTO Shipments (shipment_ref,order_number,sender_name,sender_address,"
            "receiver_name,receiver_address,item_description,weight_kg,transport_cost,surcharge,"
            "payment_status,status,warehouse_id,vehicle_id,driver_id,created_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            row
        )
        shp_ids.append(cur.lastrowid)

    # ── Deliveries ───────────────────────────────────────────────────────────
    deliveries = [
        (shp_ids[0], drv_ids[0], veh_ids[0], "A1 → M1 → A58", str(today - timedelta(days=10)), str(today-timedelta(days=9)),  "delivered"),
        (shp_ids[1], drv_ids[2], veh_ids[4], "M60 → M6 → M5", str(today - timedelta(days=7)),  str(today-timedelta(days=6)),  "delivered"),
        (shp_ids[2], drv_ids[1], veh_ids[2], "M6 → A45",       str(today - timedelta(days=2)),  None,                          "in_transit"),
        (shp_ids[3], None,       None,        "TBD",             str(today + timedelta(days=3)),  None,                          "pending"),
        (shp_ids[4], drv_ids[2], veh_ids[5], "M1 → A1",        str(today - timedelta(days=1)),  None,                          "in_transit"),
        (shp_ids[5], drv_ids[0], veh_ids[1], "M6 → A38",       str(today - timedelta(days=5)),  str(today-timedelta(days=4)),  "delivered"),
    ]
    for shp_id, drv_id, veh_id, route, sched, actual, status in deliveries:
        cur.execute(
            "INSERT INTO Deliveries (shipment_id,driver_id,vehicle_id,route_details,"
            "scheduled_date,actual_delivery_date,delivery_status) VALUES (?,?,?,?,?,?,?)",
            (shp_id, drv_id, veh_id, route, sched, actual, status)
        )

    # ── Incidents ────────────────────────────────────────────────────────────
    cur.execute(
        "INSERT INTO Incidents (shipment_id,reported_by,incident_type,description,reported_at,resolution_notes) "
        "VALUES (?,?,?,?,?,?)",
        (shp_ids[4], user_ids["driver3"], "delay",
         "Traffic congestion on M1 near junction 28 causing 4-hour delay.",
         str(today - timedelta(days=1)), None)
    )

    # ── Seed audit log ───────────────────────────────────────────────────────
    cur.execute(
        "INSERT INTO AuditLogs (user_id,action,table_name,description) VALUES (?,?,?,?)",
        (user_ids["admin"], "SYSTEM_INIT", "ALL", "Database seeded with initial data.")
    )

    conn.commit()
    logger.info("Seed data inserted successfully.")
