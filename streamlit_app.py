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
        username = st.text_input("பயனர் பெயர் (Username)")
        password = st.text_input("கடவுச்சொல் (Password)", type="password")
        submitted = st.form_submit_button("உள்நுழைக (Login)")
        if submitted:
            if username not in USERS:
                st.error("❌ Invalid username. Please try again.")
            elif USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ தவறான கடவுச்சொல்")
    st.stop()

# ---------- Sidebar ----------
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username}**")
menu = st.sidebar.radio("பக்கத் தேர்வுகள்", ["📚 Library", "⚙️ Admin", "📋 Lending Summary"], index=0)
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ---------- Utility ----------
def get_students():
    return requests.get(f"{API_BASE}/students").json()

def get_loans(sid):
    return requests.get(f"{API_BASE}/student-loans/{sid}").json()

# ---------- Library ----------
if menu == "📚 Library":
    st.title("அகரம் தமிழ்ப்பள்ளி - நூலகச் செயலி")
    try:
        students = get_students()
    except Exception as e:
        st.error(f"⚠️ Failed to load students: {e}")
        st.stop()
    if not students:
        st.warning("📭 மாணவர் பட்டியல் காலியாக உள்ளது.")
        st.stop()

    classes = sorted(set(s["class"] for s in students if s["class"]))
    selected_class = st.selectbox("வகுப்பு (Classroom)", classes)

    filtered_students = [s for s in students if s["class"] == selected_class]
    student_lookup = {f"{s['first_name']} {s['last_name']}": s["id"] for s in filtered_students}
    selected_student = st.selectbox("மாணவர் (Student)", list(student_lookup.keys()))
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
    try:
        student_file = st.file_uploader("📤 Upload Students", type=["xlsx"], key="stu_up")
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
            st.success("✅ மாணவர் பதிவுகள் செய்யப்பட்டது") if res.ok else st.error("❌ பிழை ஏற்பட்டது")
            st.download_button("📥 Download Student Template", open("student_upload_template_upsert.xlsx", "rb").read(), file_name="student_template.xlsx")

        book_file = st.file_uploader("📤 Upload Books", type=["xlsx"], key="book_up")
        if book_file:
            df = pd.read_excel(book_file)
            books = [{"title": r.get("Title", ""), "barcode": str(r.get("Barcode", ""))} for _, r in df.iterrows()]
            res = requests.post(f"{API_BASE}/books/upsert", json=books)
            st.success("✅ புத்தகங்கள் பதிவேற்றம் செய்யப்பட்டது") if res.ok else st.error("❌ பிழை ஏற்பட்டது")
            st.download_button("📥 Download Book Template", open("book_upload_template_upsert.xlsx", "rb").read(), file_name="book_template.xlsx")
    except Exception as e:
        st.error(f"⚠️ Admin section error: {e}")

# ---------- Lending Summary ----------
elif menu == "📋 Lending Summary":
    st.title("📋 Book Lending Summary")
    try:
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
    except Exception as e:
        st.error(f"⚠️ Lending summary error: {e}")