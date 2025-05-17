import streamlit as st
import requests
import pandas as pd
from datetime import date

#API_BASE = "http://localhost:5000"
API_BASE = "https://agaram-library-app.onrender.com"

st.set_page_config(page_title="Library App", layout="wide")

# ------------------------------
# Header: Logo + Title
logo_col, title_col = st.columns([1, 6])
with logo_col:
    st.image("AGARAM_LOGO.png", width=70)
with title_col:
    st.markdown("<h1 style='margin-top: 10px;'>அகரம் தமிழ்ப்பள்ளி - நூலகச் செயலி</h1>", unsafe_allow_html=True)

# ------------------------------
# Load students
@st.cache_data(ttl=3600)
def load_students():
    resp = requests.get(f"{API_BASE}/students")
    return resp.json() if resp.status_code == 200 else []

students = load_students()

# Class and Student Selectors (side-by-side)
classes = sorted(set(s["class"] for s in students if s["class"]))

class_col, student_col = st.columns(2)
with class_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும் (Classroom)", classes)

with student_col:
    filtered_students = [s for s in students if s["class"] == selected_class]
    student_lookup = {f"{s['first_name']} {s['last_name']}": s["id"] for s in filtered_students}
    student_names = list(student_lookup.keys())
    if student_names:
        selected_student = st.selectbox("மாணவனைத் தேர்ந்தெடுக்கவும் (Student)", student_names)
        student_id = student_lookup[selected_student]
    else:
        st.warning("இந்த வகுப்பில் மாணவர்கள் இல்லை. (No students in this class.)")
        selected_student = None
        student_id = None

# ------------------------------
# Book barcode input
barcode = st.text_input("புத்தகத்தின் பட்டியலெண் அல்லது பார்கோடு உள்ளிடவும் (Enter Book Barcode)")

# Function to get and show current loans
def get_student_loans(sid):
    resp = requests.get(f"{API_BASE}/student-loans/{sid}")
    return resp.json() if resp.status_code == 200 else []

def show_student_loans(student_id):
    st.markdown("### 📚 தற்போது மாணவர் எடுத்துள்ள புத்தகம் (Current Borrowed Book)")
    loans = get_student_loans(student_id)
    if loans:
        for loan in loans:
            st.markdown(f"- **{loan['title']}** (Barcode: `{loan['barcode']}`) — 📅 {loan['checkout_date'][:10]}")
    else:
        st.info("தற்போது எடுக்கப்பட்ட புத்தகங்கள் இல்லை (No books currently borrowed).")

# Show current borrowed book
if student_id:
    show_student_loans(student_id)

# ------------------------------
col1, col2 = st.columns(2)

# Checkout
if col1.button("📤 வெளியீடு (Check Out)"):
    if barcode and student_id:
        resp = requests.post(f"{API_BASE}/checkout", json={"student_id": student_id, "barcode": barcode})
        if resp.status_code == 200:
            st.success("புத்தகம் வெளியீடு செய்யப்பட்டது! (Book checked out!)")
            show_student_loans(student_id)
        else:
            st.error(f"பிழை: {resp.json().get('error', 'தெரியாத பிழை')} (Error occurred)")
    else:
        st.warning("மாணவர் மற்றும் பட்டியலெண் தேவை. (Please select a student and enter a barcode)")

# Return
if col2.button("📥 மீட்பு (Return)"):
    if barcode:
        resp = requests.post(f"{API_BASE}/return", json={"barcode": barcode})
        if resp.status_code == 200:
            st.success("புத்தகம் மீட்கப்பட்டது! (Book returned!)")
            show_student_loans(student_id)
        else:
            st.error("மீட்பு தோல்வி (Return failed)")
    else:
        st.warning("பட்டியலெண் தேவை. (Please enter a barcode)")

# ------------------------------
st.markdown("---")
st.header("📄 நாள் அறிக்கை (Daily Report)")

export_date = st.date_input("தேதியைத் தேர்ந்தெடுக்கவும் (Select Date)", value=date.today())

if st.button("📤 எக்செல் அறிக்கையை பதிவிறக்கவும் (Download Excel Report)"):
    resp = requests.get(f"{API_BASE}/daily-report", params={"date": export_date.isoformat()})
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            filename = f"LibraryReport_{export_date.isoformat()}.xlsx"
            df.to_excel(filename, index=False)
            st.success(f"அறிக்கை பதிவிறக்கப்பட்டது: {filename}")
        else:
            st.info("அந்த தேதிக்கு பதிவுகள் இல்லை. (No records for selected date.)")
    else:
        st.error("அறிக்கையை பெற முடியவில்லை. (Failed to fetch report)")
