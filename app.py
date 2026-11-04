from flask import Flask,render_template,request,redirect,url_for,session,flash
from werkzeug.security import check_password_hash,generate_password_hash
from emp_database import get_db_connection
import sqlite3
app = Flask(__name__)
app.secret_key="secrettt_keyyy"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email", "").strip()
        password=request.form.get("password", "").strip()
        conn=get_db_connection()
        user=conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"],password):
            if user["role"]=="examiner" and user["status"]!="active":
                flash("Admin appproval declined.", "danger")
                return redirect(url_for("login"))
            if user["status"]!="active":
                flash("Your account is not active.")
                return redirect(url_for("login"))
            session["user_id"]=user["id"]
            session["role"]=user["role"]
            if user["role"]=="admin":
                return redirect(url_for("admin_dashboard"))
            elif user["role"]=="examiner":
                return redirect(url_for("examiner_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name", "").strip()
        email=request.form.get("email", "").strip()
        password=request.form.get("password", "").strip()
        role=request.form.get("role", "")
        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))
        if role not in ("student","examiner"):
            flash("Invalid role selected.", "danger")
            return redirect(url_for("register"))
        conn=get_db_connection()
        existing_user=conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("login"))
        hashed_password=generate_password_hash(password)
        if role=="student":
            status="active"
        else:
            status="pending"
        conn.execute("""INsert INTO users (name,email,password_hash,role,status) VALUES(?,?,?,?,?)""", (name,email,hashed_password,role,status))
        conn.commit()
        conn.close()

        if role=="examiner":
            flash("Registration successful. Waiting for admin approval.", "success")
        else:
            flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    conn=get_db_connection()

    # Counting records for each table
    total_courses=conn.execute("SELECT COUNT(*) AS count FROM courses").fetchone()[0]

    total_examinations=conn.execute("SELECT COUNT(*) AS count FROM examinations").fetchone()[0]

    total_examiners=conn.execute("SELECT COUNT(*) AS count FROM users WHERE role='examiner'").fetchone()[0]

    total_students=conn.execute("SELECT COUNT(*) AS count FROM users WHERE role='student'").fetchone()[0]

    total_slots=conn.execute("SELECT COUNT(*) AS count FROM examination_slots").fetchone()[0]

    total_bookings=conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()[0]

    # This is for fetching pending examiners for approval...

    pending_examiners=conn.execute("""SELECT id,name,email FROM users WHERE role='examiner' AND status='pending' """).fetchall()
    conn.close()
    return render_template("admin_dashboard.html", 
                           pending_examiners=pending_examiners,
                           total_courses=total_courses,
                           total_examinations=total_examinations,
                           total_examiners=total_examiners,
                           total_students=total_students,
                           total_slots=total_slots,
                           total_bookings=total_bookings)

@app.route("/examiner/dashboard")
def examiner_dashboard():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session["role"]!="examiner":
        flash("You are not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    user=conn.execute("SELEcT status FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    if not user or user["status"]!="active":
        flash("Your examiner account is not active.")
        return redirect(url_for("login"))
    return render_template("examiner_dashboard.html")

@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session["role"]!="student":
        flash("You are not not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    return render_template("student_dashboard.html")

@app.route("/admin/approve_examiner/<int:user_id>", methods=["POST"])
def approve_examiner(user_id):
    if "user_id" not in session:
        flash("Please login first.","danger")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    examiner=conn.execute("SELECT id FROM users WHERE id=? AND role='examiner' AND status='pending'", (user_id,)).fetchone()
    if not examiner:
        flash("Pending examiner not found.")
        return redirect(url_for("admin_dashboard"))
    conn.execute("UPDATE users SET status='active' WHERE id=?", (user_id,))
    conn.execute("INSERT INTO examiner_profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    flash("Examiner is approved.","success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject_examiner/<int:user_id>", methods=["POST"])
def reject_examiner(user_id):
    if "user_id" not in session:
        flash("Please login first.","danger")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    examiner=conn.execute("SELECT id FROM users WHERE id=? AND role='examiner' AND status='pending'", (user_id,)).fetchone()
    if not examiner:
        flash("Pending examiner not found.")
        return redirect(url_for("admin_dashboard"))
    conn.execute("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("Examiner is rejected.","success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/examiners")
def manage_examiners():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    search=request.args.get("search", "").strip()
    conn=get_db_connection()
    if search:
        examiners=conn.execute("""SELECT id,name,email,status FROM users WHERE role='examiner'
                                AND (name LIKE ? OR CAST(id AS TEXT)=?) ORDER BY id""",(f"%{search}%", search)).fetchall()
    else:
        examiners=conn.execute("SELECT id,name,email,status FROM users WHERE role='examiner' ORDER BY id").fetchall()
    conn.close()
    return render_template("admin_examiners.html", examiners=examiners, search=search)

@app.route("/admin/students")
def manage_students():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    search=request.args.get("search", "").strip()
    conn=get_db_connection()
    if search:
        students=conn.execute("""SELECT id,name,email,status FROM users WHERE role='student'
                                AND (name LIKE ? OR CAST(id AS TEXT)=?) ORDER BY id""",(f"%{search}%", search)).fetchall()
    else:
        students=conn.execute("SELECT id,name,email,status FROM users WHERE role='student' ORDER BY id").fetchall()
    conn.close()
    return render_template("admin_students.html", students=students, search=search)

@app.route("/admin/courses")
def manage_courses():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    if session["role"]!="admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))

    search=request.args.get("search", "").strip()
    conn=get_db_connection()
    if search:
        courses=conn.execute("""SELECT id,course_code,course_name,status FROM courses
                                WHERE course_name LIKE ? OR CAST(id AS TEXT)=?
                                ORDER BY id""",(f"%{search}%", search)).fetchall()
    else:
        courses=conn.execute(""" Select id,course_code,course_name,status FROM courses ORDER BY id""").fetchall()
    conn.close()
    return render_template("coursessss.html", courses=courses, search=search)

@app.route("/admin/courses/add", methods=["POST"])
def add_course():
    if "user_id"  not in session:
        flash("Please login firts.", "danger")
        return redirect(url_for("login"))
    if session['role']!="admin":
        flash("You are not allowed to do this action.", "danger")
        return redirect(url_for("home"))
    course_code=request.form.get("course_code", "").strip()
    course_name=request.form.get("course_name", "").strip()
    status=request.form.get("status", "")
    if not course_code or not course_name:
        flash("Course code and Course name are required.", "danger")
        return redirect(url_for("manage_courses"))
    if status not in ("active","inactive"):
        flash("Invalid course status.", "danger")
        return redirect(url_for("manage_courses"))
    conn=get_db_connection()
    try:
        conn.execute("""INSERT into courses(course_code,course_name,status) VALUES(?,?,?)""", (course_code,course_name,status))
        conn.commit()
        flash("Course added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("This course code already exists.","danger")
    finally:
        conn.close()
    return redirect(url_for("manage_courses"))

@app.route("/admin/courses/edit/<int:course_id>", methods=["GET","POST"])
def edit_course(course_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"]!="admin":
        flash("You are not allowed to do this.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    course=conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if course is None:
        conn.close()
        flash("No such course exists.", "danger")
        return redirect(url_for("manage_courses"))
    if request.method=="POST":
        course_code=request.form.get("course_code", "").strip()
        course_name=request.form.get("course_name", "").strip()
        status=request.form.get("status", "")
        if not course_code or not course_name:
           flash("Course code and Course name are required.", "danger")
           conn.close()
           return redirect(url_for("edit_course", course_id=course_id))
        if status not in("active","inactive"):
            flash("Invalid course status.", "danger")
            conn.close()
            return redirect(url_for("edit_course", course_id=course_id))
        try:
            conn.execute("""UPDATE courses 
                            SET course_code=?, course_name=?, status=? 
                            WHERE id=?""",(course_code,course_name,status,course_id))
            conn.commit()
            flash("Course updated successfully.", "success")
        except sqlite3.IntegrityError:
            flash("This Course code already exists.", "danger")
        finally:
            conn.close()
        return redirect(url_for("manage_courses"))
    conn.close()
    return render_template("edit_course.html", course=course)        

@app.route("/admin/courses/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    if session["role"] != "admin":
        flash("You are not allowed to perform this action.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    course=conn.execute("SELECT id FrOM courses WHere id=?", (course_id,)).fetchone()
    if course is None:
        conn.close()
        flash("Course not found.", "danger")
        return redirect(url_for("mangae_courses"))
    try:
        conn.execute("DELETE FroM courses where id=?", (course_id,))
        conn.commit()
        flash("Courses deleted successfully.", "success")
    except sqlite3.IntegrityError:
        flash("You cannot delete this course.","danger" )
    finally:
        conn.close()
    return redirect(url_for("manage_courses"))

@app.route("/admin/examinations")
def manage_examinations():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    search=request.args.get("search", "").strip()
    conn = get_db_connection()
    if search:
        examinations = conn.execute("""SELECT ex.id,ex.examination_name,ex.examination_type,ex.duration_minutes,ex.maximum_marks,
                                       ex.status,ex.slot_creation_start,ex.slot_creation_end,ex.booking_start,ex.booking_end,
                                       c.course_code,c.course_name From examinations ex join courses c
                                       ON ex.course_id=c.id
                                       WHERE ex.examination_name LIKE ? OR CAST(ex.id AS TEXT)= ?
                                       ORDER BY ex.id""", (f"%{search}%", search)).fetchall()
    else:
        examinations = conn.execute("""SELECT ex.id,ex.examination_name,ex.examination_type,ex.duration_minutes,ex.maximum_marks,
                                       ex.status,ex.slot_creation_start,ex.slot_creation_end,ex.booking_start,ex.booking_end,
                                       c.course_code,c.course_name From examinations ex join courses c
                                       ON ex.course_id=c.id
                                   ORDER BY ex.id""").fetchall()

    active_courses = conn.execute("""SELECT id,course_code,course_name From courses WHERE status='active' """).fetchall()
    conn.close()
    return render_template("examinations.html", examinations=examinations, active_courses=active_courses, search=search)

@app.route("/admin/examinations/add", methods=["POST"])
def add_examination():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to perform this action.", "danger")
        return redirect(url_for("home"))
    course_id = request.form.get("course_id", "")
    examination_name=request.form.get("examination_name", "").strip()
    examination_type=request.form.get("examination_type", "").strip()
    duration_minutes=request.form.get("duration_minutes", "").strip()
    maximum_marks=request.form.get("maximum_marks", "").strip()
    slot_creation_start=request.form.get("slot_creation_start", "")
    slot_creation_end=request.form.get("slot_creation_end", "")
    booking_start=request.form.get("booking_start", "")
    booking_end=request.form.get("booking_end", "")

    if not examination_name or not examination_type:
        flash("Examination name and Examination type are required.", "danger")
        return redirect(url_for("manage_examinations"))
    try:
        duration_minutes=int(duration_minutes)
        maximum_marks=float(maximum_marks)
        if duration_minutes <= 0 or maximum_marks <= 0:
            raise ValueError
    except ValueError:
        flash("Duration and Maximum marks must be positive numbers.", "danger")
        return redirect(url_for("manage_examinations"))

    if slot_creation_start >= slot_creation_end:
        flash("Slot creation start time must be before end time.", "danger")
        return redirect(url_for("manage_examinations"))
    if booking_start >= booking_end:
        flash("Booking start time must be before end time.", "danger")
        return redirect(url_for("manage_examinations"))
    if slot_creation_end > booking_start:
        flash("Slot creation end time must be before booking start time.", "danger")
        return redirect(url_for("manage_examinations"))

    conn = get_db_connection()
    try:
        course=conn.execute("""SELECT id FROM courses WHERE id=? AND status='active'""", (course_id,)).fetchone()
        if course is None:
            flash("Selected course is not active or does not exist.", "danger")
            return redirect(url_for("manage_examinations"))
        conn.execute("""INSERT INTO examinations  (course_id, examination_name, examination_type, duration_minutes, maximum_marks, slot_creation_start,
                                                  slot_creation_end, booking_start, booking_end, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                                  (course_id, examination_name, examination_type, duration_minutes, maximum_marks, slot_creation_start, slot_creation_end, booking_start, booking_end, "draft"))
        conn.commit()
        flash("Examination added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Error occurred while adding examination.", "danger")
    finally:
        conn.close()
    return redirect(url_for("manage_examinations"))
        
@app.route("/admin/examinations/edit/<int:examination_id>", methods=["GET","POST"])
def edit_examination(examination_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to perform this action.", "danger")
        return redirect(url_for("home"))
    conn = get_db_connection()
    examination = conn.execute("""SELECT * FROM examinations WHERE id=?""", (examination_id,)).fetchone()
    if examination is None:
        conn.close()
        flash("Examination not found.", "danger")
        return redirect(url_for("manage_examinations"))
    
    if request.method == "POST":
        course_id = request.form.get("course_id", "")
        examination_name = request.form.get("examination_name", "").strip()
        examination_type = request.form.get("examination_type", "").strip()
        duration_minutes = request.form.get("duration_minutes", "").strip()
        maximum_marks = request.form.get("maximum_marks", "").strip()
        slot_creation_start = request.form.get("slot_creation_start", "")
        slot_creation_end = request.form.get("slot_creation_end", "")
        booking_start = request.form.get("booking_start", "")
        booking_end = request.form.get("booking_end", "")

        if not examination_name or not examination_type:
            flash("Examination name and Examination type are required.", "danger")
            conn.close()
            return redirect(url_for("edit_examination", examination_id=examination_id))
        try:
            duration_minutes = int(duration_minutes)
            maximum_marks = float(maximum_marks)
            if duration_minutes <= 0 or maximum_marks <= 0:
                raise ValueError
        except ValueError:
            flash("Duration and Maximum marks must be positive numbers.", "danger")
            conn.close()
            return redirect(url_for("edit_examination", examination_id=examination_id))
        if slot_creation_start >= slot_creation_end:
            flash("Slot creation start time must be before end time.", "danger")
            conn.close()
            return redirect(url_for("edit_examination", examination_id=examination_id))
        if booking_start >= booking_end:
            flash("Booking start time must be before end time.", "danger")
            conn.close()
            return redirect(url_for("edit_examination", examination_id=examination_id))
        if slot_creation_end > booking_start:
            flash("Slot creation end time must be before booking start time.", "danger")
            conn.close()
            return redirect(url_for("edit_examination", examination_id=examination_id))
        course = conn.execute("""SELECT id FROM courses WHERE id=? AND status='active'""", (course_id,)).fetchone()
        if course is None:
            conn.close()
            flash("Please select an active course.", "danger")
            return redirect(url_for("edit_examination", examination_id=examination_id))
        conn.execute("""UPDATE examinations SET course_id=?, examination_name=?, examination_type=?, duration_minutes=?, maximum_marks=?,
                        slot_creation_start=?, slot_creation_end=?, booking_start=?, booking_end=? WHERE id=?""",
                        (course_id, examination_name, examination_type, duration_minutes, maximum_marks, slot_creation_start, slot_creation_end, booking_start, booking_end, examination_id))       
        conn.commit()
        conn.close()
        flash("Examination updated successfully.", "success")
        return redirect(url_for("manage_examinations"))
    active_courses= conn.execute("""SELECT id, course_code, course_name FROM courses WHERE status='active'""").fetchall()
    conn.close()
    return render_template("edit_examination.html", examination=examination, active_courses=active_courses)

@app.route("/admin/examinations/delete/<int:examination_id>", methods=["POST"])
def delete_examination(examination_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to perform this action.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    exam=conn.execute("SELECT * FROM examinations WHERE id=?", (examination_id,)).fetchone()
    if exam is None:
        conn.close()
        flash("Examination not found.", "danger")
        return redirect(url_for("manage_examinations"))
    try:
        conn.execute("DeLETE FrOM examinations WhERE id=?", (examination_id,))
        conn.commit()
        flash("Examination deleted successfully.", "success")
    except sqlite3.IntegrityError:
        flash("You cannot delete this examination.", "danger")
    finally:
        conn.close()
    return redirect(url_for("manage_examinations"))

@app.route("/admin/examinations/rubrics/<int:examination_id>")
def manage_rubrics(examination_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return(redirect(url_for("login")))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    examination=conn.execute("""SELECT id,examination_name FROM examinations WHERE id=?""", (examination_id,)).fetchone()
    if examination is None:
        conn.close()
        flash("Examination not found.", "danger")
        return redirect(url_for("manage_examinations"))
    rubrics=conn.execute("""SELECT * FROM examination_rubrics WHERE examination_id=?
                            ORDER BY id""", (examination_id,)).fetchall()
    conn.close()
    return render_template("rubrics.html", examination=examination, rubrics=rubrics)

@app.route("/admin/examinations/rubrics/add/<int:examination_id>", methods=["POST"])
def add_rubric(examination_id):
    if "user_id" not in session:
            flash("Please login first.", "danger")
            return(redirect(url_for("login")))
    if session["role"]!="admin":
            flash("You are not allowed to enter this page.", "danger")
            return redirect(url_for("home"))

    criterion_name=request.form.get("criterion_name", "").strip()
    description=request.form.get("description", "").strip()
    try:
        maximum_marks=float(request.form.get("maximum_marks", ""))
        weightage=float(request.form.get("weightage", ""))
    except ValueError:
        flash("Please enter valid numbers.", "danger")
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    if not criterion_name:
        flash("Criterion name is required.", "danger")
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    if maximum_marks <= 0:
        flash("Maximum marks must be greater than 0.", "danger")
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    if weightage < 0 or weightage >100:
        flash("Weightage must be between 0 and 100.", "danger")
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    conn=get_db_connection()
    examination=conn.execute("SELECT id FROM examinations WHERE id=?", (examination_id,)).fetchone()
    if examination is None:
        conn.close()
        flash("Examination not found.", "danger")
        return redirect(url_for("manage_examinations"))

    existing_weightage=conn.execute("""SELECT COALESCE(SUM(weightage),0) from examination_rubrics WHERE examination_id=?""", (examination_id,)).fetchone()[0]
    if existing_weightage + weightage > 100:
        conn.close()
        flash("Total rubric weightage cannot exceed 100%.","danger")
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    try:
        conn.execute("""INSERT INTO examination_rubrics (examination_id, criterion_name, maximum_marks, weightage, description)
                        VALUES (?, ?, ?, ?, ?)""", (examination_id, criterion_name, maximum_marks, weightage, description))
        conn.commit()
        flash("Rubric added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("This criterion name already exists for this examination.", "danger")
    finally:
        conn.close()
    return redirect(url_for("manage_rubrics", examination_id=examination_id))

@app.route("/admin/rubrics/edit/<int:rubric_id>", methods=["GET","POST"])
def edit_rubric(rubric_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return(redirect(url_for("login")))
    if session["role"]!="admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    rubric=conn.execute("""SELECT * FROM examination_rubrics WHERE id=?""", (rubric_id,)).fetchone()
    if rubric is None:
        conn.close()
        flash("Rubric not found.", "danger")
        return redirect(url_for("manage_examinations"))
    examination_id=rubric["examination_id"]
    if request.method=="POST":
        criterion_name=request.form.get("criterion_name", "").strip()
        description=request.form.get("description", "").strip()
        try:
            maximum_marks=float(request.form.get("maximum_marks", ""))
            weightage=float(request.form.get("weightage", ""))
        except ValueError:
            flash("Please enter valid numbers.", "danger")
            conn.close()
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))
        if not criterion_name:
            flash("Criterion name is required.", "danger")
            conn.close()
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))
        if maximum_marks <= 0:
            conn.close()
            flash("Maximum marks must be greater than 0.", "danger")
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))
        if weightage < 0 or weightage > 100:
            conn.close()
            flash("Weightage must be between 0 and 100.", "danger")
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))
        existing_weightage=conn.execute("""SELECT COALESCE(SUM(weightage),0) from examination_rubrics WHERE examination_id=? AND id!=?""", (examination_id, rubric_id)).fetchone()[0]
        if existing_weightage + weightage > 100:
            conn.close()
            flash("Total rubric weightage cannot exceed 100%.", "danger")
            return redirect(url_for("edit_rubric", rubric_id=rubric_id))
        try:
            conn.execute("""UPDATE examination_rubrics SET criterion_name=?, maximum_marks=?, weightage=?, description=? WHERE id=?""",
                         (criterion_name, maximum_marks, weightage, description, rubric_id))
            conn.commit()
            flash("Rubric updated successfully.", "success")
        except sqlite3.IntegrityError:
            flash("This criterion name already exists for this examination.", "danger")
        finally:
            conn.close()
        return redirect(url_for("manage_rubrics", examination_id=examination_id))
    conn.close()
    return render_template("edit_rubric.html", rubric=rubric)

@app.route("/admin/rubrics/delete/<int:rubric_id>", methods=["POST"])
def delete_rubric(rubric_id):
    if "user_id" not in session:
            flash("Please login first.", "danger")
            return(redirect(url_for("login")))
    if session["role"]!="admin":
            flash("You are not allowed to enter this page.", "danger")
            return redirect(url_for("home"))
    conn=get_db_connection()
    rubric=conn.execute("""SELECT * FROM examination_rubrics WHERE id=?""", (rubric_id,)).fetchone()
    if rubric is None:
            conn.close()
            flash("Rubric not found.", "danger")
            return redirect(url_for("manage_examinations"))
    examination_id=rubric["examination_id"]
    try:
        conn.execute("Delete From examination_rubrics WHERE id=?", (rubric_id,))
        conn.commit()
        flash("Rubric deleted successfully.", "success")
    except sqlite3.IntegrityError:
        flash("You cannot delete this rubric.", "danger")
    finally:
        conn.close()
    return redirect(url_for("manage_rubrics", examination_id=examination_id))

@app.route("/admin/examination-slots")
def manage_examination_slots():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    slots=conn.execute("""SELECT es.id, es.slot_date, es.start_time, es.end_time, es.maximum_capacity,
                          ex.examination_name, u.name AS examiner_name,u.email AS examiner_email
                          FROM examination_slots es
                          JOIN examinations ex ON es.examination_id = ex.id
                          JOIN examiner_profiles ep ON es.examiner_id = ep.id
                          JOIN users u ON ep.user_id = u.id
                          ORDER BY es.slot_date, es.start_time""").fetchall()
    conn.close()
    return render_template("admin_exam_slots.html", slots=slots)

@app.route("/admin/bookings")
def manage_bookings():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    if session["role"] != "admin":
        flash("You are not allowed to enter this page.", "danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    bookings=conn.execute("""select b.id, b.booking_date,b.status , student.name As student_name, student.email,
                             ex.examination_name, examiner.name As examiner_name,es.slot_date, es.start_time,es.end_time
                             From bookings b JOIN users student On b.student_id=student.id 
                             JOIN examination_slots es ON b.slot_id = es.id
                             JOIN examinations ex ON es.examination_id = ex.id
                             JOIN examiner_profiles ep ON es.examiner_id = ep.id
                             JOIN users examiner ON ep.user_id = examiner.id
                             ORDER BY b.id DESC""").fetchall()
    slots=conn.execute("Select id, slot_date,start_time,end_time From examination_slots ORDER BY slot_date,start_time").fetchall()
    conn.close()
    return render_template("admin_bookings.html", bookings=bookings, slots=slots)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
