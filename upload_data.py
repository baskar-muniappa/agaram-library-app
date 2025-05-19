import pandas as pd
import requests

API = "https://agaram-library-app.onrender.com"

# --------- Load Book Data ---------
books_df = pd.read_excel("Master-Books.xlsx")
books = books_df[["Title", "Bar Code"]].dropna()
books.rename(columns={"Title": "title", "Bar Code": "barcode"}, inplace=True)

# Convert barcode to string
books["barcode"] = books["barcode"].astype(str)

book_payload = books.to_dict(orient="records")
r1 = requests.post(f"{API}/books", json=book_payload)
print("Books upload:", r1.status_code, r1.json())

# --------- Load Student Data ---------
students_file = pd.ExcelFile("Students.xlsx")
students = []

for sheet in students_file.sheet_names:
    if sheet.lower() == "classroom":
        continue
    df = students_file.parse(sheet)
    for _, row in df.iterrows():
        first = str(row.get("First Name", "")).strip()
        last = str(row.get("Last Name", "")).strip()
        if not first and not last:
            continue
        students.append({
            "first_name": first or last,
            "last_name": last or first,
            "class": sheet.strip()
        })

r2 = requests.post(f"{API}/students", json=students)
print("Students upload:", r2.status_code, r2.json())
