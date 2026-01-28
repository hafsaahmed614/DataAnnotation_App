"""
SNF Patient Navigator Case Collection App - Home Page

This Streamlit application collects historical SNF patient navigator cases
through a conversational intake process.
"""

import streamlit as st
from db import init_db

# Page configuration
st.set_page_config(
    page_title="SNF Patient Navigator Case Collection",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database is initialized
init_db()

# Title and Header
st.title("🏥 SNF Patient Navigator Case Collection")
st.markdown("---")

# Instructions Section
st.header("Welcome")
st.markdown("""
This application is designed to collect historical SNF (Skilled Nursing Facility) 
patient navigator cases through a structured, conversational intake process.

### How to Use This App

1. **Choose an Intake Form** from the sidebar:
   - **Abbreviated Intake**: A shorter form capturing essential case information
   - **Full Intake**: A comprehensive form with detailed questions about the entire patient journey

2. **Complete the Intake**:
   - Enter your **ID number** (you'll need this to view your cases later)
   - Fill in patient demographics (age, gender, race, SNF state)
   - Answer narrative questions about the case in past tense
   - All questions refer to cases that have already concluded

3. **Review Your Cases**:
   - Use the **Case Viewer** to search and review your saved cases
   - Enter your ID number to see only your cases

### Important Notes

- All cases are recorded with a fixed start date of **January 1, 2025**
- Please answer all questions in **past tense** (cases have already occurred)
- Demographic fields are required; narrative fields capture the story of each case
- Case IDs are generated automatically upon saving
- **Remember your ID number** — you'll need it to view your cases later
""")

st.markdown("---")

# Quick start section
st.header("🚀 Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📝 Abbreviated Intake")
    st.markdown("Quick form with essential questions for faster data entry.")
    st.page_link("pages/1_Abbreviated_Intake.py", label="Start Abbreviated Intake", icon="📝")

with col2:
    st.markdown("### 📋 Full Intake")
    st.markdown("Comprehensive form capturing the complete patient journey.")
    st.page_link("pages/2_Full_Intake.py", label="Start Full Intake", icon="📋")

with col3:
    st.markdown("### 🔍 Case Viewer")
    st.markdown("View and export your previously saved cases.")
    st.page_link("pages/3_Case_Viewer.py", label="View Cases", icon="🔍")

# Sidebar information
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("""
    - **Home**: Overview and instructions
    - **Abbreviated Intake**: Quick case entry
    - **Full Intake**: Comprehensive case entry  
    - **Case Viewer**: View your cases
    """)
    
    st.markdown("---")
    st.markdown("### Remember")
    st.markdown("""
    ⚠️ **Keep track of your ID number!**
    
    You'll need it to view your cases later in the Case Viewer.
    """)

# Footer
st.markdown("---")
st.caption("SNF Patient Navigator Case Collection System | Data stored securely")
