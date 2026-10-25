import sqlite3
from werkzeug.security import generate_password_hash
database_name ='emp.db'

def get_db_connection():
    conn = sqlite3.connect(database_name)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn
def create_tables():
    conn=get_db_connection()

    conn.execute("""CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'student', 'examiner')),
                    status TEXT NOT NULL CHECK(status IN ('active', 'rejected', 'pending'))
                    )
                """)
    
    conn.execute("""CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_code TEXT NOT NULL UNIQUE,
                    course_name TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active', 'inactive'))
                    )
               """)

    conn.execute("""CREATE TABLE IF NOT EXISTS examinations(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    examination_name TEXT NOT NULL,
                    examination_type TeXT NOT NULL,
                    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
                    maximum_marks REAL NOT NULL CHECK(maximum_marks > 0),
                    slot_creation_start TEXT NOT NULL,
                    slot_creation_end TEXT NOT NULL,
                    booking_start TEXT NOT NULL,
                    booking_end TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('draft', 'published', 'completed', 'cancelled')),
                    FOREIGN KEY(course_id) REFERENCES courses(id),
                    CHECK(slot_creation_start < slot_creation_end),
                    CHECK(booking_start < booking_end)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS examination_rubrics(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    examination_id INTEGER NOT NULL,
                    criterion_name TEXT NOT NULL,
                    maximum_marks REAL NOT NULL CHECK(maximum_marks > 0),
                    weightage REAL NOT NULL CHECK(weightage >= 0),
                    description TEXT,
                    FOREIGN KEY(examination_id) REFERENCES examinations(id),
                    UNIQUE(examination_id, criterion_name)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS examiner_profiles(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    department TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS examination_slots(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    examination_id INTEGER NOT NULL,
                    examiner_id INTEGER NOT NULL,
                    slot_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    maximum_capacity INTEGER NOT NULL CHECK(maximum_capacity > 0),
                    FOREIGN KEY(examination_id) REFERENCES examinations(id),
                    FOREIGN KEY(examiner_id) REFERENCES examiner_profiles(id)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS bookings(
                    id InTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    slot_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending', 'confirmed', 'cancelled')),
                    FOREIGN KEY(student_id) REFERENCES users(id),
                    FOREIGN KEY(slot_id) REFERENCES examination_slots(id),
                    UNIQUE(student_id, slot_id)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS evaluations(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id INTEGER NOT NULL UNIQUE,
                    feedback TEXT,
                    status TEXT NOT NULL CHECK(status IN ('pending', 'completed')),
                    FOREIGN KEY(booking_id) REFERENCES bookings(id)
                    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS evaluation_marks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id INTEGER NOT NULL,
                    rubric_id INTEGER NOT NULL,
                    marks_obtained REAL NOT NULL CHECK(marks_obtained >= 0),
                    FOREIGN KEY(evaluation_id) REFERENCES evaluations(id),
                    FOREIGN KEY(rubric_id) REFERENCES examination_rubrics(id),
                    UNIQUE(evaluation_id, rubric_id)
                    )""")
    conn.commit()
    conn.close()

def create_admin(name,email,password):
    conn=get_db_connection()
    password_hash = generate_password_hash(password)
    existing_admin=conn.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if existing_admin:
        print("Admin already exists.")
        conn.close()
        return
    conn.execute("""INSERT INTO users (name, email, password_hash, role, status) VALUES (?, ?, ?, 'admin', 'active')""", (name, email, password_hash))
    conn.commit()
    conn.close()
    print("Admin created successfully.")

if __name__ == "__main__":
    create_tables()
    print("All database tables created successfully.")

    admin_name=input("Enter Admin name:")
    admin_email = input("Enter Admin email: ")
    admin_password = input("Enter Admin password: ")

    create_admin(admin_name, admin_email, admin_password)


