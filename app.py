from flask import Flask,render_template,request,redirect,url_for,session,flash
from werkzeug.security import check_password_hash,generate_password_hash
from emp_database import get_db_connection

app = Flask(__name__)
app.secret_key="secrettt_keyyy"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
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
            session["user_role"]=user["role"]
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
        name=request.form["name"]
        email=request.form["email"]
        password=request.form["password"]
        role=request.form["role"]
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
            return redirect(url_for("register"))
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
    if session["user_role"]!="admin":
        flash("You are not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    conn=get_db_connection()
    pending_examiners=conn.execute("""SELECT id,name,email FROM users WHERE role='examiner' AND status='pending' """).fetchall()
    conn.close()
    return render_template("admin_dashboard.html", pending_examiners=pending_examiners)

@app.route("/examiner/dashboard")
def examiner_dashboard():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session["user_role"]!="examiner":
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
    if session["user_role"]!="student":
        flash("You are not not allowed to enter this page.","danger")
        return redirect(url_for("home"))
    return render_template("student_dashboard.html")

@app.route("/admin/approve_examiner/<int:user_id>", methods=["POST"])
def approve_examiner(user_id):
    if "user_id" not in session:
        flash("Please login first.","danger")
        return redirect(url_for("login"))
    if session["user_role"]!="admin":
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
    if session["user_role"]!="admin":
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


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
