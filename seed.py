import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "DB_AssetFlow_TI.db"
)


def get_employee_id(connection, employee_name):
    result = connection.execute(
        """
        SELECT EmployeeID
        FROM Employees
        WHERE EmployeeName = ?
        """,
        (employee_name,)
    ).fetchone()

    return result[0] if result else None


def get_computer_id(connection, code):
    result = connection.execute(
        """
        SELECT ComputerID
        FROM Computers
        WHERE Code = ?
        """,
        (code,)
    ).fetchone()

    return result[0] if result else None


def seed_database():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("PRAGMA foreign_keys = ON")

    try:
        employees = [
            (
                "Carlos Hernandez",
                "Data Analyst",
                "Business Intelligence",
                "Corporate",
                "North",
                "Monterrey",
                "Main Office",
                "Laura Martinez"
            ),
            (
                "Maria Lopez",
                "Administrative Assistant",
                "Administration",
                "Corporate",
                "Central",
                "Mexico City",
                "Corporate Office",
                "Roberto Sanchez"
            ),
            (
                "Daniel Ramirez",
                "Sales Executive",
                "Sales",
                "Commercial",
                "West",
                "Guadalajara",
                "Guadalajara Office",
                "Andrea Torres"
            ),
            (
                "Sofia Gonzalez",
                "HR Coordinator",
                "Human Resources",
                "Corporate",
                "Central",
                "Mexico City",
                "Corporate Office",
                "Patricia Romero"
            ),
            (
                "Luis Mendoza",
                "Operations Supervisor",
                "Operations",
                "Operations",
                "North",
                "Monterrey",
                "Operations Office",
                "Jorge Castillo"
            )
        ]

        for employee in employees:
            exists = connection.execute(
                """
                SELECT 1
                FROM Employees
                WHERE EmployeeName = ?
                """,
                (employee[0],)
            ).fetchone()

            if not exists:
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
                        DirectSupervisor
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    employee
                )

        computers = [
            (
                "AF-0001",
                "Laptop",
                "Dell",
                "Latitude 5450",
                "DELL-5450-001",
                "CH-001",
                "2027-04-30",
                2024,
                4,
                "Intel Core i5",
                "16 GB",
                "Windows 11 Pro",
                "FAC-1001",
                "ACT-1001",
                "PO-5001",
                "2024-05-02",
                "00:11:22:33:44:01",
                "00:11:22:33:55:01",
                "Assigned",
                "Primary laptop"
            ),
            (
                "AF-0002",
                "Laptop",
                "HP",
                "ProBook 440 G10",
                "HP-440-002",
                "CH-002",
                "2027-06-30",
                2024,
                6,
                "Intel Core i7",
                "16 GB",
                "Windows 11 Pro",
                "FAC-1002",
                "ACT-1002",
                "PO-5002",
                "2024-07-01",
                "00:11:22:33:44:02",
                "00:11:22:33:55:02",
                "Assigned",
                None
            ),
            (
                "AF-0003",
                "Laptop",
                "Lenovo",
                "ThinkPad E14",
                "LEN-E14-003",
                "CH-003",
                "2027-01-31",
                2024,
                1,
                "AMD Ryzen 7",
                "16 GB",
                "Windows 11 Pro",
                "FAC-1003",
                "ACT-1003",
                "PO-5003",
                "2024-02-05",
                "00:11:22:33:44:03",
                "00:11:22:33:55:03",
                "Available",
                "Ready for assignment"
            ),
            (
                "AF-0004",
                "Desktop",
                "Dell",
                "OptiPlex 7010",
                "DELL-7010-004",
                None,
                "2026-09-30",
                2023,
                9,
                "Intel Core i5",
                "16 GB",
                "Windows 11 Pro",
                "FAC-1004",
                "ACT-1004",
                "PO-5004",
                "2023-10-10",
                "00:11:22:33:44:04",
                "00:11:22:33:55:04",
                "Maintenance",
                "Preventive maintenance"
            ),
            (
                "AF-0005",
                "Laptop",
                "Dell",
                "Latitude 3440",
                "DELL-3440-005",
                "CH-005",
                "2027-08-31",
                2024,
                8,
                "Intel Core i5",
                "8 GB",
                "Windows 11 Pro",
                "FAC-1005",
                "ACT-1005",
                "PO-5005",
                "2024-09-02",
                "00:11:22:33:44:05",
                "00:11:22:33:55:05",
                "Assigned",
                None
            )
        ]

        for computer in computers:
            exists = connection.execute(
                """
                SELECT 1
                FROM Computers
                WHERE Code = ?
                """,
                (computer[0],)
            ).fetchone()

            if not exists:
                connection.execute(
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
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    computer
                )

        connection.commit()

        assignments = [
            ("AF-0001", "Carlos Hernandez", "2024-05-05", "Main Office"),
            ("AF-0002", "Maria Lopez", "2024-07-05", "Corporate Office"),
            ("AF-0005", "Daniel Ramirez", "2024-09-10", "Guadalajara Office")
        ]

        for code, employee_name, assignment_date, office in assignments:
            computer_id = get_computer_id(connection, code)
            employee_id = get_employee_id(connection, employee_name)

            exists = connection.execute(
                """
                SELECT 1
                FROM Assignments
                WHERE ComputerID = ?
                AND EmployeeID = ?
                AND Status = 'Active'
                """,
                (
                    computer_id,
                    employee_id
                )
            ).fetchone()

            if not exists:
                connection.execute(
                    """
                    INSERT INTO Assignments (
                        ComputerID,
                        EmployeeID,
                        AssignmentDate,
                        Office,
                        Status
                    )
                    VALUES (?, ?, ?, ?, 'Active')
                    """,
                    (
                        computer_id,
                        employee_id,
                        assignment_date,
                        office
                    )
                )

        maintenance_computer_id = get_computer_id(
            connection,
            "AF-0004"
        )

        maintenance_exists = connection.execute(
            """
            SELECT 1
            FROM Maintenance
            WHERE ComputerID = ?
            AND MaintenanceDate = ?
            """,
            (
                maintenance_computer_id,
                "2026-09-01"
            )
        ).fetchone()

        if not maintenance_exists:
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
                    maintenance_computer_id,
                    "2026-09-01",
                    "2027-03-01",
                    "Preventive",
                    "Internal cleaning and system review",
                    "IT Support",
                    "No hardware failures detected"
                )
            )

        connection.commit()

        print("Test data inserted successfully.")

    except sqlite3.Error as error:
        connection.rollback()

        print("Database error:")
        print(error)

    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()