"""
SNF Patient Navigator Case Collection - Case Viewer Page

Search and view saved cases with transcript version history.
Requires authentication - users can only view their own cases.
Admin users can view all cases with the admin password.
"""

import streamlit as st
import json
from db import (
    get_case_by_id, get_cases_by_user_name, get_all_user_names,
    get_audio_responses_for_case, get_audio_response_versions,
    init_db
)
from auth import require_auth, get_current_username, is_authenticated, init_session_state

# Page configuration
st.set_page_config(
    page_title="Case Viewer | SNF Navigator",
    page_icon="🔍",
    layout="wide"
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
init_session_state()

# Check authentication
if not require_auth():
    st.stop()

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


def display_audio_versions(case_id: str, question_id: str):
    """Display all transcript versions for a question with audio."""
    versions = get_audio_response_versions(case_id, question_id)

    if not versions:
        return

    st.markdown("**🎙️ Audio Transcript Versions:**")

    for v in versions:
        with st.expander(f"Version {v.version_number} ({v.created_at.strftime('%Y-%m-%d %H:%M')})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original Transcript (Auto):**")
                if v.auto_transcript:
                    st.text_area(
                        "Auto transcript",
                        value=v.auto_transcript,
                        height=100,
                        disabled=True,
                        key=f"auto_{v.id}",
                        label_visibility="collapsed"
                    )
                else:
                    st.info("No auto-transcript")

            with col2:
                st.markdown("**Edited Transcript:**")
                if v.edited_transcript:
                    st.text_area(
                        "Edited transcript",
                        value=v.edited_transcript,
                        height=100,
                        disabled=True,
                        key=f"edited_{v.id}",
                        label_visibility="collapsed"
                    )
                else:
                    st.info("No edits")

            # Play audio if available
            if v.audio_data:
                st.audio(v.audio_data, format="audio/wav")


def display_case(case, case_number=None, show_versions=False):
    """Display a single case with all its details."""

    # Case metadata header
    if case_number:
        st.header(f"Case {case_number}")
    else:
        st.header(f"Case")

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

    # Get audio responses for this case (for version display)
    audio_responses = {}
    if show_versions:
        all_audio = get_audio_responses_for_case(case.case_id)
        for ar in all_audio:
            if ar.question_id not in audio_responses:
                audio_responses[ar.question_id] = []
            audio_responses[ar.question_id].append(ar)

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

                        # Show transcript versions if available and requested
                        if show_versions and qid in audio_responses:
                            display_audio_versions(case.case_id, qid)

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

                if show_versions and qid in audio_responses:
                    display_audio_versions(case.case_id, qid)
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


# Title
st.title("🔍 Case Viewer")
st.markdown(f"Logged in as: **{get_current_username()}**")
st.markdown("---")

# Show transcript versions checkbox
show_versions = st.checkbox(
    "Show transcript version history",
    value=False,
    help="Display all versions of audio transcripts (original and edited)"
)

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

        # Let user select which case to view (numbered Case 1, Case 2, etc.)
        case_options = {}
        for idx, c in enumerate(user_cases, start=1):
            label = f"Case {idx} ({c.created_at.strftime('%Y-%m-%d %H:%M')}) - {c.intake_version.title()}"
            case_options[label] = (c.case_id, idx)

        selected_case_label = st.selectbox(
            "Select a case to view:",
            options=list(case_options.keys())
        )

        if selected_case_label:
            selected_case_id, case_num = case_options[selected_case_label]
            selected_case = get_case_by_id(selected_case_id)

            if selected_case:
                st.markdown("---")
                display_case(selected_case, case_number=case_num, show_versions=show_versions)
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

                        # Let admin select which case to view (numbered Case 1, Case 2, etc.)
                        case_options = {}
                        for idx, c in enumerate(user_cases, start=1):
                            label = f"Case {idx} ({c.created_at.strftime('%Y-%m-%d %H:%M')}) - {c.intake_version.title()}"
                            case_options[label] = (c.case_id, idx)

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
                                display_case(selected_case, case_number=case_num, show_versions=show_versions)
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
    - View transcript version history

    **Admin Mode:**
    - Enter admin password
    - Select a person from dropdown
    - View all their cases
    """)

    st.markdown("---")
    st.markdown("### Transcript Versions")
    st.markdown("""
    Enable **"Show transcript version history"** to see:
    - Original auto-transcription
    - Edited versions
    - All changes over time
    - Audio playback
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Download cases as JSON for offline review
    - Contact admin for full access
    """)
