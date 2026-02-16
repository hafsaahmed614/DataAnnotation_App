"""
SNF Patient Navigator Case Collection - Case Viewer Page

Search and view saved cases.
Requires authentication - users can only view their own cases.
Admin users can view all cases with the admin password.
"""

import streamlit as st
import json
from datetime import timezone, timedelta
from db import (
    get_case_by_id, get_cases_by_user_name, get_all_user_names,
    get_follow_up_questions_for_case, init_db
)
from auth import require_auth, get_current_username, is_authenticated, init_session_state

# US Central timezone (CST = UTC-6, CDT = UTC-5)
# Using UTC-6 for standard time
CST = timezone(timedelta(hours=-6))

def format_time_cst(dt):
    """Convert datetime to CST and format for display."""
    if dt is None:
        return "N/A"
    # If datetime is naive (no timezone), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to CST
    dt_cst = dt.astimezone(CST)
    return dt_cst.strftime('%b %d, %Y %I:%M %p')

# Page configuration
st.set_page_config(
    page_title="Case Viewer | SNF Navigator",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS to rename "app" to "Dashboard" in sidebar
st.markdown("""
<style>
    [data-testid="stSidebarNav"] ul li:first-child span {
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        display: inline-block !important;
    }
    [data-testid="stSidebarNav"] ul li:first-child a::before {
        content: "Dashboard" !important;
        visibility: visible !important;
        font-weight: 400 !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
init_db()
init_session_state()

# Check authentication
if not require_auth():
    st.stop()

# Get admin password from secrets (if configured)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", None)

# Question labels for display (combined from all forms)
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

    # Abbreviated GENERAL intake questions (any outcome)
    "gq1": "Case Summary",
    "gq2": "SNF Team Timing",
    "gq3": "Requirements for Safe Next Step",
    "gq4": "Estimated Timing for Leaving SNF",
    "gq5": "Alignment Across Stakeholders",
    "gq6": "SNF Conditions for Transition",
    "gq7": "Outcome",
    "gq8": "Early Signs",
    "gq9": "Learning",

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

# Full question texts (prompts shown to the user during intake)
QUESTION_TEXTS = {
    # Abbreviated intake questions
    "aq1": "Please provide a brief summary of this case: Why was the patient in the SNF, and what was the intended goal for getting them home? (2-5 sentences)",
    "aq2": "How did the SNF team's view of discharge timing and readiness evolve over time? Did expectations change from admission to discharge?",
    "aq3": "What needed to happen before a safe discharge home was possible?",
    "aq4": "What was your best estimate of the discharge date before the patient actually left? What was that estimate based on?",
    "aq5": "How aligned were the SNF team, patient/family, and HHA on the discharge plan? If there was misalignment, where did it occur?",
    "aq6": "What conditions did the SNF require to be met before discharging the patient home?",
    "aq7": "Was a Home Health Agency (HHA) involved? If so, which agency, and what happened with the handoff?",
    "aq8": "What information was shared with the HHA to prepare them for the patient's care at home?",

    # Abbreviated GENERAL intake questions
    "gq1": "Please provide a brief summary of this case: Why was the patient in the SNF, and what was the intended goal for their stay? (2-5 sentences)",
    "gq2": "How did the SNF team's view of timing and readiness for the next step evolve over time? Did expectations change during the stay?",
    "gq3": "What needed to happen before a safe next step after the SNF stay was possible?",
    "gq4": "What was your best estimate of when the patient would leave the SNF? What was that estimate based on?",
    "gq5": "How aligned were the SNF team, patient/family, and any external providers on the plan? If there was misalignment, where did it occur?",
    "gq6": "What conditions did the SNF require to be met before the patient could transition to the next setting?",
    "gq7": "What was the patient's outcome after the SNF stay (for example: discharged home, stayed long-term, returned to hospital, passed away, or something else)? If the patient did not discharge home and/or did not use our services, what were the main reasons?",
    "gq8": "Earlier in the stay, what signs (if any) suggested this outcome might happen?",
    "gq9": "What did you learn from this case, and what would you do differently next time (if anything)?",

    # Full intake questions
    "q6": "Please provide a summary of this case: Why was the patient in the SNF, and what was the intended goal for getting them home?",
    "q7": "What was the referral source for this case? What expectations were set at the time of referral?",
    "q8": "What was the patient's path to the SNF? Where did they come from, and what timing details do you recall about their journey?",
    "q9": "At the time of admission, what was the expected length of stay? How was this communicated?",
    "q10": "What did the initial assessment reveal? Consider social, functional, and logistical factors that were identified.",
    "q11": "What was the early reasoning about whether going home was feasible? What factors were considered?",
    "q12": "Who were the key SNF staff members or roles involved in this patient's care and discharge planning?",
    "q13": "How did the patient respond to discussions about going home and receiving services?",
    "q14": "What were the patient's and family's goals for the first period at home after discharge?",
    "q15": "How did the SNF team's view of discharge timing and readiness evolve over time? Did expectations change from admission to discharge?",
    "q16": "What needed to happen before a safe discharge home was possible?",
    "q17": "What services were discussed with the patient and family, and which services did they agree to receive?",
    "q18": "Was a Home Health Agency (HHA) involved? If so, which agency, and what happened with the handoff process?",
    "q19": "What information was shared with the HHA to prepare them for the patient's care at home?",
    "q20": "What was your best estimate of the discharge date before the patient actually left? What was that estimate based on?",
    "q21": "How aligned were the SNF team, patient/family, and HHA on the discharge plan? If there was misalignment, describe the details.",
    "q22": "What conditions did the SNF require to be met before discharging the patient home?",
    "q23": "What was the plan for the first 24-48 hours after the patient arrived home?",
    "q25": "How would you describe the overall transition from SNF to home? What went well and what could have been improved?",
    "q26": "Were all aspects of the handoff completed as planned? Were there any gaps or missing elements?",
    "q27": "Was there contact with the patient within 24 hours of discharge? If so, what was learned from that contact?",
    "q28": "What was the patient's initial status at home, and what was identified as the next step in their care?",
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

# Section groupings for abbreviated GENERAL intake (any outcome)
ABBREV_GENERAL_SECTIONS = {
    "Case Overview": ["gq1"],
    "SNF Stay & Transition": ["gq2", "gq3", "gq4", "gq5", "gq6"],
    "Outcome & Reflection": ["gq7", "gq8", "gq9"]
}


def get_case_numbers_by_type(cases):
    """
    Get case numbers for each case, separated by intake type.
    Returns a dict mapping case_id to (intake_type_label, case_number).
    """
    abbrev_count = 0
    abbrev_gen_count = 0
    full_count = 0
    case_numbers = {}

    for case in cases:  # Already ordered by created_at ascending
        if case.intake_version == "abbrev":
            abbrev_count += 1
            case_numbers[case.case_id] = ("Abbreviated", abbrev_count)
        elif case.intake_version == "abbrev_gen":
            abbrev_gen_count += 1
            case_numbers[case.case_id] = ("Abbrev General", abbrev_gen_count)
        else:
            full_count += 1
            case_numbers[case.case_id] = ("Full", full_count)

    return case_numbers


def display_case(case, case_number=None):
    """Display a single case with all its details."""

    # Case metadata header
    if case_number:
        st.header(f"Case {case_number}")
    else:
        st.header(f"Case")

    # Metadata columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        intake_type_label = {
            "abbrev": "Abbreviated",
            "abbrev_gen": "Abbreviated General",
            "full": "Full"
        }.get(case.intake_version, case.intake_version)
        st.metric("Intake Type", intake_type_label)

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

    # SNF Name (if available)
    snf_name = getattr(case, 'snf_name', None)
    if snf_name:
        st.markdown(f"**SNF Name:** {snf_name}")

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

    # Post-discharge services utilization
    services_utilized = getattr(case, 'services_utilized_after_discharge', None)
    if services_utilized:
        st.markdown("**Services Utilized After Discharge**")
        st.markdown(services_utilized)

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
        if case.intake_version == "abbrev":
            sections = ABBREV_SECTIONS
        elif case.intake_version == "abbrev_gen":
            sections = ABBREV_GENERAL_SECTIONS
        else:
            sections = FULL_SECTIONS

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
                        question_text = QUESTION_TEXTS.get(qid, "")
                        st.markdown(f"**{label}** *(ID: {qid})*")

                        # Display the question prompt
                        if question_text:
                            st.markdown(f"*{question_text}*")

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
                question_text = QUESTION_TEXTS.get(qid, "")
                st.markdown(f"**{label}** *(ID: {qid})*")
                if question_text:
                    st.markdown(f"*{question_text}*")
                st.info(answer)
    else:
        st.info("No narrative responses recorded for this case.")

    st.markdown("---")

    # Follow-up Questions and Answers section
    st.subheader("❓ Follow-Up Questions & Answers")

    follow_up_questions = get_follow_up_questions_for_case(case.case_id)

    if follow_up_questions:
        # Group by section
        sections = {"A": [], "B": [], "C": []}
        for fq in follow_up_questions:
            if fq.section in sections:
                sections[fq.section].append(fq)

        # Use correct section names based on intake type
        if case.intake_version == "abbrev_gen":
            section_names = {
                "A": "Section A: Reasoning Trace",
                "B": "Section B: Early Warning Signals (LT vs Hospital)",
                "C": "Section C: Decision Points & Triggers"
            }
        else:
            section_names = {
                "A": "Section A: Reasoning Trace",
                "B": "Section B: Discharge Timing Dynamics",
                "C": "Section C: SNF Patient State Transitions & Navigator Time Allocation"
            }

        # Count answered questions
        total = len(follow_up_questions)
        answered = sum(1 for fq in follow_up_questions if fq.answer_text)
        st.markdown(f"**Progress:** {answered}/{total} questions answered")

        for section_key in ["A", "B", "C"]:
            section_questions = sections[section_key]
            if section_questions:
                with st.expander(f"📌 {section_names[section_key]} ({len([q for q in section_questions if q.answer_text])}/{len(section_questions)} answered)"):
                    for fq in sorted(section_questions, key=lambda x: x.question_number):
                        st.markdown(f"**Q{fq.question_number}:** {fq.question_text}")
                        if fq.answer_text:
                            st.success(f"**Answer:** {fq.answer_text}")
                        else:
                            st.warning("*Not yet answered*")
                        st.markdown("---")
    else:
        st.info("No follow-up questions generated for this case yet.")

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


# Title
st.title("🔍 Case Viewer")
st.markdown(f"Logged in as: **{get_current_username()}**")
st.markdown("---")

# Access mode selection
access_mode = st.radio(
    "Select access mode:",
    ["View My Cases", "View All Cases (Admin)"],
    horizontal=True
)

if access_mode == "View My Cases":
    # User mode - show only their cases (using logged-in username)
    current_user = get_current_username()
    st.markdown(f"### Your Cases")

    # Get cases for current user
    user_cases = get_cases_by_user_name(current_user)

    if user_cases:
        st.success(f"Found {len(user_cases)} case(s)")
        st.markdown("---")

        # Get case numbers by intake type
        case_numbers = get_case_numbers_by_type(user_cases)

        # Let user select which case to view
        case_options = {}
        for c in user_cases:
            # Format time in CST
            time_str = format_time_cst(c.created_at)
            # Get intake type and case number
            intake_type, case_num = case_numbers.get(c.case_id, ("Unknown", "?"))
            # Include intake type and demographics for easier identification
            label = f"Case {case_num} - {intake_type} ({c.age_at_snf_stay}, {c.race}, {c.state}) - {time_str}"
            case_options[label] = (c.case_id, case_num)

        selected_case_label = st.selectbox(
            "Select a case to view:",
            options=list(case_options.keys())
        )

        if selected_case_label:
            selected_case_id, case_num = case_options[selected_case_label]
            selected_case = get_case_by_id(selected_case_id)

            if selected_case:
                st.markdown("---")
                display_case(selected_case, case_number=case_num)
    else:
        st.info("You haven't created any cases yet. Go to **Abbreviated Intake** or **Full Intake** to create your first case.")

else:
    # Admin mode - show all cases by person
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

        if st.button("🔓 Access Admin View", use_container_width=True, type="primary"):
            if admin_password_input == ADMIN_PASSWORD:
                st.session_state['admin_authenticated'] = True
            else:
                st.error("❌ Incorrect admin password.")

        # Show admin interface if authenticated
        if st.session_state.get('admin_authenticated', False):
            st.success("✅ Admin access granted!")
            st.markdown("---")

            # Get all unique user names
            all_users = get_all_user_names()

            if all_users:
                st.markdown(f"### Select a Person ({len(all_users)} total)")

                # Dropdown to select a person
                selected_user = st.selectbox(
                    "Select a person to view their cases:",
                    options=[""] + all_users,
                    format_func=lambda x: "-- Select a person --" if x == "" else x
                )

                if selected_user:
                    # Get cases for selected user
                    user_cases = get_cases_by_user_name(selected_user)

                    if user_cases:
                        st.markdown(f"### Cases for: **{selected_user}** ({len(user_cases)} total)")
                        st.markdown("---")

                        # Get case numbers by intake type
                        case_numbers = get_case_numbers_by_type(user_cases)

                        # Let admin select which case to view
                        case_options = {}
                        for c in user_cases:
                            # Format time in CST
                            time_str = format_time_cst(c.created_at)
                            # Get intake type and case number
                            intake_type, case_num = case_numbers.get(c.case_id, ("Unknown", "?"))
                            # Include intake type and demographics for easier identification
                            label = f"Case {case_num} - {intake_type} ({c.age_at_snf_stay}, {c.race}, {c.state}) - {time_str}"
                            case_options[label] = (c.case_id, case_num)

                        selected_case_label = st.selectbox(
                            "Select a case to view:",
                            options=list(case_options.keys()),
                            key="admin_case_select"
                        )

                        if selected_case_label:
                            selected_case_id, case_num = case_options[selected_case_label]
                            selected_case = get_case_by_id(selected_case_id)

                            if selected_case:
                                st.markdown("---")
                                st.markdown(f"**Created by:** {selected_case.user_name}")
                                display_case(selected_case, case_number=case_num)
                    else:
                        st.info(f"No cases found for {selected_user}.")
            else:
                st.info("No cases have been recorded yet.")

# Sidebar info
with st.sidebar:
    st.markdown("### Case Viewer")
    st.markdown(f"**User:** {get_current_username()}")
    st.markdown("""
    **View My Cases:**
    - See all your cases
    - Cases numbered in order (Case 1, Case 2, etc.)
    - Download cases as JSON

    **Admin Mode:**
    - Enter admin password
    - Select a person from dropdown
    - View all their cases
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Download cases as JSON for offline review
    - Contact admin for full access
    """)
