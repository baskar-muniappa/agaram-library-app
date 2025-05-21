import streamlit as st
import pandas as pd
import requests
from datetime import date
import os

# ---------- Config ----------
API_BASE = "https://agaram-library-app.onrender.com"
st.set_page_config(page_title="Agaram Library", layout="centered")

# ---------- Templates ----------
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

# ---------- Users ----------
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

# ---------- Session ----------
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

# ---------- API Utilities ----------
def get_students():
    return requests.get(f"{API_BASE}/students").json()

def get_loans(sid):
    return requests.get(f"{API_BASE}/student-loans/{sid}").json()

def get_books():
    return requests.get(f"{API_BASE}/books").json()

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
    student_names = [f"{s['first_name']} {s['last_name']}" for s in filtered_students]
    selected_student = st.selectbox("மாணவர் (Student)", student_names)

    student_lookup = {f"{s['first_name']} {s['last_name']}": s["id"] for s in filtered_students}
    student_id = student_lookup.get(selected_student)
    if not student_id:
        st.warning("⚠️ Please select a valid student.")
        st.stop()

    barcode = st.text_input("📷 பார்கோடு (Barcode)")

    if st.button("📤 வெளியீடு"):
        resp = requests.post(f"{API_BASE}/checkout", json={"student_id": student_id, "barcode": barcode})
        st.success("வெளியீடு செய்யப்பட்டது") if resp.ok else st.error(resp.json().get("error", "Error"))

    if st.button("📥 மீட்பு"):
        resp = requests.post(f"{API_BASE}/return", json={"barcode": barcode})
        st.success("மீட்பு செய்யப்பட்டது") if resp.ok else st.error(resp.json().get("error", "Error"))

    if student_id:
        try:
            loans = get_loans(student_id)
        except Exception as e:
            st.error(f"Failed to load loans: {e}")
            st.stop()
        if loans:
            st.markdown(f"**📚 {loans[0]['title']}** — 📅 {loans[0]['checkout_date'][:10]}")
        else:
            st.info("தற்போது எடுக்கப்பட்ட புத்தகங்கள் இல்லை.")

# (Other pages omitted for brevity — assumed unchanged from prior working version)