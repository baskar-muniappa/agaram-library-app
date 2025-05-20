
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

# You can now paste the rest of your previous app (unchanged sections),
# and where you had:
# selected_student = student_map[selected_student_key]
# Replace with:
# selected_student = student_map.get(selected_student_key)
# if not selected_student:
#     st.warning("⚠️ Please select a valid student.")
#     st.stop()

# Same for book_map access