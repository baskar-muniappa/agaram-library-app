from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "library.db"

# ---------- Database Setup ----------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                class TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                barcode TEXT UNIQUE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                book_id INTEGER,
                checkout_date TEXT,
                return_date TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        ''')
        conn.commit()

# ---------- Routes ----------
@app.route("/students", methods=["POST"])
def add_students():
    data = request.json  # List of students
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for s in data:
            c.execute("INSERT INTO students (first_name, last_name, class) VALUES (?, ?, ?)", 
                      (s["first_name"], s["last_name"], s["class"]))
        conn.commit()
    return jsonify({"message": "Students added"}), 201

@app.route("/students", methods=["GET"])
def get_students():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, first_name, last_name, class FROM students")
        rows = c.fetchall()
        result = [
            {"id": r[0], "first_name": r[1], "last_name": r[2], "class": r[3]}
            for r in rows
        ]
    return jsonify(result)


@app.route("/books", methods=["POST"])
def add_books():
    data = request.json  # List of books
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for b in data:
            c.execute("INSERT OR IGNORE INTO books (title, barcode) VALUES (?, ?)", 
                      (b["title"], str(b["barcode"])))
        conn.commit()
    return jsonify({"message": "Books added"}), 201

@app.route("/student-loans/<int:student_id>", methods=["GET"])
def get_student_loans(student_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT b.title, b.barcode, t.checkout_date
            FROM transactions t
            JOIN books b ON t.book_id = b.id
            WHERE t.student_id = ?
              AND t.return_date IS NULL
        ''', (student_id,))
        rows = c.fetchall()

    result = [
        {"title": r[0], "barcode": r[1], "checkout_date": r[2]}
        for r in rows
    ]
    return jsonify(result)

@app.route("/checkout", methods=["POST"])
def checkout_book():
    data = request.json
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Step 1: Check if student already has a borrowed book
        c.execute('''
            SELECT COUNT(*) FROM transactions
            WHERE student_id = ? AND return_date IS NULL
        ''', (data["student_id"],))
        count = c.fetchone()[0]
        if count > 0:
            return jsonify({"error": "Student already has a book checked out"}), 400

        # Step 2: Get book and student IDs
        c.execute("SELECT id FROM books WHERE barcode = ?", (data["barcode"],))
        book = c.fetchone()
        c.execute("SELECT id FROM students WHERE id = ?", (data["student_id"],))
        student = c.fetchone()
        if not book or not student:
            return jsonify({"error": "Invalid student or book"}), 400

        # Step 3: Checkout
        c.execute('''
            INSERT INTO transactions (student_id, book_id, checkout_date)
            VALUES (?, ?, ?)
        ''', (student[0], book[0], datetime.now().isoformat()))
        conn.commit()

    return jsonify({"message": "Book checked out"}), 200

@app.route("/return", methods=["POST"])
def return_book():
    data = request.json
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Step 1: Get the most recent open transaction for this book
        c.execute('''
            SELECT id FROM transactions
            WHERE book_id = (SELECT id FROM books WHERE barcode = ?)
              AND return_date IS NULL
            ORDER BY checkout_date DESC
            LIMIT 1
        ''', (data["barcode"],))
        row = c.fetchone()

        if not row:
            return jsonify({"error": "No open transaction found for this book"}), 400

        transaction_id = row[0]

        # Step 2: Update it
        c.execute('''
            UPDATE transactions
            SET return_date = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), transaction_id))

        conn.commit()

    return jsonify({"message": "Book returned"}), 200

@app.route("/daily-report")
def daily_report():
    date = request.args.get("date")  # format YYYY-MM-DD
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT s.first_name, s.last_name, s.class, b.title, t.checkout_date
            FROM transactions t
            JOIN students s ON t.student_id = s.id
            JOIN books b ON t.book_id = b.id
            WHERE date(t.checkout_date) = ?
        ''', (date,))
        rows = c.fetchall()
    report = [
        {
            "first_name": r[0],
            "last_name": r[1],
            "class": r[2],
            "book_title": r[3],
            "checkout_date": r[4]
        }
        for r in rows
    ]
    return jsonify(report)

import os

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)