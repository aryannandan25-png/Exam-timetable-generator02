from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from scheduler import generate_schedule

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "exam_timetable.db"
app = Flask(__name__)
app.secret_key = "change-this-secret-key"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            students TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            slot TEXT NOT NULL,
            room TEXT NOT NULL,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
        """)


@app.route("/")
def index():
    with get_db() as db:
        subjects = db.execute("SELECT * FROM subjects ORDER BY semester, code").fetchall()
        exams = db.execute("""
            SELECT exams.id, subjects.code, subjects.name, subjects.semester,
                   exams.exam_date, exams.slot, exams.room
            FROM exams JOIN subjects ON subjects.id = exams.subject_id
            ORDER BY exams.exam_date, exams.slot, subjects.code
        """).fetchall()
    return render_template("index.html", subjects=subjects, exams=exams)


@app.route("/subjects/add", methods=["POST"])
def add_subject():
    code = request.form.get("code", "").strip().upper()
    name = request.form.get("name", "").strip()
    semester = request.form.get("semester", "").strip()
    students = request.form.get("students", "").strip()
    if not code or not name or not semester:
        flash("Please fill in subject code, name, and semester.", "error")
        return redirect(url_for("index"))
    try:
        with get_db() as db:
            db.execute("INSERT INTO subjects(code, name, semester, students) VALUES(?,?,?,?)",
                       (code, name, semester, students))
        flash(f"Subject {code} added.", "success")
    except sqlite3.IntegrityError:
        flash(f"Subject code {code} already exists.", "error")
    return redirect(url_for("index"))


@app.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    with get_db() as db:
        db.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    flash("Subject removed.", "success")
    return redirect(url_for("index"))


@app.route("/generate", methods=["POST"])
def generate():
    start_date = request.form.get("start_date", "").strip()
    slots_text = request.form.get("slots", "09:00-12:00,13:00-16:00")
    rooms_text = request.form.get("rooms", "Exam Hall A,Exam Hall B")
    gap = max(0, min(14, int(request.form.get("gap", "0") or 0)))
    slots = [s.strip() for s in slots_text.split(",") if s.strip()]
    rooms = [r.strip() for r in rooms_text.split(",") if r.strip()]

    with get_db() as db:
        subjects = db.execute("SELECT * FROM subjects ORDER BY semester, code").fetchall()
        db.execute("DELETE FROM exams")

        if not subjects:
            flash("Add at least one subject before generating a timetable.", "error")
            return redirect(url_for("index"))
        if not start_date or not slots or not rooms:
            flash("Enter a start date, at least one time slot, and at least one room.", "error")
            return redirect(url_for("index"))

        result = generate_schedule(
            [dict(s) for s in subjects],
            start_date=start_date,
            slots=slots,
            rooms=rooms,
            gap_days=gap
        )
        if not result["ok"]:
            flash(result["message"], "error")
            return redirect(url_for("index"))

        for item in result["schedule"]:
            db.execute(
                "INSERT INTO exams(subject_id, exam_date, slot, room) VALUES(?,?,?,?)",
                (item["subject_id"], item["date"], item["slot"], item["room"])
            )
    flash(f"Timetable generated successfully for {len(result['schedule'])} subjects.", "success")
    return redirect(url_for("index"))


@app.route("/timetable/clear", methods=["POST"])
def clear_timetable():
    with get_db() as db:
        db.execute("DELETE FROM exams")
    flash("Generated timetable cleared.", "success")
    return redirect(url_for("index"))


@app.route("/demo")
def demo():
    sample = [
        ("IT401", "Design and Analysis of Algorithms", "4", "IT-A"),
        ("IT402", "Database Management Systems", "4", "IT-A"),
        ("IT403", "Operating Systems", "4", "IT-A"),
        ("IT404", "Computer Networks", "4", "IT-B"),
        ("IT405", "Software Engineering", "4", "IT-B"),
        ("IT406", "Java Programming", "4", "IT-B"),
        ("MA401", "Discrete Mathematics", "4", "IT-A"),
    ]
    with get_db() as db:
        for row in sample:
            try:
                db.execute("INSERT INTO subjects(code,name,semester,students) VALUES(?,?,?,?)", row)
            except sqlite3.IntegrityError:
                pass
    flash("Sample semester subjects added. You can now generate a demo timetable.", "success")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
