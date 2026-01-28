"""
SNF Patient Navigator Case Collection App - Home Page

This Streamlit application collects historical SNF patient navigator cases
through a conversational intake process.
"""

import streamlit as st
from db import init_db

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
        visibility: hidden;
    }
    [data-testid="stSidebarNav"] li:first-child a span::before {
        content: "Dashboard";
        visibility: visible;
    }
</style>
""", unsafe_allow_html=True)

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
   - Enter your **full name** (case sensitive - use the same name each time)
   - Fill in patient demographics (age, gender, race, SNF state)
   - Answer narrative questions about the case in past tense
   - All questions refer to cases that have already concluded

3. **Review Your Cases**:
   - Use the **Case Viewer** to search and review your saved cases
   - Enter your full name to see your cases numbered in order (Case 1, Case 2, etc.)

### Important Notes

- All cases are recorded with a fixed start date of **January 1, 2025**
- Please answer all questions in **past tense** (cases have already occurred)
- Demographic fields are required; narrative fields capture the story of each case
- Your cases are automatically numbered in the order you enter them
- **Use your full name consistently** — names are case sensitive
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
    ⚠️ **Use your full name consistently!**

    Names are case sensitive. Use the exact same name each time to view all your cases together.
    """)

# Footer
st.markdown("---")
st.caption("SNF Patient Navigator Case Collection System | Data stored securely")
