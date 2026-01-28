"""
SNF Patient Navigator Case Collection App - Home Page

This Streamlit application collects historical SNF patient navigator cases
through a conversational intake process.
"""

import streamlit as st
import pandas as pd
from db import get_recent_cases, init_db

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
   - Start with patient demographics (age, gender, race, SNF state)
   - Answer narrative questions about the case in past tense
   - All questions refer to cases that have already concluded

3. **Review Cases**:
   - Use the **Case Viewer** to search and review saved cases by Case ID
   - Recent cases are displayed on this home page (demographics only)

### Important Notes

- All cases are recorded with a fixed start date of **January 1, 2025**
- Please answer all questions in **past tense** (cases have already occurred)
- Demographic fields are required; narrative fields capture the story of each case
- Case IDs are generated automatically upon saving
""")

st.markdown("---")

# Recent Cases Section
st.header("📋 Recent Cases")

# Fetch recent cases
recent_cases = get_recent_cases(limit=20)

if recent_cases:
    # Build table data (exclude narrative text for PHI protection)
    table_data = []
    for case in recent_cases:
        table_data.append({
            "Case ID": case.case_id[:8] + "...",  # Truncated for display
            "Full Case ID": case.case_id,
            "Created": case.created_at.strftime("%Y-%m-%d %H:%M") if case.created_at else "N/A",
            "Intake Type": "Abbreviated" if case.intake_version == "abbrev" else "Full",
            "Age": case.age_at_snf_stay,
            "Gender": case.gender,
            "Race": case.race,
            "State": case.state,
            "SNF Days": case.snf_days if case.snf_days else "—"
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table without Full Case ID column (for cleaner display)
    display_df = df.drop(columns=["Full Case ID"])
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.caption("💡 **Tip**: Use the Case Viewer page to see full details including narratives.")
    
else:
    st.info("No cases have been recorded yet. Use the sidebar to start an intake.")

# Sidebar information
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("""
    - **Home**: Overview and recent cases
    - **Abbreviated Intake**: Quick case entry
    - **Full Intake**: Comprehensive case entry  
    - **Case Viewer**: Search and view cases
    """)
    
    st.markdown("---")
    st.markdown("### Statistics")
    total_cases = len(get_recent_cases(limit=1000))
    st.metric("Total Cases", total_cases)
    
    if recent_cases:
        abbrev_count = sum(1 for c in recent_cases if c.intake_version == "abbrev")
        full_count = sum(1 for c in recent_cases if c.intake_version == "full")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Abbreviated", abbrev_count)
        with col2:
            st.metric("Full", full_count)

# Footer
st.markdown("---")
st.caption("SNF Patient Navigator Case Collection System | Data stored securely")
