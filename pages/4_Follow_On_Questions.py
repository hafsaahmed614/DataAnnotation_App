"""
SNF Patient Navigator Case Collection - Follow-On Questions Page

This page allows users to answer AI-generated follow-up questions for their cases.
Users can return to complete unanswered questions at any time.
"""

import json
import streamlit as st
from db import (
    init_db,
    get_setting,
    get_cases_with_pending_follow_ups,
    get_follow_up_questions_for_case,
    update_follow_up_answer,
    save_follow_up_audio_response,
    get_latest_follow_up_audio,
    get_case_by_id,
    get_cases_by_user_name
)
from auth import require_auth, get_current_username, init_session_state

# Page configuration
st.set_page_config(
    page_title="Follow-On Questions | SNF Navigator",
    page_icon="❓",
    layout="wide"
)

# Custom CSS to rename "app" to "Dashboard" in sidebar
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child a span {
        font-size: 0 !important;
    }
    [data-testid="stSidebarNav"] li:first-child a span::before {
        content: "Dashboard";
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
init_db()
init_session_state()

# Check authentication
if not require_auth():
    st.stop()

# Section labels for display
SECTION_LABELS = {
    "A": "Reasoning Trace",
    "B": "Discharge Timing Dynamics",
    "C": "SNF Patient State Transitions, Incentives, and Navigator Time Allocation"
}

# Question labels for abbreviated intake
ABBREVIATED_QUESTION_LABELS = {
    "aq1": "Case Summary",
    "aq2": "SNF Team Discharge Timing",
    "aq3": "Requirements for Safe Discharge",
    "aq4": "Estimated Discharge Date",
    "aq5": "Alignment Across Stakeholders",
    "aq6": "SNF Discharge Conditions",
    "aq7": "HHA Involvement",
    "aq8": "Information Shared with HHA"
}

# Question labels for full intake
FULL_INTAKE_QUESTION_LABELS = {
    "q6": "Case Summary",
    "q7": "Referral Source and Expectation",
    "q8": "Upstream Path to SNF",
    "q9": "Expected Length of Stay at Admission",
    "q10": "Initial Assessment",
    "q11": "Early Home Feasibility Reasoning",
    "q12": "Key SNF Roles and People",
    "q13": "Patient Response to Discharge/Services",
    "q14": "Patient/Family Goals for Home",
    "q15": "SNF Discharge Timing Over Time",
    "q16": "Requirements for Safe Discharge",
    "q17": "Services Discussed and Agreed",
    "q18": "HHA Involvement and Handoff",
    "q19": "Information Shared with HHA",
    "q20": "Estimated Discharge Date and Reasoning",
    "q21": "Alignment Across Stakeholders",
    "q22": "SNF Discharge Conditions",
    "q23": "Plan for First 24-48 Hours",
    "q25": "Transition SNF to Home Overall",
    "q26": "Handoff Completion and Gaps",
    "q27": "24-Hour Follow-up Contact",
    "q28": "Initial At-Home Status and Next Steps"
}

# Initialize session state
if 'selected_followup_case' not in st.session_state:
    st.session_state.selected_followup_case = None
if 'followup_answers' not in st.session_state:
    st.session_state.followup_answers = {}
if 'followup_audio' not in st.session_state:
    st.session_state.followup_audio = {}
if 'saved_questions' not in st.session_state:
    st.session_state.saved_questions = set()  # Track which questions were just saved


def get_case_numbers_by_type(username: str) -> dict:
    """
    Get case numbers for each case, separated by intake type.
    Returns a dict mapping case_id to its number within its intake type.
    """
    all_cases = get_cases_by_user_name(username)

    # Separate by intake type and number them
    abbrev_count = 0
    full_count = 0
    case_numbers = {}

    for case in all_cases:  # Already ordered by created_at ascending
        if case.intake_version == "abbrev":
            abbrev_count += 1
            case_numbers[case.case_id] = ("Abbreviated Intake", abbrev_count)
        else:
            full_count += 1
            case_numbers[case.case_id] = ("Full Intake", full_count)

    return case_numbers


def save_single_answer(case_id: str, q_id: str, answer_text: str, is_na: bool = False):
    """Save a single answer and return success status."""
    try:
        # Save the answer
        update_follow_up_answer(q_id, answer_text)

        # Save audio if available and not N/A (no transcription - admin only)
        if not is_na:
            audio_data = st.session_state.followup_audio.get(case_id, {}).get(q_id)

            if audio_data:
                save_follow_up_audio_response(
                    case_id=case_id,
                    follow_up_question_id=q_id,
                    audio_data=audio_data,
                    auto_transcript=None,  # Transcription is admin-only
                    edited_transcript=None
                )

        # Mark as saved in session state
        st.session_state.saved_questions.add(q_id)
        return True
    except Exception as e:
        st.error(f"Error saving answer: {str(e)}")
        return False


# Title
st.title("❓ Follow-On Questions")
st.markdown(f"""
Logged in as: **{get_current_username()}**

Answer the AI-generated follow-up questions for your cases. These questions help capture
deeper reasoning, timing dynamics, and factors that influenced patient outcomes.

You can **type** your answers or **record audio**.
""")
st.markdown("---")

# Get user's cases with follow-up questions
username = get_current_username()
cases_with_followups = get_cases_with_pending_follow_ups(username)

if not cases_with_followups:
    st.info("📋 You don't have any cases with follow-up questions yet.")
    st.markdown("""
    Follow-up questions are generated automatically when you save a case in:
    - **Abbreviated Intake**
    - **Full Intake**

    Complete an intake form to get started!
    """)
    st.stop()

# Get case numbers for display
case_numbers = get_case_numbers_by_type(username)

# Create a formatted list of cases for selection with new naming format
case_options = []
case_id_map = {}
reverse_case_id_map = {}  # Map case_id back to display name
for case_info in cases_with_followups:
    case_id = case_info["case_id"]
    answered = case_info["answered_questions"]
    total = case_info["total_questions"]
    status = "✅ Complete" if case_info["is_complete"] else f"⏳ {answered}/{total} answered"

    # Get the case number from our mapping
    if case_id in case_numbers:
        intake_type, case_num = case_numbers[case_id]
        display_name = f"{intake_type} - Case {case_num} - {status}"
    else:
        # Fallback if not found
        intake_type = "Abbreviated Intake" if case_info["intake_version"] == "abbrev" else "Full Intake"
        display_name = f"{intake_type} - {status}"

    case_options.append(display_name)
    case_id_map[display_name] = case_id
    reverse_case_id_map[case_id] = display_name

# Check if we have a case from redirect (just saved)
# Set the widget's session state key directly to avoid the warning
if 'last_saved_case_id' in st.session_state and st.session_state.last_saved_case_id:
    redirect_case_id = st.session_state.last_saved_case_id
    st.session_state.last_saved_case_id = None
    # Set the widget key directly if the case exists in our options
    if redirect_case_id in reverse_case_id_map:
        st.session_state.case_selector = reverse_case_id_map[redirect_case_id]
        st.session_state.selected_followup_case = redirect_case_id

# Case selection section
st.header("1. Select a Case")

# Determine if we need to set a default (only on first load when key doesn't exist)
if "case_selector" not in st.session_state:
    # First load - use the selected_followup_case if set, otherwise default to placeholder
    if st.session_state.selected_followup_case and st.session_state.selected_followup_case in reverse_case_id_map:
        st.session_state.case_selector = reverse_case_id_map[st.session_state.selected_followup_case]
    else:
        st.session_state.case_selector = "Select a case..."

selected_display = st.selectbox(
    "Choose a case to answer follow-up questions:",
    options=["Select a case..."] + case_options,
    key="case_selector"
)

if selected_display == "Select a case...":
    st.info("👆 Select a case above to view and answer follow-up questions.")
    st.stop()

# Get the selected case ID
selected_case_id = case_id_map[selected_display]
st.session_state.selected_followup_case = selected_case_id

# Get case details for context
case = get_case_by_id(selected_case_id)

st.markdown("---")

# Get follow-up questions for this case
questions = get_follow_up_questions_for_case(selected_case_id)

if not questions:
    st.warning("No follow-up questions found for this case.")
    st.stop()

# Calculate progress
total_questions = len(questions)
answered_questions = sum(1 for q in questions if q.answer_text)
progress = answered_questions / total_questions if total_questions > 0 else 0

# Create two columns - main content and side panel
main_col, side_col = st.columns([3, 1])

with side_col:
    # Collapsible case details panel
    st.markdown("### 📋 Case Details")

    if case:
        with st.expander("Demographics", expanded=True):
            st.markdown(f"**Age:** {case.age_at_snf_stay}")
            st.markdown(f"**Gender:** {case.gender}")
            st.markdown(f"**Race:** {case.race}")
            st.markdown(f"**State:** {case.state}")
            st.markdown(f"**SNF Days:** {case.snf_days if case.snf_days else 'N/A'}")

        with st.expander("Services", expanded=True):
            st.markdown(f"**Discussed:** {case.services_discussed if case.services_discussed else 'N/A'}")
            st.markdown(f"**Accepted:** {case.services_accepted if case.services_accepted else 'N/A'}")

        # Show narrative answers - full text, not truncated
        with st.expander("Narrative Answers", expanded=False):
            if case.answers_json:
                try:
                    answers = json.loads(case.answers_json)
                    # Get the right labels based on intake type
                    if case.intake_version == "abbrev":
                        labels = ABBREVIATED_QUESTION_LABELS
                    else:
                        labels = FULL_INTAKE_QUESTION_LABELS

                    for qid, answer in answers.items():
                        if answer and answer.strip():  # Only show non-empty answers
                            label = labels.get(qid, qid)
                            st.markdown(f"**{label}:**")
                            # Show full answer text, not truncated
                            st.text_area(
                                label,
                                value=answer,
                                height=150,
                                disabled=True,
                                label_visibility="collapsed",
                                key=f"narrative_{qid}"
                            )
                            st.markdown("---")
                except:
                    st.markdown("_Unable to load answers_")

with main_col:
    # Progress bar
    st.header("2. Answer Follow-Up Questions")
    st.progress(progress, text=f"Progress: {answered_questions}/{total_questions} questions answered ({int(progress*100)}%)")

    # Initialize session state for this case's answers if needed
    if selected_case_id not in st.session_state.followup_answers:
        st.session_state.followup_answers[selected_case_id] = {}
        st.session_state.followup_audio[selected_case_id] = {}

        # Pre-populate with existing answers
        for q in questions:
            st.session_state.followup_answers[selected_case_id][q.id] = q.answer_text or ""

    # Group questions by section
    current_section = None
    for question in questions:
        section = question.section

        # Add section header when section changes
        if section != current_section:
            current_section = section
            st.markdown("---")
            st.subheader(f"Section {section}: {SECTION_LABELS.get(section, section)}")

        # Question display
        q_id = question.id
        is_answered = question.answer_text is not None
        is_na = question.answer_text == "N/A"
        was_just_saved = q_id in st.session_state.saved_questions

        # Status icon
        if is_na:
            status_icon = "⊘"
            status_text = "N/A"
        elif is_answered:
            status_icon = "✅"
            status_text = "Answered"
        else:
            status_icon = "⏳"
            status_text = "Pending"

        st.markdown(f"**{status_icon} Question {section}{question.question_number}:** _{status_text}_")
        st.markdown(f"*{question.question_text}*")

        # Show "Saved" indicator if just saved
        if was_just_saved:
            st.success("✅ Saved!")

        # Skip input if already answered as N/A
        if is_na:
            st.info("This question was marked as N/A")
        else:
            # Input method selector
            input_method = st.radio(
                f"Answer method:",
                ["Type", "Record Audio"],
                key=f"method_fu_{q_id}",
                horizontal=True,
                label_visibility="collapsed"
            )

            if input_method == "Record Audio":
                # Audio recording
                audio_value = st.audio_input(
                    f"Record your answer",
                    key=f"audio_fu_{q_id}"
                )

                if audio_value is not None:
                    audio_bytes = audio_value.read()
                    st.session_state.followup_audio[selected_case_id][q_id] = audio_bytes
                    # Use the file's actual MIME type for playback (browsers record in WebM, not WAV)
                    st.audio(audio_bytes, format=audio_value.type if hasattr(audio_value, 'type') else "audio/webm")
                    st.success("✅ Audio recorded! Click Save to submit.")
                    # Mark that this question has audio (for save logic)
                    st.session_state.followup_answers[selected_case_id][q_id] = "[Audio response]"
                else:
                    # Check if audio was previously recorded
                    if st.session_state.followup_audio.get(selected_case_id, {}).get(q_id):
                        st.info("Audio previously recorded.")
            else:
                # Text input
                current_value = st.session_state.followup_answers[selected_case_id].get(q_id, "")
                text_answer = st.text_area(
                    "Type your answer:",
                    value=current_value,
                    height=120,
                    key=f"text_fu_{q_id}",
                    label_visibility="collapsed",
                    help="Provide a detailed answer to this follow-up question."
                )
                st.session_state.followup_answers[selected_case_id][q_id] = text_answer

            # Save and N/A buttons
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("💾 Save", key=f"save_fu_{q_id}", type="secondary"):
                    answer_text = st.session_state.followup_answers[selected_case_id].get(q_id, "").strip()

                    if answer_text:
                        if save_single_answer(selected_case_id, q_id, answer_text):
                            st.rerun()
                    else:
                        st.warning("Please provide an answer before saving.")

            with col2:
                if st.button("⊘ N/A", key=f"na_fu_{q_id}", type="secondary"):
                    if save_single_answer(selected_case_id, q_id, "N/A", is_na=True):
                        st.rerun()

    st.markdown("---")

    # Save All button
    st.header("3. Save All Answers")

    if st.button("💾 Save All Answers", use_container_width=True, type="primary"):
        saved_count = 0
        error_count = 0
        already_saved_count = 0
        empty_count = 0

        with st.spinner("Saving all answers..."):
            for question in questions:
                q_id = question.id
                answer_text = st.session_state.followup_answers[selected_case_id].get(q_id, "").strip()

                if not answer_text:
                    # Empty answer, skip
                    empty_count += 1
                elif question.answer_text == answer_text:
                    # Already saved with same value
                    already_saved_count += 1
                else:
                    # New or changed answer, save it
                    if save_single_answer(selected_case_id, q_id, answer_text):
                        saved_count += 1
                    else:
                        error_count += 1

        # Calculate total answered
        total_answered = saved_count + already_saved_count

        if saved_count > 0:
            st.success(f"✅ Saved {saved_count} new answer(s)! Total answered: {total_answered}/{total_questions}")
        elif already_saved_count > 0:
            st.success(f"✅ All {already_saved_count} answer(s) already saved!")
        elif empty_count == total_questions:
            st.warning("No answers to save. Please answer some questions first.")
        else:
            st.info("No new answers to save.")
        if error_count > 0:
            st.warning(f"⚠️ {error_count} answer(s) could not be saved.")

# Sidebar info
with st.sidebar:
    st.markdown("### Follow-On Questions")
    st.markdown(f"**User:** {get_current_username()}")

    st.markdown("---")
    st.markdown("### Your Cases")
    for case_info in cases_with_followups:
        case_id = case_info["case_id"]
        if case_id in case_numbers:
            intake_type, case_num = case_numbers[case_id]
            short_type = "Abbrev" if "Abbreviated" in intake_type else "Full"
        else:
            short_type = "Abbrev" if case_info["intake_version"] == "abbrev" else "Full"
            case_num = "?"
        status = "✅" if case_info["is_complete"] else f"⏳ {case_info['answered_questions']}/{case_info['total_questions']}"
        st.markdown(f"- {short_type} #{case_num}: {status}")

    st.markdown("---")
    st.markdown("### Question Sections")
    for section, label in SECTION_LABELS.items():
        st.markdown(f"**{section})** {label}")

    st.markdown("---")
    st.markdown("### Audio Recording")
    st.markdown("""
    - Select **Record Audio** for any question
    - Click **N/A** if question doesn't apply
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Answer in **past tense**
    - Be as detailed as possible
    - Use **N/A** for non-applicable questions
    - Return anytime to complete remaining questions
    """)
