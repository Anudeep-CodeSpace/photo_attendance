import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "student_details.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_database():
    """
    Creates the SQLite DB file and initializes the Student_Details table.
    Safe to run multiple times.
    """
    # Create DB file if not exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load schema
    with open(SCHEMA_PATH, "r") as schema_file:
        schema_sql = schema_file.read()

    # Execute schema
    cursor.executescript(schema_sql)

    conn.commit()
    conn.close()


def get_connection():
    """
    Returns a new SQLite connection.
    (FastAPI will open a connection per request.)
    """
    return sqlite3.connect(DB_PATH, check_same_thread=False)


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
