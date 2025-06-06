from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# Set your PostgreSQL URL (from Render or env)
DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://library_db_bt0l_user:VmAv5zeUUQdaNvvNsKL6cxCzBZaFB0cm@dpg-d0kvonbuibrs739t6ucg-a.virginia-postgres.render.com/library_db_bt0l"

app = Flask(__name__)
CORS(app)

# ---------- Database Setup ----------
def init_db():
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                class TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title TEXT,
                barcode TEXT UNIQUE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                book_id INTEGER REFERENCES books(id),
                checkout_date TIMESTAMP,
                return_date TIMESTAMP
            )
        ''')
        conn.commit()

@app.route("/", methods=["GET"])
def home():
    return "✅ Agaram Library API is running!"


# ---------- Routes ----------
@app.route("/students", methods=["POST"])
def add_students():
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        for s in data:
            c.execute("INSERT INTO students (first_name, last_name, class) VALUES (%s, %s, %s)",
                      (s["first_name"], s["last_name"], s["class"]))
        conn.commit()
    return jsonify({"message": "Students added"}), 201

@app.route("/students", methods=["GET"])
def get_students():
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("SELECT id, first_name, last_name, class FROM students")
        rows = c.fetchall()
    return jsonify(rows)

@app.route("/books", methods=["POST"])
def add_books():
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        for b in data:
            c.execute("INSERT INTO books (title, barcode) VALUES (%s, %s) ON CONFLICT (barcode) DO NOTHING",
                      (b["title"], str(b["barcode"])))
        conn.commit()
    return jsonify({"message": "Books added"}), 201

@app.route("/student-loans/<int:student_id>", methods=["GET"])
def get_student_loans(student_id):
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT b.title, b.barcode, t.checkout_date
            FROM transactions t
            JOIN books b ON t.book_id = b.id
            WHERE t.student_id = %s
              AND t.return_date IS NULL
        ''', (student_id,))
        rows = c.fetchall()
    return jsonify(rows)

@app.route("/checkout", methods=["POST"])
def checkout_book():
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*) FROM transactions
            WHERE student_id = %s AND return_date IS NULL
        ''', (data["student_id"],))
        count = c.fetchone()['count']
        if count > 0:
            return jsonify({"error": "Student already has a book checked out"}), 400

        c.execute("SELECT id FROM books WHERE barcode = %s", (data["barcode"],))
        book = c.fetchone()
        c.execute("SELECT id FROM students WHERE id = %s", (data["student_id"],))
        student = c.fetchone()
        if not book or not student:
            return jsonify({"error": "Invalid student or book"}), 400

        c.execute('''
            INSERT INTO transactions (student_id, book_id, checkout_date)
            VALUES (%s, %s, %s)
        ''', (student["id"], book["id"], datetime.now()))
        conn.commit()

    return jsonify({"message": "Book checked out"}), 200

@app.route("/return", methods=["POST"])
def return_book():
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()

        c.execute('''
            SELECT id FROM transactions
            WHERE book_id = (SELECT id FROM books WHERE barcode = %s)
              AND return_date IS NULL
            ORDER BY checkout_date DESC
            LIMIT 1
        ''', (data["barcode"],))
        row = c.fetchone()

        if not row:
            return jsonify({"error": "No open transaction found for this book"}), 400

        transaction_id = row["id"]

        c.execute('''
            UPDATE transactions
            SET return_date = %s
            WHERE id = %s
        ''', (datetime.now(), transaction_id))
        conn.commit()

    return jsonify({"message": "Book returned"}), 200

@app.route("/daily-report")
def daily_report():
    date = request.args.get("date")
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT s.first_name, s.last_name, s.class, b.title, t.checkout_date
            FROM transactions t
            JOIN students s ON t.student_id = s.id
            JOIN books b ON t.book_id = b.id
            WHERE DATE(t.checkout_date) = %s
        ''', (date,))
        rows = c.fetchall()
    return jsonify(rows)



@app.route("/student/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
    return jsonify({"message": "Student deleted"})

@app.route("/book/<string:barcode>", methods=["DELETE"])
def delete_book(barcode):
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM books WHERE barcode = %s", (barcode,))
        conn.commit()
    return jsonify({"message": "Book deleted"})

@app.route("/student/<int:student_id>", methods=["PUT"])
def edit_student(student_id):
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("UPDATE students SET first_name = %s, last_name = %s, class = %s WHERE id = %s",
                  (data["first_name"], data["last_name"], data["class"], student_id))
        conn.commit()
    return jsonify({"message": "Student updated"})

@app.route("/book/<string:barcode>", methods=["PUT"])
def edit_book(barcode):
    data = request.json
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("UPDATE books SET title = %s WHERE barcode = %s",
                  (data["title"], barcode))
        conn.commit()
    return jsonify({"message": "Book updated"})

@app.route("/students/upsert", methods=["POST"])
def upsert_students():
    data = request.json  # List of students
    inserted = 0
    updated = 0
    skipped = 0

    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        for s in data:
            try:
                student_id = s.get("id")
                if student_id:
                    # Insert with ID, or update if ID already exists
                    c.execute("""
                        INSERT INTO students (id, first_name, last_name, class)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id)
                        DO UPDATE SET first_name = EXCLUDED.first_name,
                                      last_name = EXCLUDED.last_name,
                                      class = EXCLUDED.class
                    """, (student_id, s["first_name"], s["last_name"], s["class"]))
                    updated += 1
                else:
                    c.execute("INSERT INTO students (first_name, last_name, class) VALUES (%s, %s, %s)",
                              (s["first_name"], s["last_name"], s["class"]))
                    inserted += 1
            except Exception as e:
                print("❌ Failed to upsert student:", s, "Error:", e)
                skipped += 1
        conn.commit()

    return jsonify({
        "message": "Upsert complete for students",
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped
    }), 200


@app.route("/books/upsert", methods=["POST"])
def upsert_books():
    data = request.json  # List of books
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        for b in data:
            c.execute("INSERT INTO books (title, barcode) VALUES (%s, %s) "
                      "ON CONFLICT (barcode) DO UPDATE SET title = EXCLUDED.title",
                      (b["title"], str(b["barcode"])))
        conn.commit()
    return jsonify({"message": "Upsert complete for books"})


@app.route("/books", methods=["GET"])
def get_books():
    with psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, barcode FROM books")
        rows = c.fetchall()
    return jsonify(rows)


# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
