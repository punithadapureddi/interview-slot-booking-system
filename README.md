# 📅 Interview Slot Booking System

A beginner-friendly Flask web application that lets a college admin manage interview slots and students book them — all in one clean interface.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🔐 Auth | Student register/login, Admin login (separate roles) |
| 🗓️ Slots | Admin can add, view, and delete interview slots |
| 📌 Booking | Students can browse and book slots |
| 🚫 No duplicates | Each student can book a slot only once |
| ❌ Cancel | Students can cancel their bookings |
| 🔍 Search | Search slots by company name |
| 📊 Dashboard | Stats for both admin and students |
| 📱 Responsive | Bootstrap 5 mobile-friendly UI |

---

## 🏗️ Project Structure

```
interview-slot-booking/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── interview_booking.db      # SQLite database (auto-created)
├── README.md
├── static/
│   ├── css/style.css         # Custom styles
│   └── js/main.js            # Small JS enhancements
└── templates/
    ├── base.html             # Layout with navbar
    ├── login.html            # Login page
    ├── register.html         # Student registration
    ├── student_dashboard.html
    ├── view_slots.html       # Browse & book slots
    ├── my_bookings.html      # Student's bookings
    ├── admin_dashboard.html  # Admin stats
    ├── admin_slots.html      # Manage all slots
    ├── add_slot.html         # Add new slot form
    └── slot_bookings.html    # View bookings for a slot
```

---

## 🚀 Setup & Run (Local)

### 1. Clone / download the project

```bash
git clone <your-repo-url>
cd interview-slot-booking
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open your browser and visit: **http://127.0.0.1:5000**

The database (`interview_booking.db`) is created automatically on first run.

---

## 🔑 Default Credentials

| Role    | Email                    | Password  |
|---------|--------------------------|-----------|
| Admin   | admin@interview.com      | admin123  |
| Student | Register a new account   | —         |

> **Tip:** Change the admin password and `app.secret_key` in `app.py` before deploying!

---

## 🗄️ Database Schema

```sql
-- Users (students + admin)
CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,
    email    TEXT    NOT NULL UNIQUE,
    password TEXT    NOT NULL,
    role     TEXT    NOT NULL DEFAULT 'student'
);

-- Interview slots
CREATE TABLE slots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company      TEXT    NOT NULL,
    role         TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    time         TEXT    NOT NULL,
    venue        TEXT    NOT NULL,
    total_seats  INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Bookings
CREATE TABLE bookings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    slot_id    INTEGER NOT NULL REFERENCES slots(id),
    booked_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, slot_id)   -- prevents duplicates
);
```

---

## ☁️ Deployment on Render (Free)

1. Push your project to a GitHub repository.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Connect your GitHub repo.
4. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Add a secret environment variable: `SECRET_KEY` → any long random string.
6. Update `app.secret_key` in `app.py` to `os.environ.get("SECRET_KEY", "fallback")`.
7. Click **Deploy**.

> Note: Render's free tier uses an ephemeral filesystem, so SQLite data resets on each deploy. For persistent storage, use [Render's PostgreSQL](https://render.com/docs/databases) or [PlanetScale](https://planetscale.com).

---

## 🛡️ Security Notes (for production)

- Change `app.secret_key` to a long random string (use `secrets.token_hex(32)`).
- Store secrets in environment variables, not in source code.
- Switch from SQLite to PostgreSQL for multi-user production use.
- Add CSRF protection (e.g., Flask-WTF).
- Use HTTPS (Render/Heroku handle this automatically).

---

## 📚 Built With

- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [SQLite](https://sqlite.org/) — Embedded database
- [Bootstrap 5](https://getbootstrap.com/) — Responsive UI
- [Werkzeug](https://werkzeug.palletsprojects.com/) — Password hashing
- [Bootstrap Icons](https://icons.getbootstrap.com/) — Icon set

---

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first to discuss what you'd like to change.
