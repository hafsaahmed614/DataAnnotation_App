"""
SNF Patient Navigator Case Collection - Case Viewer Page

Search and view saved cases. Regular users can only view their own cases.
Admin users can view all cases with the admin password.
"""

import streamlit as st
import json
from db import get_case_by_id, get_cases_by_user_id, get_recent_cases, init_db

# Page configuration
st.set_page_config(
    page_title="Case Viewer | SNF Navigator",
    page_icon="🔍",
    layout="wide"
)

# Ensure database is initialized
init_db()

# Get admin password from secrets (if configured)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", None)

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


def display_case(case):
    """Display a single case with all its details."""
    
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


# Title
st.title("🔍 Case Viewer")
st.markdown("View saved cases by entering your ID number or admin password.")
st.markdown("---")

# Access mode selection
access_mode = st.radio(
    "Select access mode:",
    ["View My Cases (User ID)", "View All Cases (Admin)"],
    horizontal=True
)

if access_mode == "View My Cases (User ID)":
    # User mode - show only their cases
    st.markdown("### Enter Your ID Number")
    
    user_id_input = st.text_input(
        "Your ID Number",
        placeholder="Enter the ID number you used when creating cases...",
        help="Enter the same ID number you used when submitting cases"
    )
    
    if st.button("🔍 View My Cases", use_container_width=True, type="primary"):
        if user_id_input and user_id_input.strip():
            user_cases = get_cases_by_user_id(user_id_input.strip())
            
            if user_cases:
                st.success(f"Found {len(user_cases)} case(s) for ID: {user_id_input}")
                st.markdown("---")
                
                # Let user select which case to view
                case_options = {
                    f"{c.case_id[:8]}... ({c.created_at.strftime('%Y-%m-%d %H:%M')}) - {c.intake_version.title()}": c.case_id 
                    for c in user_cases
                }
                
                selected_case_label = st.selectbox(
                    "Select a case to view:",
                    options=list(case_options.keys())
                )
                
                if selected_case_label:
                    selected_case_id = case_options[selected_case_label]
                    selected_case = get_case_by_id(selected_case_id)
                    
                    if selected_case:
                        st.markdown("---")
                        display_case(selected_case)
            else:
                st.warning(f"No cases found for ID: {user_id_input}")
                st.info("Make sure you're using the same ID number you entered when creating cases.")
        else:
            st.error("Please enter your ID number.")

else:
    # Admin mode - show all cases
    st.markdown("### Admin Access")
    
    if ADMIN_PASSWORD is None:
        st.error("⚠️ Admin password not configured. Please add ADMIN_PASSWORD to Streamlit secrets.")
    else:
        admin_password_input = st.text_input(
            "Admin Password",
            type="password",
            placeholder="Enter admin password...",
            help="Contact the administrator for access"
        )
        
        if st.button("🔓 Access All Cases", use_container_width=True, type="primary"):
            if admin_password_input == ADMIN_PASSWORD:
                st.success("✅ Admin access granted!")
                st.markdown("---")
                
                # Get all recent cases
                all_cases = get_recent_cases(limit=100)
                
                if all_cases:
                    st.markdown(f"### All Cases ({len(all_cases)} total)")
                    
                    # Let admin select which case to view
                    case_options = {
                        f"{c.case_id[:8]}... | User: {c.user_id} | {c.created_at.strftime('%Y-%m-%d %H:%M')} | {c.intake_version.title()}": c.case_id 
                        for c in all_cases
                    }
                    
                    selected_case_label = st.selectbox(
                        "Select a case to view:",
                        options=list(case_options.keys())
                    )
                    
                    if selected_case_label:
                        selected_case_id = case_options[selected_case_label]
                        selected_case = get_case_by_id(selected_case_id)
                        
                        if selected_case:
                            st.markdown("---")
                            st.markdown(f"**Created by User ID:** `{selected_case.user_id}`")
                            display_case(selected_case)
                else:
                    st.info("No cases have been recorded yet.")
            else:
                st.error("❌ Incorrect admin password.")

# Sidebar info
with st.sidebar:
    st.markdown("### Case Viewer")
    st.markdown("""
    **User Mode:**
    - Enter your ID number
    - View only cases you created
    
    **Admin Mode:**
    - Enter admin password
    - View all cases from all users
    """)
    
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Use the same ID you entered when creating cases
    - Download cases as JSON for offline review
    - Contact admin for full access
    """)
