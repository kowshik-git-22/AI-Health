import os
from dotenv import load_dotenv #loads hidden env file
load_dotenv()
from google import genai
from google.genai import types
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")#this will check and load the api key
client = genai.Client(api_key=GEMINI_API_KEY)#creating a client to read prescption like calling model where ever we want
from flask import Flask, render_template,request,jsonify,session,redirect,url_for
import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect("healthconnect.db")#creates local data base

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            instruction TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            condition_summary TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            dose_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (medicine_id) REFERENCES medicines (id)
        )
    """)

    conn.commit()
    conn.close()

from datetime import timedelta
app = Flask(__name__)#creates the web server object. All routes and settings are registered on this object.”

app.secret_key = os.getenv("SECRET_KEY", "replace_this_with_something_random_later")
app.permanent_session_lifetime = timedelta(days=30)
            #this is the url path
@app.route("/api/signup", methods=["POST"])#post means it only accepts post requests use in sending form
def api_signup():
    data = request.get_json()#json is just a text format for sending data between a browser and server
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    if not name or not email or not password:# used to not show an error when json returns empty
        return jsonify({"message": "Please fill in all required fields"}), 400

    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect("healthconnect.db")#opens a connection to database file
    cursor = conn.cursor()#A cursor is the pen that runs commands on the database, conn is the connection, cursor is what actually sends SQL commands
    try:
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",# placeholders Each ? gets filled by the matching item in the bracket on the next line, in order: name, email, phone, hashed password
            (name, email, phone, hashed_password)
        )

        conn.commit()
    except sqlite3.IntegrityError:#two user cant have same name in my app
        conn.close()
        return jsonify({"message": "Email already registered"}), 409

    conn.close()

    return jsonify({"message": "Account created successfully"}), 201   

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    identifier = data.get("identifier")#can be an email or password
    password = data.get("password")
    remember = data.get("remember", False)

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, password FROM users WHERE email = ? OR phone = ?",
        (identifier, identifier)
    )
    row = cursor.fetchone()#fetchone() takes the first matching row. It comes back
    conn.close()

    if row is None:
        return jsonify({"message": "Invalid email/phone or password"}), 401

    user_id, name, hashed_password = row#Unpacks the tuple into three variables. If row is (1, "abcd", "scrypt:..."), then user_id = 1, name = "abcd", hashed_password = "scrypt:...".

    from werkzeug.security import check_password_hash
    if not check_password_hash(hashed_password, password):
        return jsonify({"message": "Invalid email/phone or password"}), 401

    session.permanent = bool(remember)
    session["user_id"] = user_id
    session["user_name"] = name

    return jsonify({"message": "Login successful"}), 200
    
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    import datetime
    today = datetime.date.today().isoformat()

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, frequency, instruction FROM medicines WHERE user_id = ? ORDER BY id DESC LIMIT 3",
        (session["user_id"],)
    )
    rows = cursor.fetchall()

    cursor.execute("SELECT medicine_id, status FROM doses WHERE user_id = ? AND dose_date = ?", (session["user_id"], today))
    dose_rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM medicines WHERE user_id = ?", (session["user_id"],))
    medicine_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM records WHERE user_id = ?", (session["user_id"],))
    record_count = cursor.fetchone()[0]

    conn.close()

    dose_status = {d[0]: d[1] for d in dose_rows}

    upcoming = []
    for r in rows:
        med_id, name, frequency, instruction = r
        timing = (frequency or "") + (" - " + instruction if instruction else "")
        upcoming.append({
            "id": med_id,
            "name": name,
            "timing": timing,
            "status": dose_status.get(med_id, "pending")
        })

    return render_template(
        "dashboard.html",
        name=session.get("user_name"),
        upcoming=upcoming,
        medicine_count=medicine_count,
        record_count=record_count
    )


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, phone FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()

    return render_template("profile.html", name=user[0], email=user[1], phone=user[2])



@app.route("/records")
def records():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename, upload_date, condition_summary FROM records WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    record_list = [{"filename": r[0], "date": r[1], "condition": r[2]} for r in rows]

    return render_template("records.html", name=session.get("user_name"), records=record_list)


from flask import send_from_directory

@app.route("/uploads/<filename>")
def serve_upload(filename):
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return send_from_directory("uploads", filename)


@app.route("/upload")
def upload():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("upload.html",name=session.get("user_name"))


@app.route("/medicines")
def medicines():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    import datetime
    today = datetime.date.today().isoformat()

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, dosage, frequency, instruction FROM medicines WHERE user_id = ?", (session["user_id"],))
    rows = cursor.fetchall()

    cursor.execute("SELECT medicine_id, status FROM doses WHERE user_id = ? AND dose_date = ?", (session["user_id"], today))
    dose_rows = cursor.fetchall()
    conn.close()

    dose_status = {d[0]: d[1] for d in dose_rows}

    medicine_list = []
    for row in rows:
        id_, name, dosage, frequency, instruction = row
        combined = ((frequency or "") + " " + (instruction or "")).lower()

        slots = set()
        if "morning" in combined:
            slots.add("morning")
        if "afternoon" in combined or "noon" in combined:
            slots.add("afternoon")
        if "night" in combined or "bedtime" in combined or "evening" in combined:
            slots.add("night")

        if not slots:
            if "1-0-0" in combined:
                slots.add("morning")
            elif "0-1-0" in combined:
                slots.add("afternoon")
            elif "0-0-1" in combined:
                slots.add("night")
            elif "1-1-1" in combined or "three" in combined or "thrice" in combined:
                slots.update(["morning", "afternoon", "night"])
            elif "twice" in combined or "two times" in combined:
                slots.update(["morning", "night"])
            else:
                slots.add("morning")

        medicine_list.append({
            "id": id_,
            "name": name,
            "dosage": dosage,
            "frequency": frequency,
            "instruction": instruction,
            "slots": ",".join(slots),
            "status": dose_status.get(id_, "pending")
        })

    return render_template("medicines.html", name=session.get("user_name"), medicines=medicine_list)




@app.route("/api/delete-medicine/<int:medicine_id>", methods=["POST"])
def api_delete_medicine(medicine_id):
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM medicines WHERE id = ? AND user_id = ?",
        (medicine_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted"}), 200


import time

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401

    file = request.files.get("prescription")
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    timestamp = str(int(time.time()))
    unique_filename = f"user{session['user_id']}_{timestamp}_{file.filename}"
    save_path = os.path.join("uploads", unique_filename)
    file.save(save_path)

    with open(save_path, "rb") as f:
        image_bytes = f.read()

    prompt = """
    You are reading a medical prescription image. Extract the following information
    and return ONLY a valid JSON object, with no markdown, no backticks, no extra text.

    Structure exactly like this:
    {
      "condition": "A short, plain description of what condition this prescription appears to be treating, based on the medicines listed",
      "medicines": [
        {"name": "", "dosage": "", "frequency": "", "instruction": ""}
      ],
      "care_tips": [
        "5 to 7 short, general self-care tips relevant to this condition, such as rest, hydration, or diet advice"
      ],
      "disclaimer": "A short reminder that this is AI-generated guidance and the user should follow their doctor's advice and consult them with any concerns"
    }

    Keep every field concise and in plain language, suitable for a patient with no medical background.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=file.mimetype),
            prompt
        ]
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    import json
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        return jsonify({"message": "AI response could not be read as JSON", "raw": raw_text}), 500

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (user_id, filename, upload_date, condition_summary) VALUES (?, ?, ?, ?)",
        (session["user_id"], unique_filename, time.strftime("%Y-%m-%d %H:%M"), result.get("condition"))
    )
    conn.commit()
    conn.close()

    return jsonify(result), 200



@app.route("/api/save-medicines", methods=["POST"])
def api_save_medicines():
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401

    data = request.get_json()
    medicines = data.get("medicines", [])

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()

    for med in medicines:
        cursor.execute(
            "INSERT INTO medicines (user_id, name, dosage, frequency, instruction) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], med.get("name"), med.get("dosage"), med.get("frequency"), med.get("instruction"))
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Medicines saved"}), 200






#chat bot route
@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401

    data = request.get_json()
    user_message = data.get("message", "")
    history = data.get("history", [])

    contents = []
    for msg in history:
        contents.append(msg["text"])
    contents.append(user_message)

    conversation_text = "\n".join(contents)

    prompt = f"""You are a helpful medical assistant inside a health app called Apricity AI.
    Answer briefly and clearly, in plain language, for someone with no medical background.
    Always remind them to consult a doctor for serious concerns.
    Here is the conversation so far, most recent message last:

    {conversation_text}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return jsonify({"reply": response.text}), 200


@app.route('/chat')
def chat():
    return render_template('chat.html', name=session.get('name'))  # match however you pass user data elsewhere


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


#Dose taken 
@app.route("/api/mark-dose/<int:medicine_id>", methods=["POST"])
def api_mark_dose(medicine_id):
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401

    import datetime
    today = datetime.date.today().isoformat()

    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM doses WHERE medicine_id = ? AND user_id = ? AND dose_date = ?",
        (medicine_id, session["user_id"], today)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE doses SET status = ? WHERE id = ?", ("taken", existing[0]))
    else:
        cursor.execute(
            "INSERT INTO doses (medicine_id, user_id, dose_date, status) VALUES (?, ?, ?, ?)",
            (medicine_id, session["user_id"], today, "taken")
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Marked as taken"}), 200




@app.route("/admin/users")
def admin_users():
    conn = sqlite3.connect("healthconnect.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM users")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)



init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)