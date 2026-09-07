import os
import sqlite3

from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    abort
)

from services.responsibility_form_service import (generate_responsibility_form)
from services.excel_export_service import (create_excel_report)
from services.movement_service import register_movement
from services.backup_service import (
    create_backup,
    list_backups,
    ensure_daily_backup
)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "DB_AssetFlow_TI.db"
)

BACKUP_DIRECTORY = os.path.join(
    BASE_DIR,
    "backups"
)

def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection

def generate_responsibility_number(connection):
    year = date.today().year

    result = connection.execute(
        """
        SELECT MAX(AcknowledgementID) AS LastID
        FROM AssetAcknowledgements
        """
    ).fetchone()

    last_id = result["LastID"]

    next_number = 1 if last_id is None else last_id + 1

    return f"RF-{year}-{next_number:04d}"

@app.route("/")
def index():
    connection = get_db_connection()

    total_computers = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Computers
        """
    ).fetchone()["Total"]

    assigned = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Computers
        WHERE Status = 'Assigned'
        """
    ).fetchone()["Total"]

    available = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Computers
        WHERE Status = 'Available'
        """
    ).fetchone()["Total"]

    maintenance = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Computers
        WHERE Status = 'Maintenance'
        """
    ).fetchone()["Total"]

    total_employees = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Employees
        WHERE Active = 1
        """
    ).fetchone()["Total"]

    overdue_maintenance = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Maintenance
        WHERE NextMaintenanceDate IS NOT NULL
        AND DATE(NextMaintenanceDate) < DATE('now', 'localtime')
        """
    ).fetchone()["Total"]

    due_soon_maintenance = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Maintenance
        WHERE NextMaintenanceDate IS NOT NULL
        AND DATE(NextMaintenanceDate) >= DATE('now', 'localtime')
        AND DATE(NextMaintenanceDate)
            <= DATE('now', 'localtime', '+30 days')
        """
    ).fetchone()["Total"]

    pending_forms = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM AssetAcknowledgements
        WHERE Status = 'Generated'
        """
    ).fetchone()["Total"]

    recent_assignments = connection.execute(
        """
        SELECT
            A.AssignmentID,
            A.AssignmentDate,
            A.Status,
            C.ComputerID,
            C.Code,
            C.Brand,
            C.Model,
            E.EmployeeName,
            A.Office
        FROM Assignments A
        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID
        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID
        ORDER BY A.AssignmentID DESC
        LIMIT 5
        """
    ).fetchall()

    upcoming_maintenance = connection.execute(
        """
        SELECT
            M.MaintenanceID,
            M.NextMaintenanceDate,
            M.MaintenanceType,
            C.ComputerID,
            C.Code,
            C.Brand,
            C.Model,

            CASE
                WHEN DATE(M.NextMaintenanceDate)
                    < DATE('now', 'localtime')
                    THEN 'Overdue'

                WHEN DATE(M.NextMaintenanceDate)
                    <= DATE('now', 'localtime', '+30 days')
                    THEN 'Due Soon'

                ELSE 'Scheduled'
            END AS MaintenanceStatus

        FROM Maintenance M

        INNER JOIN Computers C
            ON M.ComputerID = C.ComputerID

        WHERE M.NextMaintenanceDate IS NOT NULL

        ORDER BY
            M.NextMaintenanceDate ASC

        LIMIT 5
        """
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        total_computers=total_computers,
        assigned=assigned,
        available=available,
        maintenance=maintenance,
        total_employees=total_employees,
        overdue_maintenance=overdue_maintenance,
        due_soon_maintenance=due_soon_maintenance,
        pending_forms=pending_forms,
        recent_assignments=recent_assignments,
        upcoming_maintenance=upcoming_maintenance,
        active_page="dashboard"
    )

@app.route("/inventory")
def inventory():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    equipment_type = request.args.get("type", "").strip()
    brand = request.args.get("brand", "").strip()

    connection = get_db_connection()

    query = """
        SELECT
            ComputerID,
            Code,
            Type,
            Brand,
            Model,
            SerialNumber,
            FixedAsset,
            Processor,
            RAM,
            OperatingSystem,
            Status
        FROM Computers
        WHERE 1 = 1
    """

    params = []

    if search:
        query += """
            AND (
                Code LIKE ?
                OR SerialNumber LIKE ?
                OR Brand LIKE ?
                OR Model LIKE ?
                OR FixedAsset LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status:
        query += " AND Status = ?"
        params.append(status)

    if equipment_type:
        query += " AND Type = ?"
        params.append(equipment_type)

    if brand:
        query += " AND Brand = ?"
        params.append(brand)

    query += " ORDER BY ComputerID DESC"

    computers = connection.execute(
        query,
        params
    ).fetchall()

    statuses = connection.execute(
        """
        SELECT DISTINCT Status
        FROM Computers
        WHERE Status IS NOT NULL
        ORDER BY Status
        """
    ).fetchall()

    types = connection.execute(
        """
        SELECT DISTINCT Type
        FROM Computers
        WHERE Type IS NOT NULL
        ORDER BY Type
        """
    ).fetchall()

    brands = connection.execute(
        """
        SELECT DISTINCT Brand
        FROM Computers
        WHERE Brand IS NOT NULL
        ORDER BY Brand
        """
    ).fetchall()

    connection.close()

    return render_template(
        "inventory.html",
        computers=computers,
        statuses=statuses,
        types=types,
        brands=brands,
        search=search,
        selected_status=status,
        selected_type=equipment_type,
        selected_brand=brand,
        active_page="inventory"
    )

@app.route("/inventory/<int:computer_id>")
def equipment_detail(computer_id):
    connection = get_db_connection()

    computer = connection.execute(
        """
        SELECT *
        FROM Computers
        WHERE ComputerID = ?
        """,
        (computer_id,)
    ).fetchone()

    assignment = connection.execute(
        """
        SELECT
            A.AssignmentDate,
            A.Office,
            A.Status AS AssignmentStatus,
            E.EmployeeName,
            E.Position,
            E.Area
        FROM Assignments A
        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID
        WHERE A.ComputerID = ?
        AND A.Status = 'Active'
        ORDER BY A.AssignmentID DESC
        LIMIT 1
        """,
        (computer_id,)
    ).fetchone()

    maintenance = connection.execute(
        """
        SELECT
            MaintenanceDate,
            NextMaintenanceDate,
            MaintenanceType,
            Technician,
            Observations
        FROM Maintenance
        WHERE ComputerID = ?
        ORDER BY MaintenanceDate DESC
        LIMIT 1
        """,
        (computer_id,)
    ).fetchone()

    movements = connection.execute(
        """
        SELECT
            MovementID,
            MovementType,
            Description,
            PreviousValue,
            NewValue,
            MovementDate
        FROM AssetMovements
        WHERE ComputerID = ?
        ORDER BY MovementDate DESC,
                MovementID DESC
        LIMIT 20
        """,
        (computer_id,)
    ).fetchall()

    connection.close()

    if computer is None:
        return "Equipment not found", 404

    return render_template(
        "equipment_detail.html",
        computer=computer,
        assignment=assignment,
        maintenance=maintenance,
        movements=movements,
        active_page="inventory"
    )

@app.route("/inventory/new", methods=["GET", "POST"])
def create_equipment():
    error = None

    statuses = [
        "Available",
        "Assigned",
        "Maintenance",
        "Storage",
        "Retired",
        "Lost",
        "Stolen"
    ]

    if request.method == "POST":
        code = clean_value(
            request.form.get("code", "")
        )

        equipment_type = clean_value(
            request.form.get("type", "")
        )

        brand = clean_value(
            request.form.get("brand", "")
        )

        model = clean_value(
            request.form.get("model", "")
        )

        serial_number = clean_value(
            request.form.get("serial_number", "")
        )

        charger_serial_number = clean_value(
            request.form.get(
                "charger_serial_number",
                ""
            )
        )

        initial_warranty = clean_value(
            request.form.get(
                "initial_warranty",
                ""
            )
        )

        purchase_year = clean_value(
            request.form.get(
                "purchase_year",
                ""
            )
        )

        purchase_month = clean_value(
            request.form.get(
                "purchase_month",
                ""
            )
        )

        processor = clean_value(
            request.form.get(
                "processor",
                ""
            )
        )

        ram = clean_value(
            request.form.get(
                "ram",
                ""
            )
        )

        operating_system = clean_value(
            request.form.get(
                "operating_system",
                ""
            )
        )

        invoice = clean_value(
            request.form.get(
                "invoice",
                ""
            )
        )

        fixed_asset = clean_value(
            request.form.get(
                "fixed_asset",
                ""
            )
        )

        purchase_order = clean_value(
            request.form.get(
                "purchase_order",
                ""
            )
        )

        entry_date = clean_value(
            request.form.get(
                "entry_date",
                ""
            )
        )

        wifi_mac = clean_value(
            request.form.get(
                "wifi_mac",
                ""
            )
        )

        ethernet_mac = clean_value(
            request.form.get(
                "ethernet_mac",
                ""
            )
        )

        status = request.form.get(
            "status",
            "Available"
        )

        comments = clean_value(
            request.form.get(
                "comments",
                ""
            )
        )

        if not code:
            error = "Code is required."

        elif not equipment_type:
            error = "Equipment type is required."

        elif not serial_number:
            error = "Serial number is required."

        elif status not in statuses:
            error = "Invalid equipment status."

        if purchase_year:
            try:
                purchase_year = int(
                    purchase_year
                )

            except ValueError:
                error = (
                    "Purchase year must be numeric."
                )

        if purchase_month:
            try:
                purchase_month = int(
                    purchase_month
                )

                if (
                    purchase_month < 1
                    or purchase_month > 12
                ):
                    error = (
                        "Purchase month must be "
                        "between 1 and 12."
                    )

            except ValueError:
                error = (
                    "Purchase month must be numeric."
                )

        if error is None:
            connection = get_db_connection()

            error = validate_unique_equipment(
                connection,
                code,
                serial_number,
                fixed_asset
            )

            if error is None:

                cursor = connection.execute(
                    """
                    INSERT INTO Computers (
                        Code,
                        Type,
                        Brand,
                        Model,
                        SerialNumber,
                        ChargerSerialNumber,
                        InitialWarranty,
                        PurchaseYear,
                        PurchaseMonth,
                        Processor,
                        RAM,
                        OperatingSystem,
                        Invoice,
                        FixedAsset,
                        PurchaseOrder,
                        EntryDate,
                        WifiMacAddress,
                        EthernetMacAddress,
                        Status,
                        Comments
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?
                    )
                    """,
                    (
                        code,
                        equipment_type,
                        brand,
                        model,
                        serial_number,
                        charger_serial_number,
                        initial_warranty,
                        purchase_year,
                        purchase_month,
                        processor,
                        ram,
                        operating_system,
                        invoice,
                        fixed_asset,
                        purchase_order,
                        entry_date,
                        wifi_mac,
                        ethernet_mac,
                        status,
                        comments
                    )
                )

                computer_id = cursor.lastrowid

                register_movement(
                    connection,
                    computer_id,
                    "Created",
                    (
                        "Equipment registered "
                        "in AssetFlow TI."
                    ),
                    None,
                    status
                )

                connection.commit()
                connection.close()

                return redirect(
                    url_for(
                        "equipment_detail",
                        computer_id=computer_id
                    )
                )

            connection.close()

    return render_template(
        "equipment_form.html",
        mode="create",
        equipment=None,
        error=error,
        statuses=statuses,
        active_page="inventory"
    )

@app.route("/inventory/<int:computer_id>/edit", methods=["GET", "POST"])
def edit_equipment(computer_id):
    connection = get_db_connection()

    equipment = connection.execute(
        """
        SELECT *
        FROM Computers
        WHERE ComputerID = ?
        """,
        (computer_id,)
    ).fetchone()

    if equipment is None:
        connection.close()
        return "Equipment not found", 404

    statuses = [
        "Available",
        "Assigned",
        "Maintenance",
        "Storage",
        "Retired",
        "Lost",
        "Stolen"
    ]

    error = None

    if request.method == "POST":
        code = clean_value(
            request.form.get("code", "")
        )

        equipment_type = clean_value(
            request.form.get("type", "")
        )

        brand = clean_value(
            request.form.get("brand", "")
        )

        model = clean_value(
            request.form.get("model", "")
        )

        serial_number = clean_value(
            request.form.get("serial_number", "")
        )

        charger_serial_number = clean_value(
            request.form.get(
                "charger_serial_number",
                ""
            )
        )

        initial_warranty = clean_value(
            request.form.get(
                "initial_warranty",
                ""
            )
        )

        purchase_year = clean_value(
            request.form.get(
                "purchase_year",
                ""
            )
        )

        purchase_month = clean_value(
            request.form.get(
                "purchase_month",
                ""
            )
        )

        processor = clean_value(
            request.form.get(
                "processor",
                ""
            )
        )

        ram = clean_value(
            request.form.get(
                "ram",
                ""
            )
        )

        operating_system = clean_value(
            request.form.get(
                "operating_system",
                ""
            )
        )

        invoice = clean_value(
            request.form.get(
                "invoice",
                ""
            )
        )

        fixed_asset = clean_value(
            request.form.get(
                "fixed_asset",
                ""
            )
        )

        purchase_order = clean_value(
            request.form.get(
                "purchase_order",
                ""
            )
        )

        entry_date = clean_value(
            request.form.get(
                "entry_date",
                ""
            )
        )

        wifi_mac = clean_value(
            request.form.get(
                "wifi_mac",
                ""
            )
        )

        ethernet_mac = clean_value(
            request.form.get(
                "ethernet_mac",
                ""
            )
        )

        status = request.form.get(
            "status",
            "Available"
        )

        comments = clean_value(
            request.form.get(
                "comments",
                ""
            )
        )

        if not code:
            error = "Code is required."

        elif not equipment_type:
            error = "Equipment type is required."

        elif not serial_number:
            error = "Serial number is required."

        elif status not in statuses:
            error = "Invalid equipment status."

        if purchase_year and error is None:
            try:
                purchase_year = int(
                    purchase_year
                )

            except ValueError:
                error = (
                    "Purchase year must be numeric."
                )

        if purchase_month and error is None:
            try:
                purchase_month = int(
                    purchase_month
                )

                if not 1 <= purchase_month <= 12:
                    error = (
                        "Purchase month must be "
                        "between 1 and 12."
                    )

            except ValueError:
                error = (
                    "Purchase month must be numeric."
                )

        if error is None:
            error = validate_unique_equipment(
                connection,
                code,
                serial_number,
                fixed_asset,
                computer_id
            )

        if error is None:
            previous_status = equipment["Status"]

            connection.execute(
                """
                UPDATE Computers
                SET
                    Code = ?,
                    Type = ?,
                    Brand = ?,
                    Model = ?,
                    SerialNumber = ?,
                    ChargerSerialNumber = ?,
                    InitialWarranty = ?,
                    PurchaseYear = ?,
                    PurchaseMonth = ?,
                    Processor = ?,
                    RAM = ?,
                    OperatingSystem = ?,
                    Invoice = ?,
                    FixedAsset = ?,
                    PurchaseOrder = ?,
                    EntryDate = ?,
                    WifiMacAddress = ?,
                    EthernetMacAddress = ?,
                    Status = ?,
                    Comments = ?,
                    LastUpdateDate = CURRENT_TIMESTAMP
                WHERE ComputerID = ?
                """,
                (
                    code,
                    equipment_type,
                    brand,
                    model,
                    serial_number,
                    charger_serial_number,
                    initial_warranty,
                    purchase_year,
                    purchase_month,
                    processor,
                    ram,
                    operating_system,
                    invoice,
                    fixed_asset,
                    purchase_order,
                    entry_date,
                    wifi_mac,
                    ethernet_mac,
                    status,
                    comments,
                    computer_id
                )
            )

            register_movement(
                connection,
                computer_id,
                "Updated",
                "Equipment information updated.",
                previous_status,
                status
            )

            connection.commit()
            connection.close()

            return redirect(
                url_for(
                    "equipment_detail",
                    computer_id=computer_id
                )
            )

    connection.close()

    return render_template(
        "equipment_form.html",
        mode="edit",
        equipment=equipment,
        error=error,
        statuses=statuses,
        active_page="inventory"
    )

@app.route("/employees")
def employees():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    connection = get_db_connection()

    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeName,
            E.Position,
            E.Area,
            E.BusinessLine,
            E.Site,
            E.City,
            E.Office,
            E.DirectSupervisor,
            E.Active,
            COUNT(A.AssignmentID) AS AssignedEquipment
        FROM Employees E
        LEFT JOIN Assignments A
            ON E.EmployeeID = A.EmployeeID
            AND A.Status = 'Active'
        WHERE 1 = 1
    """

    params = []

    if search:
        search_value = f"%{search}%"

        query += """
            AND (
                E.EmployeeName LIKE ?
                OR E.Position LIKE ?
                OR E.Area LIKE ?
                OR E.City LIKE ?
                OR E.Office LIKE ?
                OR E.DirectSupervisor LIKE ?
            )
        """

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status == "active":
        query += " AND E.Active = 1"

    elif status == "inactive":
        query += " AND E.Active = 0"

    query += """
        GROUP BY
            E.EmployeeID,
            E.EmployeeName,
            E.Position,
            E.Area,
            E.BusinessLine,
            E.Site,
            E.City,
            E.Office,
            E.DirectSupervisor,
            E.Active
        ORDER BY E.EmployeeName
    """

    employees = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    return render_template(
        "employees.html",
        employees=employees,
        search=search,
        selected_status=status,
        active_page="employees"
    )

@app.route("/employees/<int:employee_id>")
def employee_detail(employee_id):
    connection = get_db_connection()

    employee = connection.execute(
        """
        SELECT *
        FROM Employees
        WHERE EmployeeID = ?
        """,
        (employee_id,)
    ).fetchone()

    if employee is None:
        connection.close()
        return "Employee not found", 404

    equipment = connection.execute(
        """
        SELECT
            C.ComputerID,
            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber,
            C.Status,
            A.AssignmentDate,
            A.Office
        FROM Assignments A
        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID
        WHERE A.EmployeeID = ?
        AND A.Status = 'Active'
        ORDER BY A.AssignmentDate DESC
        """,
        (employee_id,)
    ).fetchall()

    assignment_history = connection.execute(
        """
        SELECT
            C.Code,
            C.Brand,
            C.Model,
            A.AssignmentDate,
            A.ReturnDate,
            A.Status
        FROM Assignments A
        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID
        WHERE A.EmployeeID = ?
        ORDER BY A.AssignmentID DESC
        """,
        (employee_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "employee_detail.html",
        employee=employee,
        equipment=equipment,
        assignment_history=assignment_history,
        active_page="employees"
    )

@app.route("/employees/new", methods=["GET", "POST"])
def create_employee():
    error = None

    if request.method == "POST":
        employee_name = clean_value(
            request.form.get("employee_name", "")
        )

        position = clean_value(
            request.form.get("position", "")
        )

        area = clean_value(
            request.form.get("area", "")
        )

        business_line = clean_value(
            request.form.get("business_line", "")
        )

        site = clean_value(
            request.form.get("site", "")
        )

        city = clean_value(
            request.form.get("city", "")
        )

        office = clean_value(
            request.form.get("office", "")
        )

        direct_supervisor = clean_value(
            request.form.get("direct_supervisor", "")
        )

        if not employee_name:
            error = "Employee name is required."

        if error is None:
            connection = get_db_connection()

            connection.execute(
                """
                INSERT INTO Employees (
                    EmployeeName,
                    Position,
                    Area,
                    BusinessLine,
                    Site,
                    City,
                    Office,
                    DirectSupervisor,
                    Active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    employee_name,
                    position,
                    area,
                    business_line,
                    site,
                    city,
                    office,
                    direct_supervisor
                )
            )

            connection.commit()
            connection.close()

            return redirect(
                url_for("employees")
            )

    return render_template(
        "employee_form.html",
        mode="create",
        employee=None,
        error=error,
        active_page="employees"
    )

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):
    connection = get_db_connection()

    employee = connection.execute(
        """
        SELECT *
        FROM Employees
        WHERE EmployeeID = ?
        """,
        (employee_id,)
    ).fetchone()

    if employee is None:
        connection.close()
        return "Employee not found", 404

    error = None

    if request.method == "POST":
        employee_name = clean_value(
            request.form.get("employee_name", "")
        )

        position = clean_value(
            request.form.get("position", "")
        )

        area = clean_value(
            request.form.get("area", "")
        )

        business_line = clean_value(
            request.form.get("business_line", "")
        )

        site = clean_value(
            request.form.get("site", "")
        )

        city = clean_value(
            request.form.get("city", "")
        )

        office = clean_value(
            request.form.get("office", "")
        )

        direct_supervisor = clean_value(
            request.form.get("direct_supervisor", "")
        )

        active = request.form.get(
            "active",
            "1"
        )

        if active not in ["0", "1"]:
            active = "1"

        if not employee_name:
            error = "Employee name is required."

        if error is None:
            connection.execute(
                """
                UPDATE Employees
                SET
                    EmployeeName = ?,
                    Position = ?,
                    Area = ?,
                    BusinessLine = ?,
                    Site = ?,
                    City = ?,
                    Office = ?,
                    DirectSupervisor = ?,
                    Active = ?
                WHERE EmployeeID = ?
                """,
                (
                    employee_name,
                    position,
                    area,
                    business_line,
                    site,
                    city,
                    office,
                    direct_supervisor,
                    int(active),
                    employee_id
                )
            )

            connection.commit()
            connection.close()

            return redirect(
                url_for(
                    "employee_detail",
                    employee_id=employee_id
                ),
                active_page="employees"
            )

    connection.close()

    return render_template(
        "employee_form.html",
        mode="edit",
        employee=employee,
        error=error,
        active_page="employees"
    )

@app.route("/assignments")
def assignments():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    connection = get_db_connection()

    query = """
        SELECT
            A.AssignmentID,
            A.AssignmentDate,
            A.ReturnDate,
            A.Office,
            A.Status,
            C.ComputerID,
            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber,
            E.EmployeeID,
            E.EmployeeName,
            E.Position,
            E.Area
        FROM Assignments A
        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID
        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID
        WHERE 1 = 1
    """

    params = []

    if search:
        search_value = f"%{search}%"

        query += """
            AND (
                C.Code LIKE ?
                OR C.SerialNumber LIKE ?
                OR C.Brand LIKE ?
                OR C.Model LIKE ?
                OR E.EmployeeName LIKE ?
                OR E.Area LIKE ?
            )
        """

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status:
        query += " AND A.Status = ?"
        params.append(status)

    query += """
        ORDER BY
            CASE
                WHEN A.Status = 'Active' THEN 0
                ELSE 1
            END,
            A.AssignmentID DESC
    """

    assignments_data = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    return render_template(
        "assignments.html",
        assignments=assignments_data,
        search=search,
        selected_status=status,
        active_page="assignments"
    )

@app.route("/assignments/new", methods=["GET", "POST"])
def create_assignment():
    connection = get_db_connection()

    available_computers = connection.execute(
        """
        SELECT
            ComputerID,
            Code,
            Brand,
            Model,
            SerialNumber
        FROM Computers
        WHERE Status = 'Available'
        ORDER BY Code
        """
    ).fetchall()

    active_employees = connection.execute(
        """
        SELECT
            EmployeeID,
            EmployeeName,
            Position,
            Office
        FROM Employees
        WHERE Active = 1
        ORDER BY EmployeeName
        """
    ).fetchall()

    error = None

    if request.method == "POST":
        computer_id = request.form.get(
            "computer_id",
            ""
        ).strip()

        employee_id = request.form.get(
            "employee_id",
            ""
        ).strip()

        assignment_date = request.form.get(
            "assignment_date",
            ""
        ).strip()

        office = clean_value(
            request.form.get(
                "office",
                ""
            )
        )

        comments = clean_value(
            request.form.get(
                "comments",
                ""
            )
        )

        if not computer_id:
            error = "Equipment is required."

        elif not employee_id:
            error = "Employee is required."

        elif not assignment_date:
            error = "Assignment date is required."

        if error is None:
            computer = connection.execute(
                """
                SELECT *
                FROM Computers
                WHERE ComputerID = ?
                """,
                (computer_id,)
            ).fetchone()

            employee = connection.execute(
                """
                SELECT *
                FROM Employees
                WHERE EmployeeID = ?
                """,
                (employee_id,)
            ).fetchone()

            if computer is None:
                error = "Equipment not found."

            elif computer["Status"] != "Available":
                error = "Equipment is not available."

            elif employee is None:
                error = "Employee not found."

            elif employee["Active"] != 1:
                error = "Employee is inactive."

        if error is None:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO Assignments (
                        ComputerID,
                        EmployeeID,
                        AssignmentDate,
                        Office,
                        Status,
                        Comments
                    )
                    VALUES (?, ?, ?, ?, 'Active', ?)
                    """,
                    (
                        computer_id,
                        employee_id,
                        assignment_date,
                        office,
                        comments
                    )
                )

                assignment_id = cursor.lastrowid

                connection.execute(
                    """
                    UPDATE Computers
                    SET
                        Status = 'Assigned',
                        LastUpdateDate = CURRENT_TIMESTAMP
                    WHERE ComputerID = ?
                    """,
                    (computer_id,)
                )

                register_movement(
                    connection,
                    computer_id,
                    "Assignment",
                    (
                        "Equipment assigned to "
                        f"{employee['EmployeeName']}."
                    ),
                    "Available",
                    (
                        "Assigned to "
                        f"{employee['EmployeeName']}"
                    )
                )

                connection.commit()
                connection.close()

                return redirect(
                    url_for("assignments")
                )

            except sqlite3.Error as error_db:
                connection.rollback()
                error = str(error_db)

    connection.close()

    return render_template(
        "assignment_form.html",
        computers=available_computers,
        employees=active_employees,
        error=error,
        active_page="assignments"
    )

@app.route("/assignments/<int:assignment_id>/return", methods=["POST"])
def return_assignment(assignment_id):
    connection = get_db_connection()

    assignment = connection.execute(
        """
        SELECT
            A.*,
            E.EmployeeName
        FROM Assignments A
        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID
        WHERE A.AssignmentID = ?
        """,
        (assignment_id,)
    ).fetchone()

    if assignment is None:
        connection.close()
        return "Assignment not found", 404

    if assignment["Status"] != "Active":
        connection.close()

        return redirect(
            url_for("assignments")
        )

    try:
        connection.execute(
            """
            UPDATE Assignments
            SET
                Status = 'Finalized',
                ReturnDate = DATE('now', 'localtime')
            WHERE AssignmentID = ?
            """,
            (assignment_id,)
        )

        connection.execute(
            """
            UPDATE Computers
            SET
                Status = 'Available',
                LastUpdateDate = CURRENT_TIMESTAMP
            WHERE ComputerID = ?
            """,
            (assignment["ComputerID"],)
        )

        register_movement(
            connection,
            assignment["ComputerID"],
            "Return",
            (
                "Equipment returned by "
                f"{assignment['EmployeeName']}."
            ),
            (
                "Assigned to "
                f"{assignment['EmployeeName']}"
            ),
            "Available"
        )

        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()

    return redirect(
        url_for("assignments")
    )

@app.route("/assignments/<int:assignment_id>/reassign", methods=["GET", "POST"])
def reassign_equipment(assignment_id):
    connection = get_db_connection()

    current_assignment = connection.execute(
        """
        SELECT
            A.*,
            C.Code,
            C.Brand,
            C.Model,
            E.EmployeeName
        FROM Assignments A
        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID
        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID
        WHERE A.AssignmentID = ?
        """,
        (assignment_id,)
    ).fetchone()

    if current_assignment is None:
        connection.close()
        return "Assignment not found", 404

    if current_assignment["Status"] != "Active":
        connection.close()

        return redirect(
            url_for("assignments")
        )

    employees = connection.execute(
        """
        SELECT
            EmployeeID,
            EmployeeName,
            Position,
            Office
        FROM Employees
        WHERE Active = 1
        AND EmployeeID != ?
        ORDER BY EmployeeName
        """,
        (
            current_assignment["EmployeeID"],
        )
    ).fetchall()

    error = None

    if request.method == "POST":
        new_employee_id = request.form.get(
            "employee_id",
            ""
        ).strip()

        assignment_date = request.form.get(
            "assignment_date",
            ""
        ).strip()

        office = clean_value(
            request.form.get(
                "office",
                ""
            )
        )

        comments = clean_value(
            request.form.get(
                "comments",
                ""
            )
        )

        if not new_employee_id:
            error = "New employee is required."

        elif not assignment_date:
            error = "Assignment date is required."

        elif (
            str(new_employee_id)
            == str(current_assignment["EmployeeID"])
        ):
            error = (
                "Equipment is already assigned "
                "to this employee."
            )

        new_employee = None

        if error is None:
            new_employee = connection.execute(
                """
                SELECT *
                FROM Employees
                WHERE EmployeeID = ?
                AND Active = 1
                AND EmployeeID != ?
                """,
                (
                    new_employee_id,
                    current_assignment["EmployeeID"]
                )
            ).fetchone()

            if new_employee is None:
                error = (
                    "Employee is invalid or inactive."
                )

        if error is None:
            try:
                connection.execute(
                    """
                    UPDATE Assignments
                    SET
                        Status = 'Finalized',
                        ReturnDate = ?
                    WHERE AssignmentID = ?
                    """,
                    (
                        assignment_date,
                        assignment_id
                    )
                )

                connection.execute(
                    """
                    INSERT INTO Assignments (
                        ComputerID,
                        EmployeeID,
                        AssignmentDate,
                        Office,
                        Status,
                        Comments
                    )
                    VALUES (
                        ?, ?, ?, ?, 'Active', ?
                    )
                    """,
                    (
                        current_assignment[
                            "ComputerID"
                        ],
                        new_employee_id,
                        assignment_date,
                        office,
                        comments
                    )
                )

                connection.execute(
                    """
                    UPDATE Computers
                    SET
                        Status = 'Assigned',
                        LastUpdateDate = CURRENT_TIMESTAMP
                    WHERE ComputerID = ?
                    """,
                    (
                        current_assignment[
                            "ComputerID"
                        ],
                    )
                )

                register_movement(
                    connection,
                    current_assignment[
                        "ComputerID"
                    ],
                    "Reassignment",
                    (
                        "Equipment reassigned from "
                        f"{current_assignment['EmployeeName']} "
                        "to "
                        f"{new_employee['EmployeeName']}."
                    ),
                    current_assignment[
                        "EmployeeName"
                    ],
                    new_employee[
                        "EmployeeName"
                    ]
                )

                connection.commit()
                connection.close()

                return redirect(
                    url_for("assignments")
                )

            except sqlite3.Error as error_db:
                connection.rollback()
                error = str(error_db)

    connection.close()

    return render_template(
        "reassign_form.html",
        assignment=current_assignment,
        employees=employees,
        error=error,
        active_page="assignments"
    )

@app.route("/responsibility-forms")
def responsibility_forms():
    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    connection = get_db_connection()

    query = """
        SELECT
            R.AcknowledgementID,
            R.AcknowledgementNumber,
            R.GenerationDate,
            R.FilePath,
            R.Status,
            R.Comments,

            A.AssignmentID,
            A.AssignmentDate,

            E.EmployeeName,
            E.Position,
            E.Area,

            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber

        FROM AssetAcknowledgements R

        INNER JOIN Assignments A
            ON R.AssignmentID = A.AssignmentID

        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID

        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID

        WHERE 1 = 1
    """

    params = []

    if search:
        search_value = f"%{search}%"

        query += """
            AND (
                R.AcknowledgementNumber LIKE ?
                OR E.EmployeeName LIKE ?
                OR C.Code LIKE ?
                OR C.SerialNumber LIKE ?
                OR C.Brand LIKE ?
                OR C.Model LIKE ?
            )
        """

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status:
        query += """
            AND R.Status = ?
        """

        params.append(status)

    query += """
        ORDER BY R.AcknowledgementID DESC
    """

    forms = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    return render_template(
        "responsibility_forms.html",
        forms=forms,
        search=search,
        selected_status=status,
        active_page="responsibility_forms"
    )

@app.route("/responsibility-forms/new", methods=["GET", "POST"])
def create_responsibility_form():
    connection = get_db_connection()

    assignments_data = connection.execute(
        """
        SELECT
            A.AssignmentID,
            A.AssignmentDate,
            A.Office,

            E.EmployeeName,
            E.Position,

            C.Code,
            C.Brand,
            C.Model,
            C.SerialNumber

        FROM Assignments A

        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID

        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID

        WHERE A.Status = 'Active'

        AND NOT EXISTS (
            SELECT 1
            FROM AssetAcknowledgements R
            WHERE R.AssignmentID = A.AssignmentID
            AND R.Status != 'Cancelled'
        )

        ORDER BY E.EmployeeName
        """
    ).fetchall()

    selected_assignment_id = request.args.get(
        "assignment_id",
        ""
    )

    error = None

    if request.method == "POST":
        assignment_id = request.form.get(
            "assignment_id",
            ""
        ).strip()

        generation_date = request.form.get(
            "generation_date",
            ""
        ).strip()

        comments = clean_value(
            request.form.get(
                "comments",
                ""
            )
        )

        selected_assignment_id = assignment_id

        if not assignment_id:
            error = "Assignment is required."

        elif not generation_date:
            error = "Generation date is required."

        assignment = None

        if error is None:
            assignment = connection.execute(
                """
                SELECT
                    A.AssignmentID,
                    A.AssignmentDate,
                    A.Office,
                    A.Status AS AssignmentStatus,

                    E.EmployeeName,
                    E.Position,
                    E.Area,
                    E.BusinessLine,
                    E.DirectSupervisor,

                    C.Code,
                    C.Type,
                    C.Brand,
                    C.Model,
                    C.SerialNumber,
                    C.ChargerSerialNumber,
                    C.FixedAsset

                FROM Assignments A

                INNER JOIN Employees E
                    ON A.EmployeeID = E.EmployeeID

                INNER JOIN Computers C
                    ON A.ComputerID = C.ComputerID

                WHERE A.AssignmentID = ?
                """,
                (assignment_id,)
            ).fetchone()

            if assignment is None:
                error = "Assignment not found."

            elif assignment["AssignmentStatus"] != "Active":
                error = "Assignment is not active."

        if error is None:
            existing_form = connection.execute(
                """
                SELECT AcknowledgementID
                FROM AssetAcknowledgements
                WHERE AssignmentID = ?
                AND Status != 'Cancelled'
                """,
                (assignment_id,)
            ).fetchone()

            if existing_form:
                error = (
                    "This assignment already has "
                    "a responsibility form."
                )

        if error is None:
            form_number = generate_responsibility_number(
                connection
            )

            relative_path = os.path.join(
                "responsivas",
                f"{form_number}.pdf"
            )

            absolute_path = os.path.join(
                BASE_DIR,
                relative_path
            )

            try:
                cursor = connection.execute(
                    """
                    INSERT INTO AssetAcknowledgements (
                        AssignmentID,
                        AcknowledgementNumber,
                        GenerationDate,
                        FilePath,
                        Status,
                        Comments
                    )
                    VALUES (?, ?, ?, ?, 'Generated', ?)
                    """,
                    (
                        assignment_id,
                        form_number,
                        generation_date,
                        relative_path,
                        comments
                    )
                )

                form_id = cursor.lastrowid

                pdf_data = {
                    "EmployeeName":
                        assignment["EmployeeName"],

                    "Position":
                        assignment["Position"],

                    "Area":
                        assignment["Area"],

                    "BusinessLine":
                        assignment["BusinessLine"],

                    "Office":
                        assignment["Office"],

                    "DirectSupervisor":
                        assignment["DirectSupervisor"],

                    "Code":
                        assignment["Code"],

                    "Type":
                        assignment["Type"],

                    "Brand":
                        assignment["Brand"],

                    "Model":
                        assignment["Model"],

                    "SerialNumber":
                        assignment["SerialNumber"],

                    "ChargerSerialNumber":
                        assignment["ChargerSerialNumber"],

                    "FixedAsset":
                        assignment["FixedAsset"],

                    "AssignmentDate":
                        assignment["AssignmentDate"]
                }

                generate_responsibility_form(
                    absolute_path,
                    form_number,
                    generation_date,
                    pdf_data,
                    comments
                )

                connection.commit()
                connection.close()

                return redirect(
                    url_for(
                        "responsibility_forms"
                    )
                )

            except Exception as error_pdf:
                connection.rollback()

                if os.path.exists(absolute_path):
                    os.remove(absolute_path)

                error = str(error_pdf)

    connection.close()

    return render_template(
        "responsibility_form_new.html",
        assignments=assignments_data,
        error=error,
        today=date.today().isoformat(),
        selected_assignment_id=selected_assignment_id,
        active_page="responsibility_forms"
    )

@app.route("/responsibility-forms/<int:form_id>/download")
def download_responsibility_form(form_id):
    connection = get_db_connection()

    form = connection.execute(
        """
        SELECT
            AcknowledgementNumber,
            FilePath
        FROM AssetAcknowledgements
        WHERE AcknowledgementID = ?
        """,
        (form_id,)
    ).fetchone()

    connection.close()

    if form is None:
        abort(404)

    if not form["FilePath"]:
        abort(404)

    file_path = os.path.abspath(
        os.path.join(
            BASE_DIR,
            form["FilePath"]
        )
    )

    allowed_directory = os.path.abspath(
        os.path.join(
            BASE_DIR,
            "responsivas"
        )
    )

    if not file_path.startswith(
        allowed_directory + os.sep
    ):
        abort(403)

    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=(
            f"{form['AcknowledgementNumber']}.pdf"
        )
    )

@app.route("/responsibility-forms/<int:form_id>/status", methods=["POST"])
def update_responsibility_status(form_id):
    new_status = request.form.get(
        "status",
        ""
    )

    valid_statuses = [
        "Generated",
        "Signed",
        "Cancelled"
    ]

    if new_status not in valid_statuses:
        abort(400)

    connection = get_db_connection()

    form = connection.execute(
        """
        SELECT AcknowledgementID
        FROM AssetAcknowledgements
        WHERE AcknowledgementID = ?
        """,
        (form_id,)
    ).fetchone()

    if form is None:
        connection.close()
        abort(404)

    connection.execute(
        """
        UPDATE AssetAcknowledgements
        SET Status = ?
        WHERE AcknowledgementID = ?
        """,
        (
            new_status,
            form_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("responsibility_forms")
    )

@app.route("/maintenance")
def maintenance_list():
    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    connection = get_db_connection()

    query = """
        SELECT
            M.MaintenanceID,
            M.MaintenanceDate,
            M.NextMaintenanceDate,
            M.MaintenanceType,
            M.Description,
            M.Technician,
            M.Observations,

            C.ComputerID,
            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber,
            C.Status AS EquipmentStatus,

            CASE
                WHEN M.NextMaintenanceDate IS NULL
                    THEN 'No Schedule'

                WHEN DATE(M.NextMaintenanceDate)
                    < DATE('now', 'localtime')
                    THEN 'Overdue'

                WHEN DATE(M.NextMaintenanceDate)
                    <= DATE(
                        'now',
                        'localtime',
                        '+30 days'
                    )
                    THEN 'Due Soon'

                ELSE 'Scheduled'
            END AS MaintenanceStatus

        FROM Maintenance M

        INNER JOIN Computers C
            ON M.ComputerID = C.ComputerID

        WHERE 1 = 1
    """

    params = []

    if search:
        search_value = f"%{search}%"

        query += """
            AND (
                C.Code LIKE ?
                OR C.Brand LIKE ?
                OR C.Model LIKE ?
                OR C.SerialNumber LIKE ?
                OR M.Technician LIKE ?
                OR M.MaintenanceType LIKE ?
            )
        """

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status == "overdue":
        query += """
            AND M.NextMaintenanceDate IS NOT NULL
            AND DATE(M.NextMaintenanceDate)
                < DATE('now', 'localtime')
        """

    elif status == "due-soon":
        query += """
            AND M.NextMaintenanceDate IS NOT NULL
            AND DATE(M.NextMaintenanceDate)
                >= DATE('now', 'localtime')
            AND DATE(M.NextMaintenanceDate)
                <= DATE(
                    'now',
                    'localtime',
                    '+30 days'
                )
        """

    elif status == "scheduled":
        query += """
            AND M.NextMaintenanceDate IS NOT NULL
            AND DATE(M.NextMaintenanceDate)
                > DATE(
                    'now',
                    'localtime',
                    '+30 days'
                )
        """

    elif status == "no-schedule":
        query += """
            AND M.NextMaintenanceDate IS NULL
        """

    query += """
        ORDER BY
            CASE
                WHEN M.NextMaintenanceDate IS NULL
                    THEN 1
                ELSE 0
            END,
            M.NextMaintenanceDate ASC,
            M.MaintenanceDate DESC
    """

    records = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    return render_template(
        "maintenance.html",
        records=records,
        search=search,
        selected_status=status,
        active_page="maintenance"
    )

@app.route("/maintenance/new", methods=["GET", "POST"])
def create_maintenance():
    connection = get_db_connection()

    computers = connection.execute(
        """
        SELECT
            ComputerID,
            Code,
            Type,
            Brand,
            Model,
            SerialNumber,
            Status
        FROM Computers
        ORDER BY Code
        """
    ).fetchall()

    selected_computer_id = request.args.get(
        "computer_id",
        ""
    )

    error = None

    if request.method == "POST":
        computer_id = request.form.get(
            "computer_id",
            ""
        ).strip()

        maintenance_date = request.form.get(
            "maintenance_date",
            ""
        ).strip()

        next_maintenance_date = clean_value(
            request.form.get(
                "next_maintenance_date",
                ""
            )
        )

        maintenance_type = clean_value(
            request.form.get(
                "maintenance_type",
                ""
            )
        )

        description = clean_value(
            request.form.get(
                "description",
                ""
            )
        )

        technician = clean_value(
            request.form.get(
                "technician",
                ""
            )
        )

        observations = clean_value(
            request.form.get(
                "observations",
                ""
            )
        )

        selected_computer_id = computer_id

        if not computer_id:
            error = "Equipment is required."

        elif not maintenance_date:
            error = "Maintenance date is required."

        if (
            error is None
            and next_maintenance_date
            and next_maintenance_date < maintenance_date
        ):
            error = (
                "Next maintenance date cannot be "
                "earlier than maintenance date."
            )

        computer = None

        if error is None:
            computer = connection.execute(
                """
                SELECT *
                FROM Computers
                WHERE ComputerID = ?
                """,
                (computer_id,)
            ).fetchone()

            if computer is None:
                error = "Equipment not found."

        if error is None:
            try:
                connection.execute(
                    """
                    INSERT INTO Maintenance (
                        ComputerID,
                        MaintenanceDate,
                        NextMaintenanceDate,
                        MaintenanceType,
                        Description,
                        Technician,
                        Observations
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        computer_id,
                        maintenance_date,
                        next_maintenance_date,
                        maintenance_type,
                        description,
                        technician,
                        observations
                    )
                )

                movement_value = (
                    f"{maintenance_type or 'General'}"
                    f" - {maintenance_date}"
                )

                if next_maintenance_date:
                    movement_value += (
                        f" | Next: "
                        f"{next_maintenance_date}"
                    )

                register_movement(
                    connection,
                    computer_id,
                    "Maintenance",
                    (
                        "Equipment maintenance "
                        "registered."
                    ),
                    None,
                    movement_value
                )

                connection.commit()
                connection.close()

                return redirect(
                    url_for("maintenance_list")
                )

            except sqlite3.Error as error_db:
                connection.rollback()
                error = str(error_db)

    connection.close()

    return render_template(
        "maintenance_form.html",
        computers=computers,
        error=error,
        today=date.today().isoformat(),
        selected_computer_id=selected_computer_id,
        active_page="maintenance"
    )

@app.route("/reports")
def reports():
    connection = get_db_connection()

    total_equipment = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Computers
        """
    ).fetchone()["Total"]

    total_employees = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Employees
        """
    ).fetchone()["Total"]

    total_assignments = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Assignments
        """
    ).fetchone()["Total"]

    total_maintenance = connection.execute(
        """
        SELECT COUNT(*) AS Total
        FROM Maintenance
        """
    ).fetchone()["Total"]

    connection.close()

    return render_template(
        "reports.html",
        total_equipment=total_equipment,
        total_employees=total_employees,
        total_assignments=total_assignments,
        total_maintenance=total_maintenance,
        active_page="reports"
    )

@app.route("/reports/inventory")
def export_inventory():
    connection = get_db_connection()

    records = connection.execute(
        """
        SELECT
            Code,
            Type,
            Brand,
            Model,
            SerialNumber,
            ChargerSerialNumber,
            InitialWarranty,
            PurchaseYear,
            PurchaseMonth,
            Processor,
            RAM,
            OperatingSystem,
            Invoice,
            FixedAsset,
            PurchaseOrder,
            EntryDate,
            WifiMacAddress,
            EthernetMacAddress,
            Status,
            Comments
        FROM Computers
        ORDER BY Code
        """
    ).fetchall()

    connection.close()

    headers = [
        "Code",
        "Type",
        "Brand",
        "Model",
        "Serial Number",
        "Charger Serial Number",
        "Warranty",
        "Purchase Year",
        "Purchase Month",
        "Processor",
        "RAM",
        "Operating System",
        "Invoice",
        "Fixed Asset",
        "Purchase Order",
        "Entry Date",
        "WiFi MAC",
        "Ethernet MAC",
        "Status",
        "Comments"
    ]

    file_path = os.path.join(
        BASE_DIR,
        "exports",
        "AssetFlow_Inventory.xlsx"
    )

    create_excel_report(
        file_path,
        "Inventory",
        headers,
        records
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="AssetFlow_Inventory.xlsx"
    )

@app.route("/reports/employees")
def export_employees():
    connection = get_db_connection()

    records = connection.execute(
        """
        SELECT
            EmployeeName,
            Position,
            Area,
            BusinessLine,
            Site,
            City,
            Office,
            DirectSupervisor,

            CASE
                WHEN Active = 1
                    THEN 'Active'
                ELSE 'Inactive'
            END AS EmployeeStatus

        FROM Employees

        ORDER BY EmployeeName
        """
    ).fetchall()

    connection.close()

    headers = [
        "Employee Name",
        "Position",
        "Area",
        "Business Line",
        "Site",
        "City",
        "Office",
        "Direct Supervisor",
        "Status"
    ]

    file_path = os.path.join(
        BASE_DIR,
        "exports",
        "AssetFlow_Employees.xlsx"
    )

    create_excel_report(
        file_path,
        "Employees",
        headers,
        records
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="AssetFlow_Employees.xlsx"
    )

@app.route("/reports/assignments")
def export_assignments():
    connection = get_db_connection()

    records = connection.execute(
        """
        SELECT
            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber,

            E.EmployeeName,
            E.Position,
            E.Area,

            A.Office,
            A.AssignmentDate,
            A.ReturnDate,
            A.Status,
            A.Comments

        FROM Assignments A

        INNER JOIN Computers C
            ON A.ComputerID = C.ComputerID

        INNER JOIN Employees E
            ON A.EmployeeID = E.EmployeeID

        ORDER BY A.AssignmentID DESC
        """
    ).fetchall()

    connection.close()

    headers = [
        "Equipment Code",
        "Type",
        "Brand",
        "Model",
        "Serial Number",
        "Employee",
        "Position",
        "Area",
        "Office",
        "Assignment Date",
        "Return Date",
        "Status",
        "Comments"
    ]

    file_path = os.path.join(
        BASE_DIR,
        "exports",
        "AssetFlow_Assignments.xlsx"
    )

    create_excel_report(
        file_path,
        "Assignments",
        headers,
        records
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="AssetFlow_Assignments.xlsx"
    )

@app.route("/reports/maintenance")
def export_maintenance():
    connection = get_db_connection()

    records = connection.execute(
        """
        SELECT
            C.Code,
            C.Type,
            C.Brand,
            C.Model,
            C.SerialNumber,

            M.MaintenanceDate,
            M.NextMaintenanceDate,
            M.MaintenanceType,
            M.Description,
            M.Technician,
            M.Observations

        FROM Maintenance M

        INNER JOIN Computers C
            ON M.ComputerID = C.ComputerID

        ORDER BY M.MaintenanceDate DESC
        """
    ).fetchall()

    connection.close()

    headers = [
        "Equipment Code",
        "Equipment Type",
        "Brand",
        "Model",
        "Serial Number",
        "Maintenance Date",
        "Next Maintenance",
        "Maintenance Type",
        "Description",
        "Technician",
        "Observations"
    ]

    file_path = os.path.join(
        BASE_DIR,
        "exports",
        "AssetFlow_Maintenance.xlsx"
    )

    create_excel_report(
        file_path,
        "Maintenance",
        headers,
        records
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="AssetFlow_Maintenance.xlsx"
    )

@app.route("/backups")
def backups():
    backup_files = list_backups(
        BACKUP_DIRECTORY
    )

    return render_template(
        "backups.html",
        backups=backup_files,
        active_page="backups"
    )

@app.route("/backups/create", methods=["POST"])
def create_backup_manual():
    create_backup(
        DATABASE_PATH,
        BACKUP_DIRECTORY
    )

    return redirect(
        url_for("backups")
    )

@app.route("/backups/<path:filename>/download")
def download_backup(filename):
    if os.path.basename(filename) != filename:
        abort(400)

    backup_path = os.path.abspath(
        os.path.join(
            BACKUP_DIRECTORY,
            filename
        )
    )

    allowed_directory = os.path.abspath(
        BACKUP_DIRECTORY
    )

    if not backup_path.startswith(
        allowed_directory + os.sep
    ):
        abort(403)

    if not os.path.exists(
        backup_path
    ):
        abort(404)

    return send_file(
        backup_path,
        as_attachment=True,
        download_name=filename
    )

@app.route("/activity")
def activity():
    search = request.args.get(
        "search",
        ""
    ).strip()

    movement_type = request.args.get(
        "type",
        ""
    ).strip()

    connection = get_db_connection()

    query = """
        SELECT
            M.MovementID,
            M.ComputerID,
            M.MovementType,
            M.Description,
            M.PreviousValue,
            M.NewValue,
            M.MovementDate,

            C.Code,
            C.Brand,
            C.Model,
            C.SerialNumber

        FROM AssetMovements M

        LEFT JOIN Computers C
            ON M.ComputerID = C.ComputerID

        WHERE 1 = 1
    """

    parameters = []

    if search:
        query += """
            AND (
                C.Code LIKE ?
                OR C.SerialNumber LIKE ?
                OR C.Brand LIKE ?
                OR C.Model LIKE ?
                OR M.Description LIKE ?
                OR M.PreviousValue LIKE ?
                OR M.NewValue LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if movement_type:
        query += """
            AND M.MovementType = ?
        """

        parameters.append(
            movement_type
        )

    query += """
        ORDER BY M.MovementDate DESC,
                 M.MovementID DESC
    """

    movements = connection.execute(
        query,
        parameters
    ).fetchall()

    movement_types = connection.execute(
        """
        SELECT DISTINCT MovementType
        FROM AssetMovements
        WHERE MovementType IS NOT NULL
        ORDER BY MovementType
        """
    ).fetchall()

    connection.close()

    return render_template(
        "activity.html",
        movements=movements,
        movement_types=movement_types,
        search=search,
        selected_type=movement_type,
        active_page="activity"
    )

def clean_value(value):
    value = value.strip()
    return value if value else None

def validate_unique_equipment(
    connection,
    code,
    serial_number,
    fixed_asset,
    computer_id=None
):
    query_extra = ""
    params_extra = []

    if computer_id is not None:
        query_extra = " AND ComputerID != ?"
        params_extra.append(computer_id)

    if code:
        result = connection.execute(
            f"""
            SELECT ComputerID
            FROM Computers
            WHERE Code = ?
            {query_extra}
            """,
            [code] + params_extra
        ).fetchone()

        if result:
            return "The equipment code already exists."

    if serial_number:
        result = connection.execute(
            f"""
            SELECT ComputerID
            FROM Computers
            WHERE SerialNumber = ?
            {query_extra}
            """,
            [serial_number] + params_extra
        ).fetchone()

        if result:
            return "The serial number already exists."

    if fixed_asset:
        result = connection.execute(
            f"""
            SELECT ComputerID
            FROM Computers
            WHERE FixedAsset = ?
            {query_extra}
            """,
            [fixed_asset] + params_extra
        ).fetchone()

        if result:
            return "The fixed asset already exists."

    return None

if __name__ == "__main__":
    ensure_daily_backup(
        DATABASE_PATH,
        BACKUP_DIRECTORY
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )