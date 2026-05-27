"""
Interview Slot Booking System
A beginner-friendly Flask application for managing interview slots.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

# ─── App Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "interview_booking.db")


# ─── Database Helpers ─────────────────────────────────────────────────────────
def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dict-like access: row["column"]
    return conn


def init_db():
    """Create tables if they don't exist and seed admin account."""
    conn = get_db()
    c = conn.cursor()

    # Users table (students + admin)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'student'  -- 'student' or 'admin'
        )
    """)

    # Interview slots table
    c.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            company      TEXT    NOT NULL,
            role         TEXT    NOT NULL,
            date         TEXT    NOT NULL,   -- e.g. "2025-08-15"
            time         TEXT    NOT NULL,   -- e.g. "10:00 AM"
            venue        TEXT    NOT NULL,
            total_seats  INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Bookings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            slot_id    INTEGER NOT NULL,
            booked_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (slot_id) REFERENCES slots(id),
            UNIQUE (user_id, slot_id)   -- Prevent duplicate bookings
        )
    """)

    # Seed default admin (email: admin@interview.com / password: admin123)
    existing = c.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if not existing:
        hashed = generate_password_hash("admin123")
        c.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@interview.com", hashed, "admin"),
        )

    conn.commit()
    conn.close()


# Ensure the database exists when the module is imported by Gunicorn or Render.
init_db()


# ─── Auth Decorators ──────────────────────────────────────────────────────────
def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Redirect to home if user is not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated


# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Landing page: redirect based on session."""
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Student registration."""
    if request.method == "POST":
        name  = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]

        if not name or not email or not pwd:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            flash("Email already registered. Please log in.", "warning")
            conn.close()
            return redirect(url_for("login"))

        hashed = generate_password_hash(pwd)
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
            (name, email, hashed),
        )
        conn.commit()
        conn.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login for both students and admin."""
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], pwd):
            # Store user info in session
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            session["role"]      = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ─── Shared Home (redirects by role) ─────────────────────────────────────────
@app.route("/home")
@login_required
def home():
    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("student_dashboard"))


# ─── Student Routes ───────────────────────────────────────────────────────────
@app.route("/student/dashboard")
@login_required
def student_dashboard():
    """Student home: stats + quick links."""
    conn = get_db()
    uid = session["user_id"]

    total_slots    = conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
    my_bookings    = conn.execute("SELECT COUNT(*) FROM bookings WHERE user_id=?", (uid,)).fetchone()[0]
    upcoming_count = conn.execute("""
        SELECT COUNT(*) FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        WHERE b.user_id = ? AND s.date >= date('now')
    """, (uid,)).fetchone()[0]
    conn.close()

    return render_template("student_dashboard.html",
                           total_slots=total_slots,
                           my_bookings=my_bookings,
                           upcoming_count=upcoming_count)


@app.route("/student/slots")
@login_required
def view_slots():
    """View all available slots; supports search by company."""
    search = request.args.get("search", "").strip()
    conn   = get_db()
    uid    = session["user_id"]

    # Get all slots with booked seat count
    if search:
        slots = conn.execute("""
            SELECT s.*,
                   COUNT(b.id) AS booked_count
            FROM slots s
            LEFT JOIN bookings b ON b.slot_id = s.id
            WHERE s.company LIKE ?
            GROUP BY s.id
            ORDER BY s.date, s.time
        """, (f"%{search}%",)).fetchall()
    else:
        slots = conn.execute("""
            SELECT s.*,
                   COUNT(b.id) AS booked_count
            FROM slots s
            LEFT JOIN bookings b ON b.slot_id = s.id
            GROUP BY s.id
            ORDER BY s.date, s.time
        """).fetchall()

    # Find which slot IDs the current student has already booked
    my_booked_ids = {
        row["slot_id"]
        for row in conn.execute("SELECT slot_id FROM bookings WHERE user_id=?", (uid,)).fetchall()
    }
    conn.close()

    return render_template("view_slots.html",
                           slots=slots,
                           my_booked_ids=my_booked_ids,
                           search=search)


@app.route("/student/book/<int:slot_id>", methods=["POST"])
@login_required
def book_slot(slot_id):
    """Book a slot for the logged-in student."""
    uid  = session["user_id"]
    conn = get_db()

    # Check slot exists
    slot = conn.execute("SELECT * FROM slots WHERE id=?", (slot_id,)).fetchone()
    if not slot:
        flash("Slot not found.", "danger")
        conn.close()
        return redirect(url_for("view_slots"))

    # Check for seats
    booked = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE slot_id=?", (slot_id,)
    ).fetchone()[0]
    if booked >= slot["total_seats"]:
        flash("Sorry, this slot is fully booked.", "warning")
        conn.close()
        return redirect(url_for("view_slots"))

    # Check for duplicate booking
    already = conn.execute(
        "SELECT id FROM bookings WHERE user_id=? AND slot_id=?", (uid, slot_id)
    ).fetchone()
    if already:
        flash("You have already booked this slot.", "warning")
        conn.close()
        return redirect(url_for("view_slots"))

    # Insert booking
    conn.execute(
        "INSERT INTO bookings (user_id, slot_id) VALUES (?, ?)", (uid, slot_id)
    )
    conn.commit()
    conn.close()
    flash(f"Successfully booked slot at {slot['company']}!", "success")
    return redirect(url_for("my_bookings"))


@app.route("/student/bookings")
@login_required
def my_bookings():
    """Show student's current bookings."""
    uid  = session["user_id"]
    conn = get_db()

    bookings = conn.execute("""
        SELECT b.id AS booking_id, s.company, s.role, s.date, s.time, s.venue, b.booked_at
        FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        WHERE b.user_id = ?
        ORDER BY s.date, s.time
    """, (uid,)).fetchall()
    conn.close()

    return render_template("my_bookings.html", bookings=bookings)


@app.route("/student/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking (only the owner can cancel)."""
    uid  = session["user_id"]
    conn = get_db()

    booking = conn.execute(
        "SELECT * FROM bookings WHERE id=? AND user_id=?", (booking_id, uid)
    ).fetchone()

    if not booking:
        flash("Booking not found or not yours.", "danger")
    else:
        conn.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        conn.commit()
        flash("Booking cancelled successfully.", "info")

    conn.close()
    return redirect(url_for("my_bookings"))


# ─── Admin Routes ─────────────────────────────────────────────────────────────
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics."""
    conn = get_db()

    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    total_slots    = conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

    # Recent bookings (latest 5)
    recent = conn.execute("""
        SELECT u.name AS student, s.company, s.date, s.time, b.booked_at
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN slots  s ON b.slot_id = s.id
        ORDER BY b.booked_at DESC
        LIMIT 5
    """).fetchall()

    # Most popular company
    popular = conn.execute("""
        SELECT s.company, COUNT(b.id) AS cnt
        FROM bookings b JOIN slots s ON b.slot_id = s.id
        GROUP BY s.company ORDER BY cnt DESC LIMIT 1
    """).fetchone()

    conn.close()
    return render_template("admin_dashboard.html",
                           total_students=total_students,
                           total_slots=total_slots,
                           total_bookings=total_bookings,
                           recent=recent,
                           popular=popular)


@app.route("/admin/slots")
@login_required
@admin_required
def admin_slots():
    """Admin: list all slots with booking counts."""
    conn  = get_db()
    slots = conn.execute("""
        SELECT s.*, COUNT(b.id) AS booked_count
        FROM slots s
        LEFT JOIN bookings b ON b.slot_id = s.id
        GROUP BY s.id
        ORDER BY s.date, s.time
    """).fetchall()
    conn.close()
    return render_template("admin_slots.html", slots=slots)


@app.route("/admin/slots/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_slot():
    """Admin: add a new interview slot."""
    if request.method == "POST":
        company = request.form["company"].strip()
        role    = request.form["role"].strip()
        date    = request.form["date"]
        time    = request.form["time"]
        venue   = request.form["venue"].strip()
        seats   = int(request.form.get("total_seats", 1))

        if not all([company, role, date, time, venue]):
            flash("All fields are required.", "danger")
            return redirect(url_for("add_slot"))

        conn = get_db()
        conn.execute(
            "INSERT INTO slots (company, role, date, time, venue, total_seats) VALUES (?, ?, ?, ?, ?, ?)",
            (company, role, date, time, venue, seats),
        )
        conn.commit()
        conn.close()
        flash(f"Slot for {company} added successfully!", "success")
        return redirect(url_for("admin_slots"))

    return render_template("add_slot.html")


@app.route("/admin/slots/delete/<int:slot_id>", methods=["POST"])
@login_required
@admin_required
def delete_slot(slot_id):
    """Admin: delete a slot and its bookings."""
    conn = get_db()
    conn.execute("DELETE FROM bookings WHERE slot_id=?", (slot_id,))
    conn.execute("DELETE FROM slots WHERE id=?", (slot_id,))
    conn.commit()
    conn.close()
    flash("Slot deleted successfully.", "info")
    return redirect(url_for("admin_slots"))


@app.route("/admin/slots/<int:slot_id>/bookings")
@login_required
@admin_required
def slot_bookings(slot_id):
    """Admin: see who booked a particular slot."""
    conn = get_db()
    slot = conn.execute("SELECT * FROM slots WHERE id=?", (slot_id,)).fetchone()
    if not slot:
        flash("Slot not found.", "danger")
        conn.close()
        return redirect(url_for("admin_slots"))

    bookings = conn.execute("""
        SELECT u.name, u.email, b.booked_at
        FROM bookings b JOIN users u ON b.user_id = u.id
        WHERE b.slot_id = ?
        ORDER BY b.booked_at
    """, (slot_id,)).fetchall()
    conn.close()
    return render_template("slot_bookings.html", slot=slot, bookings=bookings)


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
