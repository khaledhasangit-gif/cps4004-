# Northshore Logistics Ltd — Database Management System
## CPS4004 – Database Systems | St Mary's University Twickenham

---

## Project Overview

A fully functional database-driven management system built in Python + SQLite3
for Northshore Logistics Ltd. The system centralises shipments, inventory,
fleet management, driver records, incident reporting, and reporting under a
single Tkinter GUI application with role-based access control.

---

## Quick Start (3 Steps)

### Step 1 – Create and activate virtual environment

**Windows:**
```
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```
python3 -m venv venv
source venv/bin/activate
```

### Step 2 – Install dependencies
```
pip install -r requirements.txt
```

### Step 3 – Run the application
```
python app/main.py
```

The database (`data/northshore.db`) is created automatically on first run
and seeded with realistic demonstration data.

---

## Demo Login Accounts

| Username  | Password       | Role    | Access Level               |
|-----------|----------------|---------|----------------------------|
| admin     | Admin2024!     | Admin   | Full access + user mgmt    |
| manager1  | Manager2024!   | Manager | All features, no user mgmt |
| staff1    | Staff2024!     | Staff   | Shipments, inventory, incidents |
| driver1   | Driver2024!    | Driver  | View shipments + incidents |

---

## Project Structure

```
northshore_logistics/
├── app/
│   ├── main.py              ← Entry point (run this)
│   ├── database.py          ← Schema, connections, seed data
│   ├── auth.py              ← Login, sessions, RBAC
│   ├── models/
│   │   ├── shipments.py     ← Shipment + delivery CRUD
│   │   ├── inventory.py     ← Inventory CRUD + stock adjust
│   │   ├── fleet.py         ← Vehicles, drivers, warehouses
│   │   └── reports.py       ← Pandas reports, incidents, audit
│   └── ui/
│       ├── styles.py         ← Colour palette, fonts, widget helpers
│       ├── login_window.py   ← Login screen
│       ├── main_window.py    ← Main window + tab container
│       ├── dashboard_tab.py  ← KPI cards + summary
│       ├── shipments_tab.py  ← Shipments CRUD
│       ├── inventory_tab.py  ← Inventory management
│       ├── fleet_tab.py      ← Vehicles, drivers, warehouses
│       ├── incidents_tab.py  ← Incident reports + resolution
│       ├── reports_tab.py    ← Pandas reports + audit log
│       └── admin_tab.py      ← User management (admin only)
├── data/
│   └── northshore.db        ← SQLite database (auto-created)
├── logs/
│   └── audit.log            ← Application audit log (auto-created)
├── reports/                 ← CSV exports saved here
├── requirements.txt
└── README.md
```

---

## Database Schema (9 Tables)

| Table       | Purpose                                          |
|-------------|--------------------------------------------------|
| Users       | System users with roles (admin/manager/staff/driver) |
| Warehouses  | Warehouse locations and capacity                 |
| Inventory   | Stock items with reorder levels per warehouse    |
| Vehicles    | Fleet vehicles with maintenance schedules        |
| Drivers     | Driver records linked to user accounts           |
| Shipments   | Full shipment lifecycle management               |
| Deliveries  | Delivery assignment and progress tracking        |
| Incidents   | Incident reports (delays, damage, etc.)          |
| AuditLogs   | All system actions logged automatically          |

**15 indexes** on foreign keys and frequently queried columns ensure
performance at scale.

---

## Security Features

- **Password hashing**: SHA-256 with per-user random salt (hashlib + secrets)
- **RBAC**: 4 roles — admin, manager, staff, driver — each with a precise
  permission set enforced at both model and UI layer
- **Audit logging**: Every create / update / delete / login action is
  recorded to both `AuditLogs` table and `logs/audit.log`
- **Account management**: Admin can activate / deactivate accounts

---

## Libraries Used (all permitted)

| Library  | Purpose                                 |
|----------|-----------------------------------------|
| sqlite3  | Database engine                         |
| tkinter  | Graphical user interface                |
| pandas   | Report generation and CSV export        |
| hashlib  | SHA-256 password hashing                |
| secrets  | Cryptographic salt generation           |
| logging  | File-based audit logging                |
| datetime | Timestamps for records and filenames    |

---

## Submission Checklist

- [ ] `python app/main.py` starts without errors
- [ ] All 4 login roles work correctly
- [ ] Shipments: add, edit, delete, filter, search
- [ ] Inventory: add, edit, delete, adjust stock, low-stock view
- [ ] Fleet: vehicles, drivers, warehouses management
- [ ] Incidents: report and resolve
- [ ] Reports: run and export all 4 pandas reports
- [ ] Audit log: visible in Reports → Audit Log tab
- [ ] ZIP file contains: source code + `git log` output
- [ ] PDF report submitted separately (not in ZIP)

---

## Version Control (Git)

Initialise and commit:
```
git init
git add .
git commit -m "Initial commit: Northshore Logistics DMS — full implementation"
git checkout -b feature/reports
# ... develop ...
git commit -m "Add pandas report generation and CSV export"
git checkout main
git merge feature/reports
git log --oneline > git_log.txt
```

Include `git_log.txt` in your ZIP submission.

---

## Requirements

- Python 3.11 or later
- pandas 2.0+
- tkinter (included in standard Python installation)
- All other dependencies are Python standard library
