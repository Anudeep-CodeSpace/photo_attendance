-- SQLite schema for photo-attendance system

CREATE TABLE IF NOT EXISTS Student_Details (
    roll_no TEXT PRIMARY KEY,
    name TEXT,
    class TEXT,
    section TEXT,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_roll_no ON Student_Details (roll_no);
