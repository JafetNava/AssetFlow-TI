PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Employees (
    EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeeName TEXT NOT NULL,
    Position TEXT,
    Area TEXT,
    BusinessLine TEXT,
    Site TEXT,
    City TEXT,
    Office TEXT,
    DirectSupervisor TEXT,
    Active INTEGER NOT NULL DEFAULT 1,
    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Computers (
    ComputerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Code TEXT UNIQUE,
    Type TEXT NOT NULL,
    Brand TEXT,
    Model TEXT,
    SerialNumber TEXT UNIQUE,
    ChargerSerialNumber TEXT,

    InitialWarranty TEXT,
    PurchaseYear INTEGER,
    PurchaseMonth INTEGER,

    Processor TEXT,
    RAM TEXT,
    OperatingSystem TEXT,

    Invoice TEXT,
    FixedAsset TEXT UNIQUE,
    PurchaseOrder TEXT,

    EntryDate DATE,

    WifiMacAddress TEXT,
    EthernetMacAddress TEXT,

    Status TEXT NOT NULL DEFAULT 'Available',

    Comments TEXT,

    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastUpdateDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Assignments (
    AssignmentID INTEGER PRIMARY KEY AUTOINCREMENT,

    ComputerID INTEGER NOT NULL,
    EmployeeID INTEGER NOT NULL,

    AssignmentDate DATE NOT NULL,
    ReturnDate DATE,

    Office TEXT,

    Status TEXT NOT NULL DEFAULT 'Active',

    Comments TEXT,

    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ComputerID)
        REFERENCES Computers(ComputerID),

    FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID)
);

CREATE TABLE IF NOT EXISTS Maintenance (
    MaintenanceID INTEGER PRIMARY KEY AUTOINCREMENT,

    ComputerID INTEGER NOT NULL,

    MaintenanceDate DATE NOT NULL,
    NextMaintenanceDate DATE,

    MaintenanceType TEXT,
    Description TEXT,
    Technician TEXT,
    Observations TEXT,

    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ComputerID)
        REFERENCES Computers(ComputerID)
);

CREATE TABLE IF NOT EXISTS AssetAcknowledgements (
    AcknowledgementID INTEGER PRIMARY KEY AUTOINCREMENT,

    AssignmentID INTEGER NOT NULL,

    AcknowledgementNumber TEXT UNIQUE,

    GenerationDate DATE NOT NULL,

    FilePath TEXT,

    Status TEXT DEFAULT 'Generated',

    Comments TEXT,

    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (AssignmentID)
        REFERENCES Assignments(AssignmentID)
);

CREATE TABLE IF NOT EXISTS AssetMovements (
    MovementID INTEGER PRIMARY KEY AUTOINCREMENT,

    ComputerID INTEGER,

    MovementType TEXT NOT NULL,

    Description TEXT,

    PreviousValue TEXT,
    NewValue TEXT,

    MovementDate DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ComputerID)
        REFERENCES Computers(ComputerID)
);

CREATE INDEX IF NOT EXISTS idx_computers_serial_number
ON Computers(SerialNumber);

CREATE INDEX IF NOT EXISTS idx_computers_code
ON Computers(Code);

CREATE INDEX IF NOT EXISTS idx_computers_status
ON Computers(Status);

CREATE INDEX IF NOT EXISTS idx_employees_name
ON Employees(EmployeeName);

CREATE INDEX IF NOT EXISTS idx_assignments_computer
ON Assignments(ComputerID);

CREATE INDEX IF NOT EXISTS idx_assignments_employee
ON Assignments(EmployeeID);

CREATE INDEX IF NOT EXISTS idx_maintenance_computer
ON Maintenance(ComputerID);