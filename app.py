"""
SNF Patient Navigator Case Collection App - Home Page

This Streamlit application collects historical SNF patient navigator cases
through a conversational intake process.
"""

import streamlit as st
from db import init_db
from auth import init_session_state, show_login_form, is_authenticated, get_current_username, logout

# Page configuration
st.set_page_config(
    page_title="Dashboard | SNF Navigator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to rename "app" to "Dashboard" in sidebar
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child a span {
        color: transparent;
    }
    [data-testid="stSidebarNav"] li:first-child a span::before {
        content: "Dashboard";
        color: rgb(250, 250, 250);
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
init_db()

# Initialize auth session state
init_session_state()

# Title and Header
st.title("🏥 SNF Patient Navigator Case Collection")
st.markdown("---")

# Show login status and form
col_welcome, col_auth = st.columns([2, 1])

with col_welcome:
    if is_authenticated():
        st.success(f"Welcome back, **{get_current_username()}**!")
    else:
        st.info("Please **log in** or **create an account** to start entering cases.")

with col_auth:
    if is_authenticated():
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

# Show login form if not authenticated
if not is_authenticated():
    st.markdown("---")
    show_login_form()
    st.markdown("---")

# Instructions Section
st.header("Welcome")
st.markdown("""
This application is designed to collect historical SNF (Skilled Nursing Facility)
patient navigator cases through a structured, conversational intake process.

### How to Use This App

1. **Log in or Create Account**:
   - Enter your **full name** as your username
   - Create a **4-digit PIN** as your password
   - You'll need these to access your cases later

2. **Choose an Intake Form** from the sidebar:
   - **Abbreviated Intake**: A shorter form capturing essential case information
   - **Full Intake**: A comprehensive form with detailed questions about the entire patient journey

3. **Complete the Intake**:
   - Fill in patient demographics (age, gender, race, SNF state)
   - Answer narrative questions by **typing** or **recording audio**
   - Audio recordings are automatically transcribed
   - You can edit transcriptions before saving

4. **Review Your Cases**:
   - Use the **Case Viewer** to search and review your saved cases
   - View all versions of your transcripts
   - Download cases as JSON for offline review

### Important Notes

- All cases are recorded with a fixed start date of **January 1, 2025**
- Please answer all questions in **past tense** (cases have already occurred)
- Demographic fields are required; narrative fields capture the story of each case
- Your cases are automatically numbered in the order you enter them
- Audio recordings and transcripts are saved with version history
""")

st.markdown("---")

# Quick start section (only show if authenticated)
st.header("🚀 Quick Start")

if is_authenticated():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📝 Abbreviated Intake")
        st.markdown("Quick form with essential questions. Supports audio recording.")
        st.page_link("pages/1_Abbreviated_Intake.py", label="Start Abbreviated Intake", icon="📝")

    with col2:
        st.markdown("### 📋 Full Intake")
        st.markdown("Comprehensive form with audio transcription support.")
        st.page_link("pages/2_Full_Intake.py", label="Start Full Intake", icon="📋")

    with col3:
        st.markdown("### 🔍 Case Viewer")
        st.markdown("View cases, transcripts, and version history.")
        st.page_link("pages/3_Case_Viewer.py", label="View Cases", icon="🔍")
else:
    st.warning("Please log in above to access the intake forms and case viewer.")

# Sidebar information
with st.sidebar:
    st.markdown("### Account")
    if is_authenticated():
        st.success(f"Logged in as: **{get_current_username()}**")
        if st.button("Logout", key="sidebar_logout", use_container_width=True):
            logout()
            st.rerun()
    else:
        st.info("Not logged in")

    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("""
    - **Dashboard**: Overview and login
    - **Abbreviated Intake**: Quick case entry
    - **Full Intake**: Comprehensive case entry
    - **Case Viewer**: View your cases
    """)

    st.markdown("---")
    st.markdown("### Features")
    st.markdown("""
    - **Audio Recording**: Record answers instead of typing
    - **Auto-Transcription**: Whisper AI transcribes your recordings
    - **Version History**: All edits are saved
    - **Secure Access**: PIN-protected accounts
    """)

# Footer
st.markdown("---")
st.caption("SNF Patient Navigator Case Collection System | Data stored securely")
