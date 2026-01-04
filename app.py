from flask import Flask, render_template, request, redirect, session, jsonify
from db_config import db
from datetime import date, timedelta
from functools import wraps

# =========================
# APP CONFIGURATION
# =========================
app = Flask(__name__)
app.secret_key = "foodconnect_secret"  # Do NOT change (used for sessions)


# =========================
# LOGIN REQUIRED DECORATOR
# =========================
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return route_function(*args, **kwargs)
    return wrapper


# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    """
    Redirect users based on login status
    """
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session.clear()        # Prevent session fixation
            session["user"] = user["email"]
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, role)
            )
            db.commit()
        except Exception:
            return render_template("register.html", error="Email already exists")

        return redirect("/login")

    return render_template("register.html")


# =========================
# DASHBOARD (PROTECTED)
# =========================
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM donations")
    total_donations = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(quantity) AS meals FROM donations")
    total_meals = cursor.fetchone()["meals"] or 0

    return render_template(
        "dashboard.html",
        total_donations=total_donations,
        total_meals=total_meals
    )


# =========================
# ADD DONATION
# =========================
@app.route("/add-donation", methods=["GET", "POST"])
@login_required
def add_donation():
    if request.method == "POST":
        donor_name = request.form["donor_name"]
        food_type = request.form["food_type"]
        quantity = request.form["quantity"]
        location = request.form["location"]
        expiry_date = request.form["expiry_date"]

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO donations (donor_name, food_type, quantity, location, expiry_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (donor_name, food_type, quantity, location, expiry_date)
        )
        db.commit()

        return redirect("/dashboard")

    return render_template("add_donation.html")


# =========================
# VIEW DONATIONS
# =========================
@app.route("/view-donations")
@login_required
def view_donations():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM donations ORDER BY expiry_date ASC")
    donations = cursor.fetchall()

    return render_template("view_donations.html", donations=donations)


# =========================
# AI INSIGHTS (JSON API)
# =========================
@app.route("/ai-insights")
@login_required
def ai_insights():
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT SUM(quantity) AS total_meals FROM donations")
    total_meals = cursor.fetchone()["total_meals"] or 0

    cursor.execute("SELECT COUNT(*) AS total_donations FROM donations")
    total_donations = cursor.fetchone()["total_donations"]

    urgent_date = date.today() + timedelta(days=2)
    cursor.execute(
        "SELECT COUNT(*) AS urgent FROM donations WHERE expiry_date <= %s",
        (urgent_date,)
    )
    urgent = cursor.fetchone()["urgent"]

    return jsonify({
        "total_meals": total_meals,
        "total_donations": total_donations,
        "urgent_donations": urgent
    })


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
