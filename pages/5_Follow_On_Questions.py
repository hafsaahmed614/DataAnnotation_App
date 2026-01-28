"""
SNF Patient Navigator Case Collection - Follow-On Questions Page

This page allows users to answer AI-generated follow-up questions for their cases.
Users can return to complete unanswered questions at any time.
"""

import streamlit as st
from db import (
    init_db,
    get_setting,
    get_cases_with_pending_follow_ups,
    get_follow_up_questions_for_case,
    update_follow_up_answer,
    save_follow_up_audio_response,
    get_latest_follow_up_audio,
    get_case_by_id
)
from auth import require_auth, get_current_username, init_session_state
from transcribe import transcribe_audio

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

# Initialize session state
if 'selected_followup_case' not in st.session_state:
    st.session_state.selected_followup_case = None
if 'followup_answers' not in st.session_state:
    st.session_state.followup_answers = {}
if 'followup_audio' not in st.session_state:
    st.session_state.followup_audio = {}
if 'followup_transcripts' not in st.session_state:
    st.session_state.followup_transcripts = {}

# Title
st.title("❓ Follow-On Questions")
st.markdown(f"""
Logged in as: **{get_current_username()}**

Answer the AI-generated follow-up questions for your cases. These questions help capture
deeper reasoning, timing dynamics, and factors that influenced patient outcomes.

You can **type** your answers or **record audio** which will be automatically transcribed.
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

# Check if we have a case from redirect (just saved)
if 'last_saved_case_id' in st.session_state and st.session_state.last_saved_case_id:
    # Auto-select the just-saved case
    st.session_state.selected_followup_case = st.session_state.last_saved_case_id
    st.session_state.last_saved_case_id = None

# Case selection section
st.header("1. Select a Case")

# Create a formatted list of cases for selection
case_options = []
case_id_map = {}
for case_info in cases_with_followups:
    case_id = case_info["case_id"]
    intake_type = "Abbreviated" if case_info["intake_version"] == "abbrev" else "Full"
    created = case_info["created_at"].strftime("%Y-%m-%d %H:%M") if case_info["created_at"] else "Unknown"
    answered = case_info["answered_questions"]
    total = case_info["total_questions"]
    status = "✅ Complete" if case_info["is_complete"] else f"⏳ {answered}/{total} answered"

    display_name = f"{intake_type} Intake ({created}) - {status}"
    case_options.append(display_name)
    case_id_map[display_name] = case_id

# Case selector
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
if case:
    with st.expander("📋 Case Summary", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Intake Type:** {'Abbreviated' if case.intake_version == 'abbrev' else 'Full'}")
            st.markdown(f"**Age:** {case.age_at_snf_stay}")
            st.markdown(f"**Gender:** {case.gender}")
        with col2:
            st.markdown(f"**Race:** {case.race}")
            st.markdown(f"**State:** {case.state}")
            st.markdown(f"**SNF Days:** {case.snf_days if case.snf_days else 'Not provided'}")

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

# Progress bar
st.header("2. Answer Follow-Up Questions")
st.progress(progress, text=f"Progress: {answered_questions}/{total_questions} questions answered ({int(progress*100)}%)")

# Initialize session state for this case's answers if needed
if selected_case_id not in st.session_state.followup_answers:
    st.session_state.followup_answers[selected_case_id] = {}
    st.session_state.followup_audio[selected_case_id] = {}
    st.session_state.followup_transcripts[selected_case_id] = {}

    # Pre-populate with existing answers
    for q in questions:
        st.session_state.followup_answers[selected_case_id][q.id] = q.answer_text or ""
        # Load existing audio transcript if any
        existing_audio = get_latest_follow_up_audio(selected_case_id, q.id)
        if existing_audio:
            st.session_state.followup_transcripts[selected_case_id][q.id] = existing_audio.auto_transcript

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
    status_icon = "✅" if is_answered else "⏳"

    st.markdown(f"**{status_icon} Question {section}{question.question_number}:**")
    st.markdown(f"*{question.question_text}*")

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
            st.audio(audio_bytes, format="audio/wav")

            # Transcribe button
            if st.button(f"Transcribe", key=f"transcribe_fu_{q_id}"):
                with st.spinner("Transcribing..."):
                    transcript = transcribe_audio(audio_bytes)
                    if transcript:
                        st.session_state.followup_transcripts[selected_case_id][q_id] = transcript
                        st.session_state.followup_answers[selected_case_id][q_id] = transcript
                        st.success("Transcription complete!")
                        st.rerun()
                    else:
                        st.error("Transcription failed. Please try again or type your answer.")

        # Show transcript if available
        transcript = st.session_state.followup_transcripts[selected_case_id].get(q_id)
        if transcript:
            st.markdown("**Auto-transcribed:**")
            st.info(transcript)

            # Editable transcript
            edited = st.text_area(
                "Edit transcript if needed:",
                value=st.session_state.followup_answers[selected_case_id].get(q_id, ""),
                height=120,
                key=f"edit_fu_{q_id}",
                help="Edit the transcription if needed before saving."
            )
            st.session_state.followup_answers[selected_case_id][q_id] = edited
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

    # Individual save button for this question
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save", key=f"save_fu_{q_id}", type="secondary"):
            answer_text = st.session_state.followup_answers[selected_case_id].get(q_id, "").strip()

            if answer_text:
                try:
                    # Save the answer
                    update_follow_up_answer(q_id, answer_text)

                    # Save audio if available
                    audio_data = st.session_state.followup_audio[selected_case_id].get(q_id)
                    auto_transcript = st.session_state.followup_transcripts[selected_case_id].get(q_id)

                    if audio_data or auto_transcript:
                        save_follow_up_audio_response(
                            case_id=selected_case_id,
                            follow_up_question_id=q_id,
                            audio_data=audio_data,
                            auto_transcript=auto_transcript,
                            edited_transcript=answer_text if answer_text != auto_transcript else None
                        )

                    st.success("✅ Answer saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving answer: {str(e)}")
            else:
                st.warning("Please provide an answer before saving.")

    with col2:
        if is_answered:
            st.caption("✅ This question has been answered")

st.markdown("---")

# Save All button
st.header("3. Save All Answers")

if st.button("💾 Save All Answers", use_container_width=True, type="primary"):
    saved_count = 0
    error_count = 0

    with st.spinner("Saving all answers..."):
        for question in questions:
            q_id = question.id
            answer_text = st.session_state.followup_answers[selected_case_id].get(q_id, "").strip()

            if answer_text:
                try:
                    # Save the answer
                    update_follow_up_answer(q_id, answer_text)

                    # Save audio if available
                    audio_data = st.session_state.followup_audio[selected_case_id].get(q_id)
                    auto_transcript = st.session_state.followup_transcripts[selected_case_id].get(q_id)

                    if audio_data or auto_transcript:
                        save_follow_up_audio_response(
                            case_id=selected_case_id,
                            follow_up_question_id=q_id,
                            audio_data=audio_data,
                            auto_transcript=auto_transcript,
                            edited_transcript=answer_text if answer_text != auto_transcript else None
                        )

                    saved_count += 1
                except Exception as e:
                    error_count += 1
                    st.error(f"Error saving question {question.section}{question.question_number}: {str(e)}")

    if saved_count > 0:
        st.success(f"✅ Successfully saved {saved_count} answer(s)!")
    if error_count > 0:
        st.warning(f"⚠️ {error_count} answer(s) could not be saved.")

    st.rerun()

# Sidebar info
with st.sidebar:
    st.markdown("### Follow-On Questions")
    st.markdown(f"**User:** {get_current_username()}")

    st.markdown("---")
    st.markdown("### Your Cases")
    for case_info in cases_with_followups:
        intake_type = "Abbrev" if case_info["intake_version"] == "abbrev" else "Full"
        status = "✅" if case_info["is_complete"] else f"⏳ {case_info['answered_questions']}/{case_info['total_questions']}"
        st.markdown(f"- {intake_type}: {status}")

    st.markdown("---")
    st.markdown("### Question Sections")
    for section, label in SECTION_LABELS.items():
        st.markdown(f"**{section})** {label}")

    st.markdown("---")
    st.markdown("### Audio Recording")
    current_model = get_setting("whisper_model_size", "base")
    st.markdown(f"**Whisper Model:** {current_model}")
    st.markdown("""
    - Select **Record Audio** for any question
    - Click **Transcribe** to convert to text
    - Edit the transcript if needed
    - Save individual answers or all at once
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Answer in **past tense**
    - Be as detailed as possible
    - You can save answers individually or all at once
    - Return anytime to complete remaining questions
    """)
