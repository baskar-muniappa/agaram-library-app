import pandas as pd
import requests

# Load Excel files
books_df = pd.read_excel("Master-Books.xlsx")
students_xls = pd.ExcelFile("Students.xlsx")

# --- Prepare book data ---
books = []
for _, row in books_df.iterrows():
    books.append({
        "title": str(row["Title"]).strip(),
        "barcode": str(row["Bar Code"]).strip()
    })

# --- Prepare student data ---
students = []
for sheet in students_xls.sheet_names:
    if sheet.lower() == "classroom":
        continue
    df = students_xls.parse(sheet)
    for _, row in df.iterrows():
        first = row.get("Student First Name (In English)")
        last = row.get("Student Last Name (In English)")

        # Replace NaN with empty strings
        first = "" if pd.isna(first) else str(first).strip()
        last = "" if pd.isna(last) else str(last).strip()

        full_name = f"{first} {last}".strip()

        if not full_name:  # Skip completely blank rows
            continue

        students.append({
            "first_name": first,
            "last_name": last,
            "class": sheet
        })

# --- Upload to API ---
API = "http://localhost:5000"

# Upload students
r1 = requests.post(f"{API}/students", json=students)
print("Student Upload:", r1.status_code, r1.json())

# Upload books
r2 = requests.post(f"{API}/books", json=books)
print("Book Upload:", r2.status_code, r2.json())