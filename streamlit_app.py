import streamlit as st
import pandas as pd
import requests
from datetime import date

import os

# Auto-generate templates if missing
if not os.path.exists("student_upload_template_upsert.xlsx"):
    pd.DataFrame({
        "ID": [""],
        "First Name": ["Dhruvan"],
        "Last Name": ["Baskar"],
        "Class": ["1-A"]
    }).to_excel("student_upload_template_upsert.xlsx", index=False)

if not os.path.exists("book_upload_template_upsert.xlsx"):
    pd.DataFrame({
        "Title": ["Ponniyin Selvan"],
        "Barcode": ["BK002"]
    }).to_excel("book_upload_template_upsert.xlsx", index=False)

API_BASE = "https://agaram-library-app.onrender.com"
st.set_page_config(page_title="Agaram Library", layout="centered")

# ---------- Login ----------
USERS = {
    "Baskar": "serendipity",
    "Palani": "Palani123",
    "Nirmal": "Nirmal123",
    "Mukesh": "Raja",
    "Roopa": "Dancer",
    "Hemalatha": "Hema123",
    "Krithiga": "Krithiga123",
    "Meghalai": "Agaram",
    "Ezhil": "Agaram"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔐 நூலகச் செயலிக்கு உள்நுழைவு (Login)")
    with st.form("login_form", clear_on_submit=True):
        username = st.selectbox("பயனரைத் தேர்ந்தெடுக்கவும் (Select User)", list(USERS.keys()))
        password = st.text_input("கடவுச்சொல் (Password)", type="password")
        submitted = st.form_submit_button("உள்நுழைக (Login)")
        if submitted:
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("தவறான கடவுச்சொல்")
    st.stop()

# ---------- Sidebar ----------
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username}**")
menu = st.sidebar.radio("பக்கத் தேர்வுகள்", ["📚 Library", "⚙️ Admin", "📋 Lending Summary"])

# ---------- Utility ----------
def get_students():
    return requests.get(f"{API_BASE}/students").json()

def get_loans(sid):
    return requests.get(f"{API_BASE}/student-loans/{sid}").json()

# ---------- Library ----------
if menu == "📚 Library":
    st.title("அகரம் தமிழ்ப்பள்ளி - நூலகச் செயலி")
    students = get_students()
    classes = sorted(set(s["class"] for s in students if s["class"]))

    class_col, student_col = st.columns(2)
    with class_col:
        selected_class = st.selectbox("வகுப்பு (Classroom)", classes)
    with student_col:
        filtered_students = [s for s in students if s["class"] == selected_class]
        selected_student = st.selectbox("மாணவர் (Student)", [f"{s['first_name']} {s['last_name']}" for s in filtered_students])

    student_lookup = {f"{s['first_name']} {s['last_name']}": s["id"] for s in filtered_students}
    student_id = student_lookup.get(selected_student)
    barcode = st.text_input("📷 பார்கோடு (Barcode)")

    if st.button("📤 வெளியீடு"):
        resp = requests.post(f"{API_BASE}/checkout", json={"student_id": student_id, "barcode": barcode})
        st.success("வெளியீடு செய்யப்பட்டது") if resp.ok else st.error(resp.json().get("error", "Error"))

    if st.button("📥 மீட்பு"):
        resp = requests.post(f"{API_BASE}/return", json={"barcode": barcode})
        st.success("மீட்பு செய்யப்பட்டது") if resp.ok else st.error(resp.json().get("error", "Error"))

    if student_id:
        loans = get_loans(student_id)
        if loans:
            st.markdown(f"**📚 {loans[0]['title']}** — 📅 {loans[0]['checkout_date'][:10]}")
        else:
            st.info("தற்போது எடுக்கப்பட்ட புத்தகங்கள் இல்லை.")

# ---------- Admin ----------
elif menu == "⚙️ Admin":
    st.title("⚙️ நிர்வாகக் கட்டுப்பாடு")

    # Upload Students (Upsert)
    st.subheader("📤 Upload or Update Students")
    student_file = st.file_uploader("Upload Student Excel File", type=["xlsx"], key="stu_up")
    if student_file:
        df = pd.read_excel(student_file)
        students = []
        for _, r in df.iterrows():
            student = {
                "first_name": r.get("First Name", ""),
                "last_name": r.get("Last Name", ""),
                "class": r.get("Class", "")
            }
            if not pd.isna(r.get("ID")):
                student["id"] = int(r["ID"])
            students.append(student)
        res = requests.post(f"{API_BASE}/students/upsert", json=students)
        st.success("மாணவர் தகவல்கள் புதுப்பிக்கப்பட்டன") if res.ok else st.error("பிழை ஏற்பட்டது")

    st.download_button("📥 Download Student Template",
                       open("student_upload_template_upsert.xlsx", "rb").read(),
                       file_name="student_upload_template_upsert.xlsx")

    # Upload Books (Upsert)
    st.subheader("📤 Upload or Update Books")
    book_file = st.file_uploader("Upload Book Excel File", type=["xlsx"], key="book_up")
    if book_file:
        df = pd.read_excel(book_file)
        books = [{"title": r.get("Title", ""), "barcode": str(r.get("Barcode", ""))}
                 for _, r in df.iterrows()]
        res = requests.post(f"{API_BASE}/books/upsert", json=books)
        st.success("புத்தகங்கள் புதுப்பிக்கப்பட்டன") if res.ok else st.error("பிழை ஏற்பட்டது")

    st.download_button("📥 Download Book Template",
                       open("book_upload_template_upsert.xlsx", "rb").read(),
                       file_name="book_upload_template_upsert.xlsx")

    # Edit/Delete Student
    st.markdown("---")
    st.subheader("🗑️ Delete or ✏️ Edit Student")
    all_students = get_students()
    student_map = {f"{s['id']} - {s['first_name']} {s['last_name']} ({s['class']})": s for s in all_students}
    selected_student_key = st.selectbox("Select Student to Edit/Delete", list(student_map.keys()))
    selected_student = student_map[selected_student_key]

    new_fname = st.text_input("First Name", value=selected_student["first_name"])
    new_lname = st.text_input("Last Name", value=selected_student["last_name"])
    new_class = st.text_input("Class", value=selected_student["class"])

    col1, col2 = st.columns(2)
    if col1.button("✏️ Update Student"):
        res = requests.put(f"{API_BASE}/student/{selected_student['id']}",
                           json={"first_name": new_fname, "last_name": new_lname, "class": new_class})
        st.success("Student updated successfully") if res.ok else st.error("Update failed")

    if col2.button("🗑️ Delete Student"):
        res = requests.delete(f"{API_BASE}/student/{selected_student['id']}")
        st.success("Student deleted") if res.ok else st.error("Delete failed")

    # Edit/Delete Book
    st.markdown("---")
    st.subheader("🗑️ Delete or ✏️ Edit Book")
    all_books = requests.get(f"{API_BASE}/books").json()
    book_map = {f"{b['barcode']} - {b['title']}": b for b in all_books}
    selected_book_key = st.selectbox("Select Book to Edit/Delete", list(book_map.keys()))
    selected_book = book_map[selected_book_key]

    new_title = st.text_input("Book Title", value=selected_book["title"])

    col3, col4 = st.columns(2)
    if col3.button("✏️ Update Book"):
        res = requests.put(f"{API_BASE}/book/{selected_book['barcode']}", json={"title": new_title})
        st.success("Book updated successfully") if res.ok else st.error("Update failed")

    if col4.button("🗑️ Delete Book"):
        res = requests.delete(f"{API_BASE}/book/{selected_book['barcode']}")
        st.success("Book deleted") if res.ok else st.error("Delete failed")

# ---------- Lending Summary ----------
elif menu == "📋 Lending Summary":
    st.title("📋 Book Lending Summary")
    students = get_students()
    all_classes = sorted(set(s["class"] for s in students))
    selected_class = st.selectbox("Select Class", all_classes)
    class_students = [s for s in students if s["class"] == selected_class]

    data = []
    for s in class_students:
        loans = get_loans(s["id"])
        data.append({
            "Student Name": f"{s['first_name']} {s['last_name']}",
            "Book Title": loans[0]["title"] if loans else "",
            "Barcode": loans[0]["barcode"] if loans else "",
            "Date": loans[0]["checkout_date"][:10] if loans else ""
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    export_option = st.selectbox("Export Option", ["Export this class only", "Export all classes"])
    if st.button("Download Excel Report"):
        if export_option == "Export this class only":
            filename = f"Lending_Summary_{selected_class}.xlsx"
            df.to_excel(filename, index=False)
            st.download_button("📥 Download", open(filename, "rb").read(), file_name=filename)
        else:
            writer = pd.ExcelWriter("Lending_Summary_All.xlsx")
            for cls in all_classes:
                sheet_data = []
                for s in [x for x in students if x["class"] == cls]:
                    loans = get_loans(s["id"])
                    sheet_data.append({
                        "Student Name": f"{s['first_name']} {s['last_name']}",
                        "Book Title": loans[0]["title"] if loans else "",
                        "Barcode": loans[0]["barcode"] if loans else "",
                        "Date": loans[0]["checkout_date"][:10] if loans else ""
                    })
                pd.DataFrame(sheet_data).to_excel(writer, index=False, sheet_name=cls[:31])
            writer.close()
            st.download_button("📥 Download All Classes", open("Lending_Summary_All.xlsx", "rb").read(),
                file_name="Lending_Summary_All.xlsx")
