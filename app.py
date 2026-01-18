from flask import Flask, render_template, request, redirect, session, jsonify
from datetime import date, timedelta
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "foodconnect_secret"

DB_PATH = "foodconnect.db"

# -------------------------
# DATABASE HELPERS
# -------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_name TEXT,
        food_type TEXT,
        quantity INTEGER,
        location TEXT,
        expiry_date DATE
    )
    """)

    conn.commit()
    conn.close()

# -------------------------
# LOGIN REQUIRED
# -------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return redirect("/login")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (
                    request.form["name"],
                    request.form["email"],
                    request.form["password"],
                    request.form["role"]
                )
            )
            conn.commit()
        except:
            return render_template("register.html", error="Email already exists")
        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    conn = get_db()

    total_donations = conn.execute(
        "SELECT COUNT(*) FROM donations WHERE expiry_date >= ?",
        (today,)
    ).fetchone()[0]

    total_meals = conn.execute(
        "SELECT SUM(quantity) FROM donations WHERE expiry_date >= ?",
        (today,)
    ).fetchone()[0] or 0

    conn.close()

    return render_template(
        "dashboard.html",
        total_donations=total_donations,
        total_meals=total_meals
    )

# -------------------------
# ADD DONATION
# -------------------------
@app.route("/add-donation", methods=["GET", "POST"])
@login_required
def add_donation():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO donations VALUES (NULL, ?, ?, ?, ?, ?)",
            (
                request.form["donor_name"],
                request.form["food_type"],
                request.form["quantity"],
                request.form["location"],
                request.form["expiry_date"]
            )
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add_donation.html")

# -------------------------
# VIEW DONATIONS
# -------------------------
@app.route("/view-donations")
@login_required
def view_donations():
    today = date.today()
    conn = get_db()
    donations = conn.execute(
        "SELECT * FROM donations WHERE expiry_date >= ? ORDER BY expiry_date",
        (today,)
    ).fetchall()
    conn.close()
    return render_template("view_donations.html", donations=donations)

# -------------------------
# AI INSIGHTS
# -------------------------
@app.route("/ai-insights")
@login_required
def ai_insights():
    today = date.today()
    urgent_date = today + timedelta(days=2)
    conn = get_db()

    total_meals = conn.execute(
        "SELECT SUM(quantity) FROM donations WHERE expiry_date >= ?",
        (today,)
    ).fetchone()[0] or 0

    total_donations = conn.execute(
        "SELECT COUNT(*) FROM donations WHERE expiry_date >= ?",
        (today,)
    ).fetchone()[0]

    urgent = conn.execute(
        "SELECT COUNT(*) FROM donations WHERE expiry_date BETWEEN ? AND ?",
        (today, urgent_date)
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "total_meals": total_meals,
        "total_donations": total_donations,
        "urgent_donations": urgent
    })

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------------
# START
# -------------------------
init_db()
