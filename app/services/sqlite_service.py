import sqlite3
from typing import Optional, Tuple, List
from pathlib import Path
import logging

from app.models.student import StudentDB

logger = logging.getLogger("attendance")

DB_PATH = Path(__file__).resolve().parents[1] / "db" / "student_details.db"


# ------------------------------------------------------------
# Connection helper
# ------------------------------------------------------------
def get_connection():
    """
    Returns a fresh SQLite connection.
    """
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to SQLite DB at {DB_PATH}: {e}")
        raise e


# ------------------------------------------------------------
# Insert a new student
# ------------------------------------------------------------
def insert_student(
    roll_no: str,
    name: Optional[str] = None,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
) -> bool:
    """
    Inserts a student row. Returns True if successful, False if duplicate.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO Student_Details (roll_no, name, class, section)
            VALUES (?, ?, ?, ?)
            """,
            (roll_no, name, class_name, section),
        )
        conn.commit()

        logger.info(f"Inserted student roll_no={roll_no} into SQLite")
        return True

    except sqlite3.IntegrityError:
        # Duplicate primary key (student already exists)
        logger.warning(f"Duplicate student roll_no={roll_no}. Insert skipped.")
        return False

    except Exception as e:
        logger.error(f"SQLite insert failed for roll_no={roll_no}: {e}")
        return False

    finally:
        conn.close()


# ------------------------------------------------------------
# Fetch student by roll number
# ------------------------------------------------------------
def get_student(roll_no: str) -> Optional[StudentDB]:
    """
    Fetch a student row and return StudentDB model.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT roll_no, name, class, section, added_on
            FROM Student_Details
            WHERE roll_no = ?
            """,
            (roll_no,),
        )

        row = cursor.fetchone()
    except Exception as e:
        logger.error(f"SQLite query failed for roll_no={roll_no}: {e}")
        conn.close()
        return None

    conn.close()

    if row:
        return StudentDB(
            roll_no=row[0],
            name=row[1],
            class_name=row[2],
            section=row[3],
            added_on=row[4],
        )

    logger.info(f"Student roll_no={roll_no} not found in database.")
    return None


# ------------------------------------------------------------
# Fetch all students
# ------------------------------------------------------------
def get_all_students() -> List[StudentDB]:
    """
    Returns all student rows.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT roll_no, name, class, section, added_on
            FROM Student_Details
            ORDER BY roll_no
            """
        )
        rows = cursor.fetchall()
    except Exception as e:
        logger.error(f"SQLite get_all_students failed: {e}")
        conn.close()
        return []

    conn.close()

    logger.info(f"Fetched {len(rows)} total students from DB.")
    return [
        StudentDB(
            roll_no=row[0],
            name=row[1],
            class_name=row[2],
            section=row[3],
            added_on=row[4],
        )
        for row in rows
    ]


# ------------------------------------------------------------
# Update student metadata
# ------------------------------------------------------------
def update_student(
    roll_no: str,
    name: Optional[str] = None,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
) -> bool:
    """
    Updates name/class/section of a student.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE Student_Details
            SET name = COALESCE(?, name),
                class = COALESCE(?, class),
                section = COALESCE(?, section)
            WHERE roll_no = ?
            """,
            (name, class_name, section, roll_no),
        )

        conn.commit()
        updated = cursor.rowcount > 0

        if updated:
            logger.info(f"Updated student roll_no={roll_no}")
        else:
            logger.info(f"Update attempted, but roll_no={roll_no} not found.")

        return updated

    except Exception as e:
        logger.error(f"SQLite update failed for roll_no={roll_no}: {e}")
        return False

    finally:
        conn.close()


# ------------------------------------------------------------
# Delete student
# ------------------------------------------------------------
def delete_student(roll_no: str) -> bool:
    """
    Deletes a student row.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM Student_Details WHERE roll_no = ?", (roll_no,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted student roll_no={roll_no}")
        else:
            logger.info(f"Delete attempted, but roll_no={roll_no} not found.")

        return deleted

    except Exception as e:
        logger.error(f"SQLite delete failed for roll_no={roll_no}: {e}")
        return False

    finally:
        conn.close()
