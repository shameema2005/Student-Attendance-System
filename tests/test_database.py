import os, tempfile
from database import init_db, get_db

def test_database_tables_and_demo_faculty():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        init_db(path)
        db = get_db(path)
        assert db.execute("SELECT COUNT(*) FROM faculty").fetchone()[0] == 1
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'").fetchone()
        db.close()
    finally:
        os.remove(path)
