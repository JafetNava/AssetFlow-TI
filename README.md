# AssetFlow TI

AssetFlow TI is a local IT asset management system built with Flask and SQLite.

The project is designed to centralize equipment inventory, employee assignments, maintenance records, responsibility forms, activity history, reports, and database backups in a lightweight application that can run locally without requiring paid cloud infrastructure.

> This is a portfolio project. All data included in the project or seed files is fictional and used for demonstration purposes only.

---

## Overview

AssetFlow TI was created as a practical solution for IT support teams that need a simple way to manage company equipment without relying on expensive asset management platforms.

The application provides a centralized interface for tracking IT equipment throughout its lifecycle, from inventory registration to employee assignment, maintenance, return, reassignment, and retirement.

The system currently focuses primarily on computer equipment while maintaining an architecture that can be expanded to additional IT asset categories.

---

## Features

### Dashboard

Provides a general overview of the IT environment, including:

- Total equipment
- Assigned equipment
- Available equipment
- Equipment under maintenance
- Active employees
- Overdue maintenance
- Upcoming maintenance
- Pending responsibility forms
- Recent assignments
- Upcoming maintenance events

### Inventory Management

Manage IT equipment information such as:

- Asset code
- Equipment type
- Brand
- Model
- Serial number
- Charger serial number
- Processor
- RAM
- Operating system
- Wi-Fi MAC address
- Ethernet MAC address
- Fixed asset number
- Invoice
- Purchase order
- Purchase information
- Warranty information
- Equipment status
- Comments

Supported equipment statuses include:

- Available
- Assigned
- Maintenance
- Storage
- Retired
- Lost
- Stolen

### Employee Management

Maintain employee records including:

- Employee name
- Position
- Area
- Business line
- Site
- City
- Office
- Direct supervisor
- Active / inactive status

Each employee profile can also display:

- Currently assigned equipment
- Assignment history

### Equipment Assignments

AssetFlow TI maintains assignment history between employees and equipment.

Supported operations include:

- Assign available equipment
- Return equipment
- Reassign equipment
- View active assignments
- View finalized assignments
- Preserve historical assignment records

Equipment status is automatically updated when assignment operations are performed.

### Responsibility Forms

Responsibility forms can be generated directly from active equipment assignments.

The application:

- Generates unique responsibility form numbers
- Creates PDF documents
- Stores generated documents locally
- Allows PDF downloads
- Tracks form status

Available statuses:

- Generated
- Signed
- Cancelled

PDF generation is implemented using ReportLab.

### Maintenance Management

The system maintains equipment maintenance history including:

- Maintenance date
- Next maintenance date
- Maintenance type
- Description
- Technician
- Observations

Maintenance records are automatically classified as:

- Overdue
- Due Soon
- Scheduled
- No Schedule

### Activity Log

Important asset operations are recorded in an activity log.

Tracked events include:

- Equipment creation
- Equipment updates
- Assignments
- Returns
- Reassignments
- Maintenance

Each movement can contain:

- Equipment
- Event type
- Description
- Previous value
- New value
- Timestamp

This provides basic asset lifecycle traceability.

### Excel Reports

AssetFlow TI can generate Excel reports using OpenPyXL.

Available exports include:

- Inventory
- Employees
- Assignments
- Maintenance

Generated spreadsheets include formatted headers, filters, frozen panes, and adjusted column widths.

### Database Backups

The system includes SQLite database backup functionality.

Features include:

- Manual backups
- Automatic daily backup
- Native SQLite backup API
- Backup history
- Backup downloads
- Automatic cleanup of old backups

By default, a limited number of backup files are retained.

---

## Technology Stack

### Backend

- Python
- Flask
- SQLite

### Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2

### Data and Reporting

- OpenPyXL
- Pandas
- ReportLab

### Development Tools

- Git
- GitHub
- Visual Studio Code

---

## Project Structure

```text
AssetFlow-TI/
│
├── backups/
│   └── .gitkeep
│
├── database/
│   └── schema.sql
│
├── exports/
│   └── .gitkeep
│
├── responsivas/
│   └── .gitkeep
│
├── services/
│   ├── __init__.py
│   ├── backup_service.py
│   ├── excel_export_service.py
│   ├── movement_service.py
│   └── responsibility_form_service.py
│
├── static/
│   ├── css/
│   │   └── styles.css
│   │
│   └── js/
│       └── app.js
│
├── templates/
│   ├── activity.html
│   ├── assignment_form.html
│   ├── assignments.html
│   ├── backups.html
│   ├── base.html
│   ├── employee_detail.html
│   ├── employee_form.html
│   ├── employees.html
│   ├── equipment_detail.html
│   ├── equipment_form.html
│   ├── index.html
│   ├── inventory.html
│   ├── maintenance.html
│   ├── maintenance_form.html
│   ├── reassign_form.html
│   ├── reports.html
│   ├── responsibility_form_new.html
│   └── responsibility_forms.html
│
├── .gitignore
├── app.py
├── init_db.py
├── requirements.txt
└── seed.py
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/JafetNava/AssetFlow-TI.git
```

Navigate to the project directory:

```bash
cd AssetFlow-TI
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Initialize the database

```powershell
python init_db.py
```

This creates the local SQLite database using:

```text
database/schema.sql
```

### 5. Load demo data

Optional:

```powershell
python seed.py
```

The seed script inserts fictional records that can be used to explore the application.

### 6. Start the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## Database

AssetFlow TI uses SQLite as its local relational database.

Main entities include:

```text
Employees
Computers
Assignments
Maintenance
AssetAcknowledgements
AssetMovements
```

Foreign keys are enabled to preserve relational integrity.

The generated SQLite database is intentionally excluded from Git using `.gitignore`.

A new database can be recreated using:

```powershell
python init_db.py
```

---

## Screenshots

Screenshots will be added to demonstrate the main modules of the system.

Planned examples:

```text
Dashboard
Inventory
Equipment Detail
Employees
Assignments
Responsibility Forms
Maintenance
Reports
Backups
Activity Log
```

---

## Example Workflow

A typical equipment lifecycle in AssetFlow TI can follow this process:

```text
Register Equipment
        ↓
Available
        ↓
Assign to Employee
        ↓
Assigned
        ↓
Generate Responsibility Form
        ↓
Maintenance / Activity Tracking
        ↓
Return or Reassign
        ↓
Available
```

Asset movements are recorded throughout the process to maintain historical traceability.

---

## Security and Deployment Model

AssetFlow TI is currently designed as a local application.

By default, Flask runs on:

```text
127.0.0.1:5000
```

This means the application is accessible only from the local computer unless its network configuration is explicitly changed.

Generated databases, backups, reports, and PDF files are excluded from the Git repository.

---

## Future Improvements

Possible future enhancements include:

- Generalized IT asset model
- Support for mobile devices and peripherals
- Excel inventory import
- Advanced validation
- Detailed field-level audit history
- Multiple assets per responsibility form
- Backup restoration
- User authentication
- Role-based permissions
- Improved dashboard analytics
- Asset lifecycle reports
- Warranty alerts
- Maintenance notifications
- QR code asset identification
- Barcode support
- Modular Flask Blueprints architecture
- Automated testing
- Local executable packaging

---

## Project Purpose

AssetFlow TI was developed as a portfolio project to demonstrate practical skills in:

- Backend development with Python and Flask
- Relational database design
- SQL
- CRUD application development
- Data validation
- Asset lifecycle management
- Excel report generation
- PDF document generation
- Database backup strategies
- Frontend development
- Application architecture
- Git version control

The project focuses on solving a realistic IT support and asset management use case using accessible open-source technologies.

---

## Disclaimer

This repository is a portfolio and demonstration project.

All employees, equipment, serial numbers, asset information, assignments, and other records included in demo or seed data are fictional.

No real company information is included.

---

## Author

**Jafet Nava**

Portfolio project focused on data, automation, application development, and IT asset management.