#from flask_cors import CORS
from flask import Flask, request, jsonify
#from flask_cors import CORS
from database import init_db
import sqlite3
import os
import base64
from face_recognition_utils import recognize_face
from flask_cors import CORS
from datetime import datetime



# initialize database


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


UPLOAD_FOLDER = "known_faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- HOME ROUTE ----------
@app.route("/")
def home():
    start_day()
    return "Backend Running Successfully"


# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if data["username"] == "admin" and data["password"] == "admin123":
        return jsonify({"success": True})
    return jsonify({"success": False})


# ---------- ADD STUDENT ----------
@app.route("/add_student", methods=["POST"])
def add_student():
    try:
        name = request.form["name"]
        roll = request.form["roll"]
        image = request.files["image"]

        filename = roll + ".jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)

        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO students (name, roll) VALUES (?, ?)",
        (name, roll)
        )



        conn.commit()
        conn.close()

        return jsonify({"message": "Student added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})


  
 

@app.route("/recognize", methods=["POST"])
def recognize():
    try:
        data = request.json
        image_data = data["image"]

        # remove base64 header
        image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)

        temp_path = "temp.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        name = recognize_face(temp_path)

        if name:
            now = datetime.now()
            today_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE attendance
            SET time=?, status='PRESENT'
            WHERE name=? AND date=?
            """, (current_time, name, today_date))


            conn.commit()
            conn.close()

            return jsonify({"success": True, "name": name})

        else:
            return jsonify({"success": False})

    except Exception as e:
        return jsonify({"error": str(e)})
 
    
# ---------- ATTENDANCE SUMMARY ----------
@app.route("/attendance_summary", methods=["GET"])
def attendance_summary():
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()

        # total working days (unique dates)
        cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
        total_days = cursor.fetchone()[0]

        # attendance per student
        cursor.execute("""
            SELECT name, COUNT(DISTINCT date) as present_days
    FROM attendance
    GROUP BY name

        """)
        rows = cursor.fetchall()

        conn.close()

        report = []
        for row in rows:
            name = row[0]
            present = row[1]

            percentage = 0
            if total_days > 0:
                percentage = round((present / total_days) * 100, 2)

            status = "Eligible" if percentage >= 75 else "Shortage"

            report.append({
                "name": name,
                "present_days": present,
                "percentage": percentage,
                "status": status
            })

        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route("/start-day", methods=["GET"])
def start_day():

    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # get all students
    cursor.execute("SELECT name FROM students")
    students = cursor.fetchall()

    for student in students:
        name = student[0]

        # check if already created
        cursor.execute(
            "SELECT * FROM attendance WHERE name=? AND date=?",
            (name, today)
        )
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(
                "INSERT INTO attendance (name, date, time, status) VALUES (?, ?, ?, ?)",
                (name, today, "-", "ABSENT")
            )

    conn.commit()
    conn.close()

    return jsonify({"message": "Attendance sheet created"})

@app.route("/attendance", methods=["GET"])
def get_attendance():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, date, time, status FROM attendance ORDER BY date DESC")
    data = cursor.fetchall()

    records = []
    for row in data:
        records.append({
            "name": row[0],
            "date": row[1],
            "time": row[2],
            "status": row[3]
        })

    conn.close()
    return jsonify(records)



if __name__ == "__main__":
    init_db()
    app.run(port=5000, debug=True)

