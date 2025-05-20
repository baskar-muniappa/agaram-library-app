
import pandas as pd
import requests

API = "https://agaram-library-app.onrender.com"

# --------- Load Book Data ---------
try:
    books_df = pd.read_excel("Master-Books.xlsx")
    books = books_df[["Title", "Bar Code"]].dropna()
    books.rename(columns={"Title": "title", "Bar Code": "barcode"}, inplace=True)
    books["barcode"] = books["barcode"].astype(str)
    book_payload = books.to_dict(orient="records")

    r1 = requests.post(f"{API}/books/upsert", json=book_payload)
    print(f"✅ Books upsert: {r1.status_code} - {len(book_payload)} records sent")
    print("Response:", r1.json())
except Exception as e:
    print("❌ Error during book upsert:", e)

# --------- Load Student Data ---------
try:
    students_file = pd.ExcelFile("Students.xlsx")
    students = []

    for sheet in students_file.sheet_names:
        if sheet.lower() == "classroom":
            continue
        df = students_file.parse(sheet)
        for _, row in df.iterrows():
            first = str(row.get("Student First Name (In English)", "")).strip()
            last = str(row.get("Student Last Name (In English)", "")).strip()
            sid = row.get("ID")
            if not first and not last:
                continue
            student = {
                "first_name": first or last,
                "last_name": last or first,
                "class": sheet.strip()
            }
            if not pd.isna(sid):
                student["id"] = int(sid)
            students.append(student)

    r2 = requests.post(f"{API}/students/upsert", json=students)
    print(f"✅ Students upsert: {r2.status_code} - {len(students)} records sent")
    print("Response:", r2.json())
except Exception as e:
    print("❌ Error during student upsert:", e)
