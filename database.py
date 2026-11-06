import os, sqlite3
from werkzeug.security import generate_password_hash

def get_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(path):
    db = get_db(path)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS faculty(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        year TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(id),
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        UNIQUE(student_id,date)
    );
    CREATE TABLE IF NOT EXISTS internal_marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(id),
        subject TEXT NOT NULL,
        marks INTEGER NOT NULL CHECK(marks BETWEEN 0 AND 100),
        UNIQUE(student_id,subject)
    );
    """)
    if db.execute("SELECT COUNT(*) FROM faculty").fetchone()[0] == 0:
        db.execute("INSERT INTO faculty(username,name,password_hash) VALUES(?,?,?)",
                   ("faculty", "Demo Faculty", generate_password_hash("Faculty@123")))
    db.commit()
    db.close()
