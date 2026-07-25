from flask import Flask, render_template,request,jsonify,session,redirect,url_for
import sqlite3
from werkzeug.security import generate_password_hash
def init_db():
    conn = sqlite3.connect("healthconnect.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

app = Flask(__name__)
app.secret_key="replace_this_with_something_random_later"

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "Please fill in all required fields"}), 400

    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
            (name, email, phone, hashed_password)
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Email already registered"}), 409

    conn.close()

    return jsonify({"message": "Account created successfully"}), 201   

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, password FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"message": "Invalid email or password"}), 401

    user_id, name, hashed_password = row

    from werkzeug.security import check_password_hash
    if not check_password_hash(hashed_password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    session["user_id"] = user_id
    session["user_name"] = name

    return jsonify({"message": "Login successful"}), 200

    
@app.route("/")
def login():
    return render_template("login.html")
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", name=session.get("user_name"))

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("profile.html", name=session.get("user_name"))


@app.route("/records")
def records():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("records.html",name=session.get("user_name"))

@app.route("/upload")
def upload():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("upload.html",name=session.get("user_name"))

@app.route("/medicines")
def medicines():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("medicines.html",name=session.get("user_name"))

@app.route("/blood")
def blood():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("blood.html",name=session.get("user_name"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)