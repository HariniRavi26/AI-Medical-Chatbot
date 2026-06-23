from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import date, datetime, timedelta

app = Flask(__name__, static_folder="static")
CORS(app)

DB = os.path.join(os.path.dirname(__file__), "medical_chatbot.db")

EMERGENCY_SYMPTOMS = [
    "heart attack", "chest pain", "stroke", "accident",
    "breathing difficulty", "unconscious", "seizure",
    "severe bleeding", "poisoning", "choking"
]

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB):
        return
    print("Initializing database...")
    import setup_db
    print("Database ready.")

init_db()

# ── Serve frontend ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# ── Symptom Autocomplete ───────────────────────────────────────────────────────
@app.route("/symptoms/search", methods=["GET"])
def symptom_search():
    q = request.args.get("q", "").lower().strip()
    if not q or len(q) < 2:
        return jsonify([])
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symptom_name FROM symptoms
        WHERE LOWER(symptom_name) LIKE ?
        LIMIT 8
    """, (f"%{q}%",))
    results = [row["symptom_name"] for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

# ── Doctor Search ──────────────────────────────────────────────────────────────
@app.route("/get_doctor", methods=["POST"])
def get_doctor():
    data = request.json
    symptom = data.get("symptom", "").lower().strip()
    selected_date = data.get("date", str(date.today()))

    conn = get_conn()
    cursor = conn.cursor()

    # Emergency detection
    if any(e in symptom for e in EMERGENCY_SYMPTOMS):
        cursor.execute("""
            SELECT d.doctor_id, d.doctor_name, d.specialization,
                   d.experience, d.phone, d.available_time, d.rating,
                   h.hospital_name, h.phone as hosp_phone
            FROM doctors d JOIN hospitals h ON d.hospital_id = h.hospital_id
            WHERE d.specialization = 'Cardiologist'
            LIMIT 1
        """)
        doc = cursor.fetchone()
        conn.close()
        return jsonify({
            "emergency": True,
            "message": "EMERGENCY DETECTED! Immediate help needed.",
            "doctor_name": doc["doctor_name"],
            "hospital_name": doc["hospital_name"],
            "hospital_phone": doc["hosp_phone"],
            "ambulance": "108"
        })

    # Exact match
    cursor.execute("SELECT specialization FROM symptoms WHERE LOWER(symptom_name) = ?", (symptom,))
    spec = cursor.fetchone()

    # Word-by-word partial match
    if not spec:
        for word in symptom.split():
            if len(word) < 3:
                continue
            cursor.execute("SELECT specialization FROM symptoms WHERE LOWER(symptom_name) LIKE ? LIMIT 1", (f"%{word}%",))
            spec = cursor.fetchone()
            if spec:
                break

    # Full string partial match
    if not spec:
        cursor.execute("SELECT specialization FROM symptoms WHERE LOWER(symptom_name) LIKE ? LIMIT 1", (f"%{symptom}%",))
        spec = cursor.fetchone()

    if not spec:
        conn.close()
        return jsonify({"message": "No matching symptom found. Try keywords like 'headache', 'fever', 'knee pain'."})

    specialization = spec["specialization"]

    cursor.execute("""
        SELECT d.doctor_id, d.doctor_name, d.specialization,
               d.experience, d.phone, d.available_time,
               d.max_patients, d.rating, h.hospital_name, h.address
        FROM doctors d JOIN hospitals h ON d.hospital_id = h.hospital_id
        WHERE d.specialization = ?
    """, (specialization,))
    doctors = cursor.fetchall()

    result = []
    for d in doctors:
        cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id = ? AND appointment_date = ?", (d["doctor_id"], selected_date))
        booked = cursor.fetchone()["cnt"]
        slots = generate_slots(d["available_time"], d["doctor_id"], selected_date, cursor)
        result.append({
            "doctor_id":        d["doctor_id"],
            "doctor_name":      d["doctor_name"],
            "specialization":   d["specialization"],
            "experience":       d["experience"],
            "phone":            d["phone"],
            "available_time":   d["available_time"],
            "max_patients":     d["max_patients"],
            "rating":           d["rating"],
            "hospital_name":    d["hospital_name"],
            "hospital_address": d["address"],
            "booked":           booked,
            "slots":            slots
        })

    conn.close()
    return jsonify(result)

def generate_slots(available_time, doctor_id, selected_date, cursor):
    try:
        parts = available_time.split(" - ")
        start = datetime.strptime(parts[0].strip(), "%I:%M %p")
        end   = datetime.strptime(parts[1].strip(), "%I:%M %p")
    except Exception:
        return []

    cursor.execute("SELECT appointment_time FROM appointments WHERE doctor_id = ? AND appointment_date = ?", (doctor_id, selected_date))
    booked_times = {row["appointment_time"] for row in cursor.fetchall()}

    slots = []
    current = start
    while current < end:
        label = current.strftime("%I:%M %p")
        slots.append({"time": label, "booked": label in booked_times})
        current += timedelta(minutes=30)
    return slots

# ── Book Appointment ───────────────────────────────────────────────────────────
@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    data          = request.json
    patient_name  = data.get("patient_name", "").strip()
    patient_age   = data.get("patient_age", None)
    patient_phone = data.get("patient_phone", "").strip()
    doctor_id     = data.get("doctor_id")
    appt_date     = data.get("date", str(date.today()))
    appt_time     = data.get("time", "")
    booking_type  = data.get("booking_type", "General")

    if not patient_name or not doctor_id or not appt_time:
        return jsonify({"error": "Missing required fields."}), 400

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.doctor_name, d.specialization, d.max_patients,
               d.available_time, d.hospital_id, h.hospital_name
        FROM doctors d JOIN hospitals h ON d.hospital_id = h.hospital_id
        WHERE d.doctor_id = ?
    """, (doctor_id,))
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        return jsonify({"error": "Doctor not found."}), 404

    cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?", (doctor_id, appt_date, appt_time))
    if cursor.fetchone()["cnt"] > 0:
        conn.close()
        return jsonify({"message": "This time slot is already booked. Please choose another slot."})

    cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id = ? AND appointment_date = ?", (doctor_id, appt_date))
    if cursor.fetchone()["cnt"] >= doc["max_patients"]:
        conn.close()
        return jsonify({"message": "Doctor fully booked for this date. Please choose another date."})

    cursor.execute("""
        INSERT INTO appointments
        (patient_name, patient_age, patient_phone, doctor_id,
         appointment_date, appointment_time, booking_status, booking_type)
        VALUES (?, ?, ?, ?, ?, ?, 'Booked', ?)
    """, (patient_name, patient_age, patient_phone, doctor_id, appt_date, appt_time, booking_type))
    appt_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO appointment_history
        (patient_name, doctor_name, specialization, hospital_name,
         appointment_date, appointment_time, booking_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed')
    """, (patient_name, doc["doctor_name"], doc["specialization"], doc["hospital_name"], appt_date, appt_time, booking_type))

    conn.commit()
    conn.close()

    return jsonify({
        "appointment_id": appt_id,
        "patient_name":   patient_name,
        "doctor_name":    doc["doctor_name"],
        "specialization": doc["specialization"],
        "hospital_name":  doc["hospital_name"],
        "date":           appt_date,
        "time":           appt_time,
        "booking_type":   booking_type,
        "status":         "Confirmed"
    })

# ── History ────────────────────────────────────────────────────────────────────
@app.route("/history", methods=["GET"])
def history():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointment_history ORDER BY history_id DESC LIMIT 50")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

# ── Slots ──────────────────────────────────────────────────────────────────────
@app.route("/slots/<int:doctor_id>", methods=["GET"])
def get_slots(doctor_id):
    selected_date = request.args.get("date", str(date.today()))
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT available_time FROM doctors WHERE doctor_id=?", (doctor_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify([])
    slots = generate_slots(row["available_time"], doctor_id, selected_date, cursor)
    conn.close()
    return jsonify(slots)

# ── Available Dates ────────────────────────────────────────────────────────────
@app.route("/available_dates/<int:doctor_id>", methods=["GET"])
def available_dates(doctor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT max_patients FROM doctors WHERE doctor_id=?", (doctor_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return jsonify([])

    dates = []
    today = date.today()
    for i in range(7):
        d = str(today + timedelta(days=i))
        cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id=? AND appointment_date=?", (doctor_id, d))
        booked = cursor.fetchone()["cnt"]
        dates.append({"date": d, "booked": booked, "max": doc["max_patients"], "available": booked < doc["max_patients"]})

    conn.close()
    return jsonify(dates)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
