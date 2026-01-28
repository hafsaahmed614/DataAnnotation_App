"""
SNF Patient Navigator Case Collection - Case Viewer Page

Search and view saved cases by Case ID. Displays demographics, metadata,
and renders narrative responses in readable sections.
"""

import streamlit as st
import json
from db import get_case_by_id, get_all_case_ids, init_db

# Page configuration
st.set_page_config(
    page_title="Case Viewer | SNF Navigator",
    page_icon="🔍",
    layout="wide"
)

# Ensure database is initialized
init_db()

# Question labels for display (combined from both forms)
QUESTION_LABELS = {
    # Abbreviated intake questions
    "aq1": "Case Summary",
    "aq2": "SNF Team Discharge Timing",
    "aq3": "Requirements for Safe Discharge",
    "aq4": "Estimated Discharge Date",
    "aq5": "Alignment Across Stakeholders",
    "aq6": "SNF Discharge Conditions",
    "aq7": "HHA Involvement",
    "aq8": "Information Shared with HHA",
    
    # Full intake questions
    "q6": "Case Summary",
    "q7": "Referral Source and Expectation",
    "q8": "Upstream Path to SNF",
    "q9": "Expected Length of Stay at Admission",
    "q10": "Initial Assessment",
    "q11": "Early Home Feasibility",
    "q12": "Key SNF Roles and People",
    "q13": "Patient Response",
    "q14": "Patient/Family Goals",
    "q15": "SNF Discharge Timing Over Time",
    "q16": "Requirements for Safe Discharge",
    "q17": "Services Discussion and Agreement",
    "q18": "HHA Involvement and Handoff",
    "q19": "Information Shared with HHA",
    "q20": "Estimated Discharge Date and Reasoning",
    "q21": "Alignment Across Stakeholders",
    "q22": "SNF Discharge Conditions",
    "q23": "Plan for First 24-48 Hours",
    "q25": "Transition SNF to Home Overall",
    "q26": "Handoff Completion and Gaps",
    "q27": "24-Hour Follow-up Contact",
    "q28": "Initial At-Home Status"
}

# Section groupings for full intake
FULL_SECTIONS = {
    "Case Overview": ["q6", "q7"],
    "Admission & Assessment": ["q8", "q9", "q10"],
    "Care Planning": ["q11", "q12", "q13", "q14"],
    "Discharge Planning": ["q15", "q16", "q17", "q20", "q21", "q22"],
    "HHA Coordination": ["q18", "q19"],
    "Transition Home": ["q23", "q25", "q26"],
    "Follow-up": ["q27", "q28"]
}

# Section groupings for abbreviated intake
ABBREV_SECTIONS = {
    "Case Overview": ["aq1"],
    "Discharge Planning": ["aq2", "aq3", "aq4", "aq5", "aq6"],
    "HHA Coordination": ["aq7", "aq8"]
}

# Title
st.title("🔍 Case Viewer")
st.markdown("Search for a case by its Case ID to view full details including narratives.")
st.markdown("---")

# Get all case IDs for autocomplete/validation
all_case_ids = get_all_case_ids()

# Search input
col1, col2 = st.columns([3, 1])

with col1:
    case_id_input = st.text_input(
        "Enter Case ID",
        placeholder="e.g., a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        help="Enter the full UUID case ID"
    )

with col2:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

# Show recent case IDs as reference
if all_case_ids:
    with st.expander("📋 Recent Case IDs (click to expand)"):
        st.markdown("Click on a Case ID to copy it:")
        for cid in all_case_ids[:10]:
            st.code(cid, language=None)

# Process search
if case_id_input and search_clicked:
    case = get_case_by_id(case_id_input.strip())
    
    if case:
        st.markdown("---")
        st.success(f"✅ Case found!")
        
        # Case metadata header
        st.header(f"Case: {case.case_id[:8]}...")
        
        # Metadata columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Intake Type", "Abbreviated" if case.intake_version == "abbrev" else "Full")
        
        with col2:
            st.metric("Created", case.created_at.strftime("%Y-%m-%d %H:%M") if case.created_at else "N/A")
        
        with col3:
            st.metric("Case Start Date", case.case_start_date.strftime("%Y-%m-%d") if case.case_start_date else "N/A")
        
        with col4:
            st.metric("SNF Days", case.snf_days if case.snf_days else "—")
        
        st.markdown("---")
        
        # Demographics section
        st.subheader("👤 Demographics")
        
        demo_col1, demo_col2, demo_col3, demo_col4 = st.columns(4)
        
        with demo_col1:
            st.markdown(f"**Age at SNF Stay**")
            st.markdown(f"{case.age_at_snf_stay} years")
        
        with demo_col2:
            st.markdown(f"**Gender**")
            st.markdown(f"{case.gender}")
        
        with demo_col3:
            st.markdown(f"**Race**")
            st.markdown(f"{case.race}")
        
        with demo_col4:
            st.markdown(f"**SNF State**")
            st.markdown(f"{case.state}")
        
        st.markdown("---")
        
        # Services section
        st.subheader("🏥 Services")
        
        svc_col1, svc_col2 = st.columns(2)
        
        with svc_col1:
            st.markdown("**Services Discussed**")
            if case.services_discussed:
                st.markdown(case.services_discussed)
            else:
                st.markdown("*Not recorded*")
        
        with svc_col2:
            st.markdown("**Services Accepted**")
            if case.services_accepted:
                st.markdown(case.services_accepted)
            else:
                st.markdown("*Not recorded*")
        
        st.markdown("---")
        
        # Narrative responses section
        st.subheader("📝 Narrative Responses")
        
        # Parse answers JSON
        try:
            answers = json.loads(case.answers_json) if case.answers_json else {}
        except json.JSONDecodeError:
            answers = {}
        
        if answers:
            # Determine which sections to use based on intake type
            sections = ABBREV_SECTIONS if case.intake_version == "abbrev" else FULL_SECTIONS
            
            # Render by section
            for section_name, question_ids in sections.items():
                # Check if any questions in this section have answers
                section_has_content = any(
                    qid in answers and answers[qid].strip() 
                    for qid in question_ids
                )
                
                if section_has_content:
                    st.markdown(f"### 📌 {section_name}")
                    
                    for qid in question_ids:
                        if qid in answers and answers[qid].strip():
                            label = QUESTION_LABELS.get(qid, qid)
                            st.markdown(f"**{label}** *(ID: {qid})*")
                            
                            # Display answer in a nice box
                            st.info(answers[qid])
                    
                    st.markdown("")
            
            # Check for any answers that don't fit in sections
            section_qids = set()
            for qids in sections.values():
                section_qids.update(qids)
            
            other_answers = {k: v for k, v in answers.items() if k not in section_qids and v.strip()}
            
            if other_answers:
                st.markdown("### 📌 Other Responses")
                for qid, answer in other_answers.items():
                    label = QUESTION_LABELS.get(qid, qid)
                    st.markdown(f"**{label}** *(ID: {qid})*")
                    st.info(answer)
        else:
            st.info("No narrative responses recorded for this case.")
        
        st.markdown("---")
        
        # Export section
        st.subheader("📥 Export")
        
        # Prepare export data
        export_data = case.to_dict()
        export_json = json.dumps(export_data, indent=2, default=str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download Case JSON",
                data=export_json,
                file_name=f"case_{case.case_id}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            with st.expander("👁️ View Raw JSON"):
                st.json(export_data)
        
        # Full Case ID for reference
        st.markdown("---")
        st.markdown("**Full Case ID:**")
        st.code(case.case_id, language=None)
        
    else:
        st.error(f"❌ No case found with ID: {case_id_input}")
        st.info("Please check the Case ID and try again. Case IDs are UUIDs in the format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

elif search_clicked and not case_id_input:
    st.warning("⚠️ Please enter a Case ID to search.")

# Sidebar info
with st.sidebar:
    st.markdown("### Case Viewer")
    st.markdown("""
    Use this page to:
    - Search for cases by ID
    - View full case details
    - Review narrative responses
    - Export case data as JSON
    """)
    
    st.markdown("---")
    st.markdown("### Statistics")
    st.metric("Total Cases", len(all_case_ids))
    
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Case IDs are UUIDs (36 characters)
    - Copy Case ID from intake confirmation
    - Recent cases are listed above
    - Download JSON for offline review
    """)
