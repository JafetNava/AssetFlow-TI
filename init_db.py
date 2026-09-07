import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "DB_AssetFlow_TI.db"
)

SCHEMA_PATH = os.path.join(
    BASE_DIR,
    "database",
    "schema.sql"
)


def create_database():
    connection = sqlite3.connect(DATABASE_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        connection.executescript(file.read())

    connection.commit()
    connection.close()

    print("Database created successfully.")


if __name__ == "__main__":
    create_database()