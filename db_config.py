import mysql.connector

# =========================
# DATABASE CONNECTION
# =========================
"""
This module creates and provides a reusable MySQL
database connection for the FoodConnect application.
"""

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Nit@7913",   # ⚠️ Move this to env variable for public GitHub
        database="foodconnect"
    )

    if db.is_connected():
        print("✅ MySQL database connected successfully")

except mysql.connector.Error as error:
    print("❌ Failed to connect to MySQL database:", error)
    db = None
