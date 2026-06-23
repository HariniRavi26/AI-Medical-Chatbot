import sqlite3

conn = sqlite3.connect("medical_chatbot.db")
cursor = conn.cursor()

# ── Drop & recreate tables (safe to re-run) ──────────────────────────────────

cursor.executescript("""
DROP TABLE IF EXISTS appointment_history;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS symptoms;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS hospitals;

CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name TEXT NOT NULL,
    address       TEXT,
    phone         TEXT
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_name    TEXT NOT NULL,
    specialization TEXT NOT NULL,
    experience     INTEGER,
    phone          TEXT,
    available_time TEXT,
    max_patients   INTEGER DEFAULT 10,
    rating         REAL DEFAULT 4.5,
    hospital_id    INTEGER,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);

CREATE TABLE IF NOT EXISTS symptoms (
    symptom_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_name    TEXT NOT NULL,
    specialization  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name     TEXT NOT NULL,
    patient_age      INTEGER,
    patient_phone    TEXT,
    doctor_id        INTEGER,
    appointment_date TEXT,
    appointment_time TEXT,
    booking_status   TEXT DEFAULT 'Booked',
    booking_type     TEXT DEFAULT 'General',
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE IF NOT EXISTS appointment_history (
    history_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name      TEXT,
    doctor_name       TEXT,
    specialization    TEXT,
    hospital_name     TEXT,
    appointment_date  TEXT,
    appointment_time  TEXT,
    booking_type      TEXT DEFAULT 'General',
    status            TEXT DEFAULT 'Confirmed',
    created_at        TEXT DEFAULT (datetime('now'))
);
""")

# ── Hospitals ────────────────────────────────────────────────────────────────

hospitals = [
    ("Apollo Hospital",      "21 Greams Lane, Chennai",         "044-28296000"),
    ("Fortis Malar Hospital","52 1st Main Road, Adyar, Chennai","044-42892222"),
    ("MIOT International",   "4/112 Mount Poonamallee Road",    "044-22490000"),
    ("Kauvery Hospital",     "199 Luz Church Road, Mylapore",   "044-40006000"),
    ("Sri Ramachandra",      "No.1 Ramachandra Nagar, Porur",   "044-45928888"),
]

cursor.executemany(
    "INSERT INTO hospitals (hospital_name, address, phone) VALUES (?,?,?)",
    hospitals
)

# ── Doctors ──────────────────────────────────────────────────────────────────

doctors = [
    # Cardiologist
    ("Dr. Ramesh Kumar",    "Cardiologist",    15, "9841001001", "09:00 AM - 12:00 PM", 12, 4.8, 1),
    ("Dr. Priya Venkat",    "Cardiologist",    10, "9841001002", "02:00 PM - 05:00 PM", 10, 4.6, 2),
    # Neurologist
    ("Dr. Arun Balaji",     "Neurologist",     12, "9841002001", "10:00 AM - 01:00 PM", 10, 4.7, 3),
    ("Dr. Kavitha Raj",     "Neurologist",      8, "9841002002", "03:00 PM - 06:00 PM",  8, 4.5, 1),
    # Orthopedic
    ("Dr. Senthil Nathan",  "Orthopedic",      18, "9841003001", "08:00 AM - 11:00 AM", 14, 4.9, 4),
    ("Dr. Deepa Mohan",     "Orthopedic",       6, "9841003002", "01:00 PM - 04:00 PM",  8, 4.3, 2),
    # Dermatologist
    ("Dr. Lakshmi Subbu",   "Dermatologist",    9, "9841004001", "10:00 AM - 01:00 PM", 15, 4.6, 5),
    ("Dr. Vikram Anand",    "Dermatologist",   11, "9841004002", "04:00 PM - 07:00 PM", 12, 4.7, 3),
    # Psychiatrist
    ("Dr. Meena Krishnan",  "Psychiatrist",    14, "9841005001", "09:00 AM - 12:00 PM",  8, 4.8, 1),
    ("Dr. Rohit Sharma",    "Psychiatrist",     7, "9841005002", "02:00 PM - 05:00 PM",  6, 4.4, 4),
    # Gastroenterologist
    ("Dr. Suresh Patel",    "Gastroenterologist", 13, "9841006001", "08:00 AM - 11:00 AM", 10, 4.7, 2),
    ("Dr. Anitha Devi",     "Gastroenterologist",  5, "9841006002", "12:00 PM - 03:00 PM",  8, 4.2, 5),
    # Pulmonologist
    ("Dr. Karthik Rajan",   "Pulmonologist",   10, "9841007001", "09:00 AM - 12:00 PM", 10, 4.6, 3),
    ("Dr. Saranya Bose",    "Pulmonologist",    8, "9841007002", "01:00 PM - 04:00 PM",  8, 4.5, 4),
    # ENT
    ("Dr. Harish Babu",     "ENT Specialist",  16, "9841008001", "10:00 AM - 01:00 PM", 12, 4.8, 1),
    ("Dr. Nithya Srinivas", "ENT Specialist",   4, "9841008002", "03:00 PM - 06:00 PM", 10, 4.3, 5),
    # Ophthalmologist
    ("Dr. Ganesh Iyer",     "Ophthalmologist", 20, "9841009001", "08:00 AM - 11:00 AM", 15, 4.9, 2),
    ("Dr. Parvathy Menon",  "Ophthalmologist",  6, "9841009002", "02:00 PM - 05:00 PM", 10, 4.4, 3),
    # General Physician
    ("Dr. Bala Murugan",    "General Physician", 8, "9841010001", "08:00 AM - 08:00 PM", 20, 4.5, 4),
    ("Dr. Sundari Nair",    "General Physician", 5, "9841010002", "08:00 AM - 08:00 PM", 20, 4.3, 5),

    ("Dr. Anjali Rao", "Gynecologist", 12, "9841020001", "09:00 AM - 12:00 PM", 12, 4.8, 1),
    ("Dr. Sneha Iyer", "Gynecologist", 8, "9841020002", "02:00 PM - 05:00 PM", 10, 4.6, 2),
    ("Dr. Priyanka Menon", "Gynecologist", 15, "9841020003", "10:00 AM - 01:00 PM", 15, 4.9, 3),

    ("Dr. Kiran Kumar", "Pediatrician", 10, "9841021001", "09:00 AM - 12:00 PM", 15, 4.7, 1),
    ("Dr. Nisha Thomas", "Pediatrician", 7, "9841021002", "02:00 PM - 05:00 PM", 12, 4.5, 2),
    ("Dr. Rajesh Babu", "Pediatrician", 13, "9841021003", "10:00 AM - 01:00 PM", 14, 4.8, 3),

    ("Dr. Vivek Sharma", "Endocrinologist", 14, "9841022001", "09:00 AM - 12:00 PM", 12, 4.8, 4),
    ("Dr. Divya Nair", "Endocrinologist", 9, "9841022002", "02:00 PM - 05:00 PM", 10, 4.6, 5),
    ("Dr. Arun Prakash", "Endocrinologist", 11, "9841022003", "10:00 AM - 01:00 PM", 15, 4.7, 1),

    # Urologists
    ("Dr. Prakash Reddy", "Urologist", 14, "9841031001", "09:00 AM - 12:00 PM", 12, 4.8, 1),
    ("Dr. Manoj Kumar", "Urologist", 9, "9841031002", "02:00 PM - 05:00 PM", 10, 4.6, 2),

    # Dentists
    ("Dr. Shalini Devi", "Dentist", 11, "9841032001", "09:00 AM - 01:00 PM", 15, 4.8, 3),
    ("Dr. Vinod Raj", "Dentist", 7, "9841032002", "02:00 PM - 06:00 PM", 12, 4.5, 4),
]

cursor.executemany("""
    INSERT INTO doctors
    (doctor_name, specialization, experience, phone, available_time, max_patients, rating, hospital_id)
    VALUES (?,?,?,?,?,?,?,?)
""", doctors)

# ── Symptoms ─────────────────────────────────────────────────────────────────

symptoms = [
    # Cardiology
    ("chest pain",           "Cardiologist"),
    ("heart palpitations",   "Cardiologist"),
    ("shortness of breath",  "Cardiologist"),
    ("high blood pressure",  "Cardiologist"),
    ("irregular heartbeat",  "Cardiologist"),
    ("swollen legs",         "Cardiologist"),
    # Neurology
    ("headache",             "Neurologist"),
    ("migraine",             "Neurologist"),
    ("dizziness",            "Neurologist"),
    ("memory loss",          "Neurologist"),
    ("numbness",             "Neurologist"),
    ("tremors",              "Neurologist"),
    ("epilepsy",             "Neurologist"),
    # Orthopedic
    ("joint pain",           "Orthopedic"),
    ("back pain",            "Orthopedic"),
    ("knee pain",            "Orthopedic"),
    ("fracture",             "Orthopedic"),
    ("muscle pain",          "Orthopedic"),
    ("neck pain",            "Orthopedic"),
    ("bone pain",            "Orthopedic"),
    # Dermatology
    ("skin rash",            "Dermatologist"),
    ("acne",                 "Dermatologist"),
    ("itching",              "Dermatologist"),
    ("eczema",               "Dermatologist"),
    ("hair loss",            "Dermatologist"),
    ("psoriasis",            "Dermatologist"),
    # Psychiatry
    ("anxiety",              "Psychiatrist"),
    ("depression",           "Psychiatrist"),
    ("insomnia",             "Psychiatrist"),
    ("stress",               "Psychiatrist"),
    ("panic attacks",        "Psychiatrist"),
    ("mood swings",          "Psychiatrist"),
    # Gastroenterology
    ("stomach pain",         "Gastroenterologist"),
    ("vomiting",             "Gastroenterologist"),
    ("diarrhea",             "Gastroenterologist"),
    ("constipation",         "Gastroenterologist"),
    ("acid reflux",          "Gastroenterologist"),
    ("bloating",             "Gastroenterologist"),
    ("nausea",               "Gastroenterologist"),
    # Pulmonology
    ("cough",                "Pulmonologist"),
    ("breathing difficulty", "Pulmonologist"),
    ("wheezing",             "Pulmonologist"),
    ("asthma",               "Pulmonologist"),
    ("pneumonia",            "Pulmonologist"),
    ("chest congestion",     "Pulmonologist"),
    # ENT
    ("ear pain",             "ENT Specialist"),
    ("sore throat",          "ENT Specialist"),
    ("runny nose",           "ENT Specialist"),
    ("nasal congestion",     "ENT Specialist"),
    ("hearing loss",         "ENT Specialist"),
    ("tonsillitis",          "ENT Specialist"),
    ("sinusitis",            "ENT Specialist"),
    # Ophthalmology
    ("eye pain",             "Ophthalmologist"),
    ("blurred vision",       "Ophthalmologist"),
    ("red eyes",             "Ophthalmologist"),
    ("watery eyes",          "Ophthalmologist"),
    ("eye infection",        "Ophthalmologist"),
    # General
    ("fever",                "General Physician"),
    ("cold",                 "General Physician"),
    ("fatigue",              "General Physician"),
    ("weight loss",          "General Physician"),
    ("weakness",             "General Physician"),
    ("body ache",            "General Physician"),

    ("pcos", "Gynecologist"),
    ("pcod", "Gynecologist"),
    ("irregular periods", "Gynecologist"),
    ("heavy bleeding", "Gynecologist"),
    ("pregnancy consultation", "Gynecologist"),
    ("infertility", "Gynecologist"),
    ("ovarian cyst", "Gynecologist"),
    ("menstrual pain", "Gynecologist"),
    ("missed periods", "Gynecologist"),
    ("white discharge", "Gynecologist"),

    ("diabetes", "Endocrinologist"),
    ("high blood sugar", "Endocrinologist"),
    ("low blood sugar", "Endocrinologist"),
    ("thyroid", "Endocrinologist"),
    ("hypothyroidism", "Endocrinologist"),
    ("hyperthyroidism", "Endocrinologist"),
    ("weight gain", "Endocrinologist"),
    ("hormonal imbalance", "Endocrinologist"),

    ("child fever", "Pediatrician"),
    ("child cough", "Pediatrician"),
    ("child cold", "Pediatrician"),
    ("vaccination", "Pediatrician"),
    ("poor growth", "Pediatrician"),
    ("baby diarrhea", "Pediatrician"),
    ("baby vomiting", "Pediatrician"),

    ("kidney stone", "Urologist"),
    ("urinary infection", "Urologist"),
    ("painful urination", "Urologist"),
    ("blood in urine", "Urologist"),
    ("frequent urination", "Urologist"),
    ("prostate problem", "Urologist"),

    ("tooth pain", "Dentist"),
    ("cavity", "Dentist"),
    ("gum bleeding", "Dentist"),
    ("wisdom tooth pain", "Dentist"),
    ("bad breath", "Dentist"),
    ("tooth sensitivity", "Dentist"),
    ]

cursor.executemany(
    "INSERT INTO symptoms (symptom_name, specialization) VALUES (?,?)",
    symptoms
)

conn.commit()
conn.close()
print("✅ Database created successfully: medical_chatbot.db")
print(f"   • {len(hospitals)} hospitals")
print(f"   • {len(doctors)} doctors across 10 specializations")
print(f"   • {len(symptoms)} symptoms mapped")
