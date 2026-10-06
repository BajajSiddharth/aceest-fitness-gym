import os
import sqlite3
from flask import Flask, jsonify, request

DATABASE = os.getenv("DB_NAME", "aceest_fitness.db")

# Core fitness program specifications ported from baseline
PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": "Back Squat 5x5, EMOM 20min Assault Bike, Bench Press, Deadlifts",
        "diet": "Egg Whites, Grilled Chicken, Fish Curry, Target: ~2000 kcal",
        "factor": 22
    },
    "Muscle Gain (MG)": {
        "workout": "Squat 5x5, Bench 5x5, Deadlift 4x6, Overhead Press, Barbell Rows",
        "diet": "Eggs + PB Oats, Chicken Biryani, Mutton Curry, Target: ~3200 kcal",
        "factor": 35
    },
    "Beginner (BG)": {
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced High-Protein Meals, Target: 120g/day protein",
        "factor": 26
    }
}

def get_db_connection(db_path=None):
    target_db = db_path if db_path else DATABASE
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            age INTEGER,
            weight REAL,
            program TEXT,
            calories INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
        )
    """)
    conn.commit()
    conn.close()

def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or DATABASE

    init_db(app.config["DATABASE"])

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "service": "ACEest Fitness & Gym API",
            "version": "1.0.0",
            "status": "online"
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.route("/programs", methods=["GET"])
    def get_programs():
        return jsonify(PROGRAMS), 200

    @app.route("/clients", methods=["POST"])
    def create_or_update_client():
        data = request.get_json()
        if not data or "name" not in data or "program" not in data:
            return jsonify({"error": "Fields 'name' and 'program' are required"}), 400

        name = data["name"].strip()
        program = data["program"]

        if program not in PROGRAMS:
            return jsonify({"error": f"Invalid program. Available: {list(PROGRAMS.keys())}"}), 400

        age = data.get("age", 0)
        weight = float(data.get("weight", 0.0))
        calories = int(weight * PROGRAMS[program]["factor"]) if weight > 0 else 0

        conn = get_db_connection(app.config["DATABASE"])
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT OR REPLACE INTO clients (name, age, weight, program, calories)
                VALUES (?, ?, ?, ?, ?)
            """, (name, age, weight, program, calories))
            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

        return jsonify({
            "message": "Client record updated successfully",
            "client": {
                "name": name,
                "age": age,
                "weight": weight,
                "program": program,
                "calories": calories
            }
        }), 201

    @app.route("/clients/<string:name>", methods=["GET"])
    def get_client(name):
        conn = get_db_connection(app.config["DATABASE"])
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE name = ?", (name,))
        client = cur.fetchone()
        conn.close()

        if not client:
            return jsonify({"error": "Client not found"}), 404

        return jsonify({
            "id": client["id"],
            "name": client["name"],
            "age": client["age"],
            "weight": client["weight"],
            "program": client["program"],
            "calories": client["calories"]
        }), 200

    @app.route("/progress", methods=["POST"])
    def log_progress():
        data = request.get_json()
        if not data or not all(k in data for k in ("client_name", "week", "adherence")):
            return jsonify({"error": "Fields 'client_name', 'week', and 'adherence' are required"}), 400

        conn = get_db_connection(app.config["DATABASE"])
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO progress (client_name, week, adherence)
            VALUES (?, ?, ?)
        """, (data["client_name"], data["week"], int(data["adherence"])))
        conn.commit()
        conn.close()

        return jsonify({"message": "Weekly progress logged successfully"}), 201

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)