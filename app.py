from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np
import psycopg2
from psycopg2 import errors
from complaint_module import complaint_bp, mail
import os
app = Flask(__name__)
CORS(app)
app.secret_key = "college_secret_key"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")


mail.init_app(app)

# ---------- DATABASE ----------
conn = psycopg2.connect(
    dbname="college",
    user="postgres",
    password="meera"
)
cur = conn.cursor()

# ---------- CHATBOT ----------
# ================= EMBEDDING MODEL =================
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ================= LOAD QUESTIONS =================
cur.execute("SELECT question, answer, embedding FROM qa_pairs")
rows = cur.fetchall()

questions = []
answers = []
embeddings = []

for q, a, emb in rows:
    if isinstance(emb, str):
        emb = np.array(ast.literal_eval(emb), dtype="float32")
    else:
        emb = np.array(emb, dtype="float32")

    questions.append(q)
    answers.append(a)
    embeddings.append(emb)

embeddings = np.vstack(embeddings)

# ================= FAISS =================
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
faiss.normalize_L2(embeddings)
index.add(embeddings)

print(f"✅ Loaded {len(questions)} question embeddings")

def suggest_venue(purpose, strength):
    cur.execute("""
        SELECT venue_name, capacity
        FROM venues
        ORDER BY capacity ASC
    """)
    venues = cur.fetchall()

    for venue_name, capacity in venues:
        if strength <= capacity:
            return venue_name

    # fallback → biggest hall
    return venues[-1][0]

# ---------- HOME ----------
@app.route("/")
def home():
    # Auto delete daily news older than 24 hours
    cur.execute("""
        DELETE FROM daily_news
        WHERE created_at < NOW() - INTERVAL '24 HOURS'
    """)
    conn.commit()

    # Fetch last 24 hours daily news
    cur.execute("""
        SELECT title, content
        FROM daily_news
        WHERE created_at >= NOW() - INTERVAL '24 HOURS'
        ORDER BY created_at DESC
    """)
    news = cur.fetchall()

    # Fetch active events
    cur.execute("""
        SELECT title, content
        FROM events
        WHERE expiry_date >= CURRENT_DATE
        ORDER BY expiry_date
    """)
    events = cur.fetchall()

    return render_template("index.html", news=news, events=events)

    # ---------- Student DASHBOARD ----------
@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect("/student/login")

    return render_template("student_dashboard.html")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur.execute(
            "SELECT id, name FROM students WHERE email=%s AND password=%s",
            (email, password)
        )
        student = cur.fetchone()

        if student:
            session["student_id"] = student[0]
            session["student_name"] = student[1]
            return redirect("/student/dashboard")
        else:
            return render_template("student_login.html", error="Invalid login")

    return render_template("student_login.html")

#---------------student profile-------------
@app.route("/student/profile")
def student_profile():
    student_id = session.get("student_id")  # stored at login
    if not student_id:
        return redirect("/student/login") 

    cur.execute(
        "SELECT name, email, department,gender, year, address, age FROM students WHERE id = %s",
        (student_id,)
    )
    student = cur.fetchone()

    return render_template("student_profile.html", student=student)


    #-------------------staff login------------------
@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur.execute(
            "SELECT id, name FROM staff WHERE email=%s AND password=%s",
            (email, password)
        )
        staff = cur.fetchone()

        if staff:
            session["staff_id"] = staff[0]
            session["staff_name"] = staff[1]
            return redirect("/staff/dashboard")
        else:
            return render_template("staff_login.html", error="Invalid login")

    return render_template("staff_login.html")




# ---------- STAFF DASHBOARD ----------
@app.route("/staff/dashboard")
def staff_dashboard():
    if "staff_id" not in session:
        return redirect("/staff/login")

    return render_template("staff_dashboard.html")


@app.route("/staff/profile")
def staff_profile():
    staff_id = session.get("staff_id")  # stored at login

    cur.execute(
        "SELECT name, email, department, role ,gender,address, phone FROM staff WHERE id = %s",
        (staff_id,)
    )
    staff = cur.fetchone()

    return render_template("staff_profile.html", staff=staff)


# ---------- DAILY NEWS ----------
@app.route("/staff/news")
def staff_news():
    return render_template("news.html")


@app.route("/staff/add-news", methods=["POST"])
def add_news():
    cur.execute(
        "INSERT INTO daily_news (title, content) VALUES (%s, %s)",
        (request.form["title"], request.form["content"])
    )
    conn.commit()
    return redirect("/staff/dashboard")

# ---------- EVENTS ----------
@app.route("/staff/event")
def staff_event():
    return render_template("event.html")

@app.route("/staff/add-event", methods=["POST"])
def add_event():
    cur.execute(
        "INSERT INTO events (title, content, expiry_date) VALUES (%s, %s, %s)",
        (request.form["title"], request.form["content"], request.form["expiry_date"])
    )
    conn.commit()
    return redirect("/staff/dashboard")

# ---------- VENUE ----------
SLOTS = [
    "09:00 - 10:00", "10:00 - 11:00",
    "11:00 - 12:00", "01:00 - 02:00",
    "02:00 - 03:00", "03:00 - 04:00"
]
VENUES = ["PLL Seminar Hall","Edward Noting Hall","Main Hall","B1 Seminar Hall"]

@app.route("/staff/venue")
def venue_dashboard():
    return render_template("venue_dashboard.html")

@app.route("/staff/venue/book", methods=["GET", "POST"])
def book_venue():
    message = ""
    if request.method == "POST":
        staff_id = session['staff_id']  # assuming staff login session
        venue = request.form['venue']
        date = request.form['date']
        slot = request.form['slot']
        purpose = request.form['purpose']
        strength = int(request.form['strength'])

        # Check if the slot is already booked & approved
        cur.execute("""
            SELECT id, staff_id FROM venue_requests
            WHERE venue_name=%s AND date=%s AND slot=%s AND status='Approved'
        """, (venue, date, slot))
        conflict = cur.fetchone()

        if conflict:
            # Slot already approved → create a request for admin to approve later
            cur.execute("""
                INSERT INTO venue_requests (staff_id, venue_name, date, slot, purpose, expected_strength, status)
                VALUES (%s,%s,%s,%s,%s,%s,'Pending')
            """, (staff_id, venue, date, slot, purpose, strength))
            conn.commit()

            # Notify staff about conflict
            cur.execute("""
                INSERT INTO notifications (staff_id, message)
                VALUES (%s,%s)
            """, (staff_id, f"⚠️ The slot {slot} for {venue} is already booked. Admin will suggest an alternative."))
            conn.commit()
            message = "⚠️ Slot already booked. Admin will review."

        else:
            # No conflict → send request to admin for approval
            cur.execute("""
                INSERT INTO venue_requests (staff_id, venue_name, date, slot, purpose, expected_strength, status)
                VALUES (%s,%s,%s,%s,%s,%s,'Pending')
            """, (staff_id, venue, date, slot, purpose, strength))
            conn.commit()
            message = "✅ Booking request sent to admin."

    return render_template("venue_booking.html", venues=VENUES, slots=SLOTS, message=message)


@app.route("/staff/venue/my-bookings")
def my_bookings():
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT vr.id, vr.venue_name, vr.date, vr.slot, vr.status
            FROM venue_requests vr
            WHERE vr.staff_id = %s
        """, (session['staff_id'],))
        data = cur.fetchall()
        return render_template("my_bookings.html", bookings=data)

    except Exception as e:
        conn.rollback()
        print(e)
        return "Database error", 500




@app.route("/staff/venue/cancel", methods=["POST"])
def cancel_booking():
    booking_id = request.form["booking_id"]

    # Mark as "Cancel Requested"
    cur.execute("UPDATE venue_requests SET status='Cancel Requested' WHERE id=%s", (booking_id,))
    conn.commit()

    # Get info of cancelled booking
    cur.execute("SELECT venue_name, date, slot FROM venue_requests WHERE id=%s", (booking_id,))
    venue, date, slot = cur.fetchone()

    # Notify all pending requests for same venue & slot
    cur.execute("""
        SELECT staff_id FROM venue_requests
        WHERE venue_name=%s AND date=%s AND slot=%s AND status='Pending'
    """, (venue, date, slot))
    pending_staffs = cur.fetchall()
    for s in pending_staffs:
        cur.execute("""
            INSERT INTO notifications (staff_id, message)
            VALUES (%s, %s)
        """, (s[0], f"⚠️ The slot {slot} for {venue} is now available. Please re-request or wait for admin approval."))
    conn.commit()

    return redirect("/staff/venue/my-bookings")



@app.route("/admin/venue")
def admin_venue():
    cur.execute("""
        SELECT id, staff_id, venue_name, date, slot, purpose, expected_strength, status
        FROM venue_requests
        WHERE status IN ('Pending', 'Cancel Requested')
        ORDER BY date 
    """)
    requests = cur.fetchall()
    return render_template("admin_venue_requests.html", requests=requests)


@app.route("/admin/venue/reject/<int:req_id>")
def reject_venue(req_id):
    cur.execute("""
        UPDATE venue_requests
        SET status = 'Rejected'
        WHERE id = %s
    """, (req_id,))
    conn.commit()
    return redirect("/admin/venue")

@app.route("/admin/venue/approve/<int:req_id>")
def approve_venue(req_id):

    cur.execute("""
        SELECT staff_id, venue_name, date, slot, purpose, expected_strength
        FROM venue_requests
        WHERE id = %s
    """, (req_id,))
    staff_id, venue, date, slot, purpose, strength = cur.fetchone()

    # ✅ CORRECT conflict check
    cur.execute("""
        SELECT id FROM venue_requests
        WHERE venue_name=%s
          AND date=%s
          AND slot=%s
          AND status='Approved'
          AND id != %s
    """, (venue, date, slot, req_id))
    conflict = cur.fetchone()

    if conflict:
        suggested_venue = suggest_venue(purpose, strength)

        cur.execute("""
            UPDATE venue_requests
            SET venue_name=%s, status='Approved'
            WHERE id=%s
        """, (suggested_venue, req_id))
        conn.commit()

        cur.execute("""
            INSERT INTO notifications (staff_id, message)
            VALUES (%s, %s)
        """, (
            staff_id,
            f"⚠️ Slot conflict. Approved at {suggested_venue} instead of {venue}."
        ))
        conn.commit()

    else:
        cur.execute("""
            UPDATE venue_requests
            SET status='Approved'
            WHERE id=%s
        """, (req_id,))
        conn.commit()

        cur.execute("""
            INSERT INTO notifications (staff_id, message)
            VALUES (%s, %s)
        """, (
            staff_id,
            f"✅ Your booking at {venue} on {date} is approved."
        ))
        conn.commit()

    return redirect("/admin/venue")


@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html") 

@app.route("/admin/venue/cancel-approve/<int:req_id>")
def approve_cancel(req_id):

    # get venue details FIRST (required)
    cur.execute("""
        SELECT venue_name, date, slot
        FROM venue_requests
        WHERE id = %s
    """, (req_id,))
    venue_name, date, slot = cur.fetchone()

    # cancel the approval
    cur.execute("""
        UPDATE venue_requests
        SET status = 'Cancelled'
        WHERE id = %s
    """, (req_id,))
    conn.commit()

    # notify waiting staff
    cur.execute("""
        SELECT staff_id
        FROM venue_requests
        WHERE venue_name = %s
          AND date = %s
          AND slot = %s
          AND status IN ('pending', 'rejected')
    """, (venue_name, date, slot))

    waiting_staff = cur.fetchall()

    for staff in waiting_staff:
        cur.execute("""
            INSERT INTO notifications (staff_id, message)
            VALUES (%s, %s)
        """, (
            staff[0],
            f"Venue {venue_name} is now available for {date} ({slot}). You can book it."
        ))

    conn.commit()

    return redirect("/admin/venue")

@app.route("/staff/notifications")
def staff_notifications():
    staff_id = session['staff_id']  # get logged-in staff
    cur.execute("""
        SELECT message, created_at
        FROM notifications
        WHERE staff_id = %s
        ORDER BY created_at DESC
    """, (staff_id,))
    notifications = cur.fetchall()
    return render_template("staff_notifications.html", notifications=notifications)

@app.route("/admin/complaints")
def admin_complaints():
    cur.execute("SELECT * FROM complaints ORDER BY created_at DESC")
    complaints = cur.fetchall()
    return render_template("admin_complaints.html", complaints=complaints)


# ---------- CHAT ----------
@app.route("/chat", methods=["POST"])
def chat():
    user_question = request.json.get("question", "").strip()
    if not user_question:
        return jsonify({"answer": "Please ask a valid question."})

    q_emb = embed_model.encode([user_question]).astype("float32")
    faiss.normalize_L2(q_emb)

    D, I = index.search(q_emb, k=3)

    best_score = float(D[0][0])
    best_idx = I[0][0]

    # 🔍 DEBUG (VERY IMPORTANT – KEEP FOR NOW)
    print("\nUSER QUESTION:", user_question)
    print("BEST SCORE:", best_score)
    print("MATCHED QUESTION:", questions[best_idx])

    # ✅ LOWER & REALISTIC THRESHOLD
    if best_score < 0.45:
        return jsonify({"answer": "Sorry, I do not know the answer."})

    # ✅ SOFTER GAP CHECK
    if len(D[0]) > 1 and (D[0][0] - D[0][1]) < 0.03:
        return jsonify({"answer": "Sorry, I am not confident about the answer."})

    return jsonify({
        "answer": answers[best_idx],
        "confidence": round(best_score, 2)
    })


app.register_blueprint(complaint_bp)


if __name__ == "__main__":
    app.run(debug=True)

