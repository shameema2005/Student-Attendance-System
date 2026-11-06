import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "database", "attendance.db"))

@app.before_request
def setup():
    init_db(DATABASE)

def faculty_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "faculty_id" not in session:
            flash("Please log in as faculty.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db(DATABASE)
        faculty = db.execute("SELECT * FROM faculty WHERE username=?", (username,)).fetchone()
        db.close()
        if faculty and check_password_hash(faculty["password_hash"], password):
            session.clear()
            session["faculty_id"] = faculty["id"]
            session["faculty_name"] = faculty["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@faculty_required
def dashboard():
    db = get_db(DATABASE)
    student_count = db.execute("SELECT COUNT(*) n FROM students").fetchone()["n"]
    db.close()
    return render_template("dashboard.html", student_count=student_count)

@app.route("/students")
@faculty_required
def students():
    db = get_db(DATABASE)
    rows = db.execute("SELECT * FROM students ORDER BY roll_number").fetchall()
    db.close()
    return render_template("students.html", students=rows)

@app.route("/students/add", methods=["GET", "POST"])
@faculty_required
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll_number", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()
        if not all([name, roll, department, year]):
            flash("All fields are required.", "danger")
        else:
            db = get_db(DATABASE)
            try:
                db.execute("INSERT INTO students(name,roll_number,department,year) VALUES(?,?,?,?)",
                           (name, roll, department, year))
                db.commit()
                flash("Student added successfully.", "success")
                db.close()
                return redirect(url_for("students"))
            except Exception:
                flash("Roll number already exists.", "danger")
                db.close()
    return render_template("add_student.html")

@app.route("/attendance", methods=["GET", "POST"])
@faculty_required
def attendance():
    db = get_db(DATABASE)
    if request.method == "POST":
        student_id = request.form.get("student_id")
        date = request.form.get("date")
        status = request.form.get("status")
        if status not in ("Present", "Absent") or not date:
            flash("Select a valid date and status.", "danger")
        else:
            db.execute("""INSERT INTO attendance(student_id,date,status) VALUES(?,?,?)
                          ON CONFLICT(student_id,date) DO UPDATE SET status=excluded.status""",
                       (student_id, date, status))
            db.commit()
            flash("Attendance saved.", "success")
    students = db.execute("SELECT * FROM students ORDER BY roll_number").fetchall()
    records = db.execute("""SELECT a.*,s.name,s.roll_number FROM attendance a
                            JOIN students s ON s.id=a.student_id ORDER BY a.date DESC""").fetchall()
    db.close()
    return render_template("attendance.html", students=students, records=records)

@app.route("/marks", methods=["GET", "POST"])
@faculty_required
def marks():
    db = get_db(DATABASE)
    if request.method == "POST":
        student_id = request.form.get("student_id")
        subject = request.form.get("subject", "").strip()
        try:
            score = int(request.form.get("marks", ""))
            if score < 0 or score > 100 or not subject:
                raise ValueError()
            db.execute("""INSERT INTO internal_marks(student_id,subject,marks) VALUES(?,?,?)
                          ON CONFLICT(student_id,subject) DO UPDATE SET marks=excluded.marks""",
                       (student_id, subject, score))
            db.commit()
            flash("Internal marks saved.", "success")
        except ValueError:
            flash("Enter a subject and marks between 0 and 100.", "danger")
    students = db.execute("SELECT * FROM students ORDER BY roll_number").fetchall()
    records = db.execute("""SELECT m.*,s.name,s.roll_number FROM internal_marks m
                            JOIN students s ON s.id=m.student_id ORDER BY s.roll_number,m.subject""").fetchall()
    db.close()
    return render_template("marks.html", students=students, records=records)

@app.route("/reports")
@faculty_required
def reports():
    db = get_db(DATABASE)
    rows = db.execute("""
        SELECT s.id,s.name,s.roll_number,s.department,s.year,
        COALESCE(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END),0) present_count,
        COUNT(a.id) total_classes,
        CASE WHEN COUNT(a.id)=0 THEN 0
             ELSE ROUND(100.0*SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)/COUNT(a.id),2)
        END attendance_percentage,
        COALESCE(AVG(m.marks),0) average_marks
        FROM students s
        LEFT JOIN attendance a ON a.student_id=s.id
        LEFT JOIN internal_marks m ON m.student_id=s.id
        GROUP BY s.id ORDER BY s.roll_number
    """).fetchall()
    db.close()
    return render_template("reports.html", reports=rows)

if __name__ == "__main__":
    init_db(DATABASE)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
