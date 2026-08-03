from flask import Flask, render_template, request, redirect
import mysql.connector
import pandas as pd
import pickle
import statistics
import json
import os

from utils import process_student

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
model = pickle.load(open(MODEL_PATH, "rb"))

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="learnlytics"
)
cursor = db.cursor()


# =========================
# HOME
# =========================
@app.route("/")
def home():

    cursor.execute("""
        SELECT s.name, p.cgpa, p.risk_level
        FROM students s
        JOIN predictions p ON s.id = p.student_id
        ORDER BY p.cgpa DESC
    """)

    rows = cursor.fetchall()

    topper = 0
    avg_cgpa = 0
    low_risk = 0
    medium_risk = 0
    high_risk = 0
    top_names = []
    top_scores = []

    if rows:
        topper = rows[0][1]
        avg_cgpa = round(sum(r[1] for r in rows) / len(rows), 2)

        top_names = [r[0] for r in rows[:10]]
        top_scores = [r[1] for r in rows[:10]]

        for row in rows:
            risk = row[2]

            if "Low" in risk:
                low_risk += 1
            elif "Medium" in risk:
                medium_risk += 1
            elif "High" in risk:
                high_risk += 1

    return render_template(
        "index.html",
        topper=topper,
        avg_cgpa=avg_cgpa,
        low_risk=low_risk,
        medium_risk=medium_risk,
        high_risk=high_risk,
        top_names=top_names,
        top_scores=top_scores
    )


# =========================
# INPUT
# =========================
@app.route("/input")
def input_page():
    return render_template("input.html")


# =========================
# UPLOAD
# =========================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file:
        return "No file uploaded"

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df.columns = df.columns.str.strip().str.lower()

        required = ["name", "attendance", "daily_available_hours"]
        for col in required:
            if col not in df.columns:
                return f"Column missing: {col}"

        for _, row in df.iterrows():

            name = str(row["name"])
            attendance = float(row["attendance"])
            daily_hours = float(row["daily_available_hours"])

            cursor.execute(
                "INSERT INTO students (name, attendance, daily_hours) VALUES (%s,%s,%s)",
                (name, attendance, daily_hours)
            )

            student_id = cursor.lastrowid

            subjects = {}
            subject_names = set()

            for col in df.columns:
                if col.endswith("_internal"):
                    subject_names.add(col.replace("_internal", ""))

            for subject in subject_names:

                internal = float(row.get(f"{subject}_internal", 0))
                external = float(row.get(f"{subject}_external", 0))
                assignment = float(row.get(f"{subject}_assignment", 0))

                total = internal + external + assignment
                subjects[subject] = total

                cursor.execute("""
                    INSERT INTO student_subjects
                    (student_id, subject_name, internal_marks, external_marks, assignment_marks, total_marks)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    student_id,
                    subject,
                    internal,
                    external,
                    assignment,
                    total
                ))

            scores = list(subjects.values())

            avg_marks = sum(scores) / len(scores)
            lowest = min(scores)
            highest = max(scores)

            consistency = 100
            if len(scores) > 1:
                consistency = max(0, 100 - statistics.stdev(scores))

            features = [[
                attendance,
                avg_marks,
                lowest,
                highest,
                consistency,
                70
            ]]

            predicted_cgpa = float(model.predict(features)[0])
            predicted_cgpa = min(predicted_cgpa, 10)

            result = process_student(
                attendance,
                daily_hours,
                subjects
            )

            weak = ", ".join(result["weak"]) if result["weak"] else "None"
            strong = ", ".join(result["strong"]) if result["strong"] else "None"

            cursor.execute("""
                INSERT INTO predictions
                (
                    student_id,
                    cgpa,
                    grade,
                    risk_level,
                    weak_subjects,
                    strong_subjects,
                    timetable,
                    suggestions
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                student_id,
                round(predicted_cgpa, 2),
                result["grade"],
                result["risk"],
                weak,
                strong,
                json.dumps(result["timetable"]),
                json.dumps(result["suggestions"])
            ))

        db.commit()
        return redirect("/dashboard")

    except Exception as e:
        return str(e)


# =========================
# PERFORMANCE + AI INSIGHTS
# =========================
@app.route("/dashboard")
def dashboard():

    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.attendance,
            p.cgpa,
            p.grade,
            p.risk_level,
            p.weak_subjects,
            p.strong_subjects
        FROM students s
        JOIN predictions p
        ON s.id = p.student_id
        ORDER BY p.cgpa DESC
    """)

    data = cursor.fetchall()

    total_students = len(data)
    avg_cgpa = round(sum(r[3] for r in data)/total_students, 2) if total_students else 0
    high_risk = sum(1 for r in data if "High" in r[5])
    low_risk = sum(1 for r in data if "Low" in r[5])

    grade_count = {}
    for r in data:
        grade_count[r[4]] = grade_count.get(r[4], 0) + 1

    # ===== AI INSIGHTS =====
    avg_attendance = round(sum(r[2] for r in data)/total_students, 2) if total_students else 0

    topper_name = data[0][1] if data else "N/A"
    topper_cgpa = data[0][3] if data else 0

    weak_subject_count = {}
    strong_subject_count = {}

    for row in data:

        weaks = row[6]
        strongs = row[7]

        if weaks != "None":
            for sub in weaks.split(", "):
                weak_subject_count[sub] = weak_subject_count.get(sub, 0) + 1

        if strongs != "None":
            for sub in strongs.split(", "):
                strong_subject_count[sub] = strong_subject_count.get(sub, 0) + 1

    most_weak_subject = "N/A"
    best_subject = "N/A"

    if weak_subject_count:
        most_weak_subject = max(
            weak_subject_count,
            key=weak_subject_count.get
        )

    if strong_subject_count:
        best_subject = max(
            strong_subject_count,
            key=strong_subject_count.get
        )

    class_suggestion = f"Extra focus recommended in {most_weak_subject}"

    return render_template(
        "result.html",
        data=data,
        total_students=total_students,
        avg_cgpa=avg_cgpa,
        high_risk=high_risk,
        low_risk=low_risk,
        grade_labels=list(grade_count.keys()),
        grade_values=list(grade_count.values()),
        top_names=[r[1] for r in data[:10]],
        top_cgpa=[r[3] for r in data[:10]],
        avg_attendance=avg_attendance,
        topper_name=topper_name,
        topper_cgpa=topper_cgpa,
        most_weak_subject=most_weak_subject,
        best_subject=best_subject,
        class_suggestion=class_suggestion
    )


# =========================
# SMART PREDICTION
# =========================
@app.route("/prediction")
def prediction():

    search = request.args.get("search", "")
    risk = request.args.get("risk", "")
    grade = request.args.get("grade", "")
    sort = request.args.get("sort", "desc")

    query = """
        SELECT
            s.id,
            s.name,
            p.cgpa,
            p.grade,
            p.risk_level,
            p.weak_subjects,
            p.strong_subjects
        FROM students s
        JOIN predictions p
        ON s.id = p.student_id
        WHERE 1=1
    """

    values = []

    if search:
        query += " AND s.name LIKE %s"
        values.append(f"%{search}%")

    if risk:
        query += " AND p.risk_level LIKE %s"
        values.append(f"%{risk}%")

    if grade:
        query += " AND p.grade=%s"
        values.append(grade)

    if sort == "asc":
        query += " ORDER BY p.cgpa ASC"
    else:
        query += " ORDER BY p.cgpa DESC"

    cursor.execute(query, values)
    data = cursor.fetchall()

    return render_template("prediction.html", data=data)


# =========================
# STUDENT PROFILE
# =========================
@app.route("/student/<int:student_id>")
def student_profile(student_id):

    cursor.execute("""
        SELECT
            s.name,
            s.attendance,
            s.daily_hours,
            p.cgpa,
            p.grade,
            p.risk_level,
            p.weak_subjects,
            p.strong_subjects,
            p.timetable,
            p.suggestions
        FROM students s
        JOIN predictions p
        ON s.id = p.student_id
        WHERE s.id=%s
    """, (student_id,))

    info = cursor.fetchone()

    if not info:
        return "Student not found"

    cursor.execute("""
        SELECT subject_name, total_marks
        FROM student_subjects
        WHERE student_id=%s
    """, (student_id,))

    rows = cursor.fetchall()

    subjects = [r[0] for r in rows]
    scores = [r[1] for r in rows]

    # parse JSON safely
    timetable = json.loads(info[8]) if info[8] else []
    suggestions = json.loads(info[9]) if info[9] else []

    # OLD FORMAT -> NEW FORMAT conversion
    if isinstance(timetable, dict):
        timetable = [
            {
                "day": subject.upper(),
                "task": hours
            }
            for subject, hours in timetable.items()
        ]

    if isinstance(suggestions, dict):
        suggestions = [
            f"{subject.upper()}: {text}"
            for subject, text in suggestions.items()
        ]

    return render_template(
        "student.html",
        info=info,
        subjects=subjects,
        scores=scores,
        timetable=timetable,
        suggestions=suggestions
    )
# =========================
# DELETE ONE STUDENT
# =========================
@app.route("/delete/<int:student_id>")
def delete_student(student_id):

    cursor.execute(
        "DELETE FROM student_subjects WHERE student_id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM predictions WHERE student_id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (student_id,)
    )

    db.commit()

    return redirect("/prediction")


# =========================
# DELETE MULTIPLE STUDENTS
# =========================
@app.route("/delete_selected", methods=["POST"])
def delete_selected():

    ids = request.form.getlist("student_ids")

    if ids:
        for student_id in ids:

            cursor.execute(
                "DELETE FROM student_subjects WHERE student_id=%s",
                (student_id,)
            )

            cursor.execute(
                "DELETE FROM predictions WHERE student_id=%s",
                (student_id,)
            )

            cursor.execute(
                "DELETE FROM students WHERE id=%s",
                (student_id,)
            )

        db.commit()

    return redirect("/prediction")

if __name__ == "__main__":
    app.run(debug=True) 