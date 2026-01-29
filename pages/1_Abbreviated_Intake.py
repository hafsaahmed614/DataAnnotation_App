"""
SNF Patient Navigator Case Collection - Abbreviated Intake Page

Shorter intake form capturing essential case information with conversational
narrative prompts. Supports both typed and audio-recorded answers.
"""

import streamlit as st
from db import create_case, save_audio_response, init_db, get_setting, create_follow_up_questions
from auth import require_auth, get_current_username, init_session_state
from openai_integration import generate_follow_up_questions

# Page configuration
st.set_page_config(
    page_title="Abbreviated Intake | SNF Navigator",
    page_icon="📝",
    layout="wide"
)

# Custom CSS to rename "app" to "Dashboard" in sidebar (using font-size trick to reduce flicker)
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

# Constants
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"
]

GENDER_OPTIONS = ["Female", "Male", "Non-binary", "Other", "Prefer not to say"]

RACE_OPTIONS = [
    "American Indian or Alaska Native",
    "Asian",
    "Black or African American",
    "Hispanic or Latino",
    "Native Hawaiian or Other Pacific Islander",
    "White",
    "Two or More Races",
    "Other",
    "Prefer not to say"
]

# Abbreviated intake narrative questions with stable IDs
ABBREV_QUESTIONS = {
    "aq1": {
        "label": "Case Summary",
        "prompt": "Please provide a brief summary of this case: Why was the patient in the SNF, and what was the intended goal for getting them home? (2-5 sentences)",
        "help": "Describe the main reason for the SNF stay and the discharge goal."
    },
    "aq2": {
        "label": "SNF Team Discharge Timing",
        "prompt": "How did the SNF team's view of discharge timing and readiness evolve over time? Did expectations change from admission to discharge?",
        "help": "Describe how the timeline and readiness assessment shifted during the stay."
    },
    "aq3": {
        "label": "Requirements for Safe Discharge",
        "prompt": "What needed to happen before a safe discharge home was possible?",
        "help": "List the conditions, milestones, or preparations required."
    },
    "aq4": {
        "label": "Estimated Discharge Date",
        "prompt": "What was your best estimate of the discharge date before the patient actually left? What was that estimate based on?",
        "help": "Describe your prediction and the reasoning behind it."
    },
    "aq5": {
        "label": "Alignment Across Stakeholders",
        "prompt": "How aligned were the SNF team, patient/family, and HHA on the discharge plan? If there was misalignment, where did it occur?",
        "help": "Describe agreement or disagreement among parties involved."
    },
    "aq6": {
        "label": "SNF Discharge Conditions",
        "prompt": "What conditions did the SNF require to be met before discharging the patient home?",
        "help": "List specific criteria the SNF needed satisfied."
    },
    "aq7": {
        "label": "HHA Involvement",
        "prompt": "Was a Home Health Agency (HHA) involved? If so, which agency, and what happened with the handoff?",
        "help": "Describe the HHA coordination and transition process."
    },
    "aq8": {
        "label": "Information Shared with HHA",
        "prompt": "What information was shared with the HHA to prepare them for the patient's care at home?",
        "help": "Describe the content and method of information transfer."
    }
}

# Initialize session state for form data
if 'abbrev_answers' not in st.session_state:
    st.session_state.abbrev_answers = {qid: "" for qid in ABBREV_QUESTIONS}
if 'abbrev_audio' not in st.session_state:
    st.session_state.abbrev_audio = {qid: None for qid in ABBREV_QUESTIONS}

# Title
st.title("📝 Abbreviated Intake")
st.markdown(f"""
Logged in as: **{get_current_username()}**

This form captures essential case information through a brief set of questions.
All questions are in **past tense** — please describe what happened in completed cases.

You can **type** your answers or **record audio**.

*Case start date is automatically set to January 1, 2025.*
""")
st.markdown("---")

# Section 1: Demographics
st.header("1. Patient Demographics")
st.markdown("*All demographic fields are required.*")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input(
        "Age at SNF Stay",
        min_value=0,
        max_value=120,
        value=None,
        help="Patient's age in years during the SNF stay",
        placeholder="Enter age...",
        key="abbrev_age"
    )

    gender = st.selectbox(
        "Gender",
        options=[""] + GENDER_OPTIONS,
        index=0,
        help="Patient's gender",
        key="abbrev_gender"
    )

with col2:
    race = st.selectbox(
        "Race",
        options=[""] + RACE_OPTIONS,
        index=0,
        help="Patient's race/ethnicity",
        key="abbrev_race"
    )

    state = st.selectbox(
        "SNF State",
        options=[""] + US_STATES,
        index=0,
        help="State where the SNF is located",
        key="abbrev_state"
    )

st.markdown("---")

# Section 2: Narrative Questions with Audio Support
st.header("2. Case Narrative")
st.markdown("*Answer by typing or recording audio.*")

for qid, question in ABBREV_QUESTIONS.items():
    st.subheader(question["label"])
    st.markdown(f"*{question['prompt']}*")

    # Input method selector
    input_method = st.radio(
        f"Answer method for {question['label']}:",
        ["Type", "Record Audio"],
        key=f"method_{qid}",
        horizontal=True,
        label_visibility="collapsed"
    )

    if input_method == "Record Audio":
        # Audio recording
        audio_value = st.audio_input(
            f"Record your answer for: {question['label']}",
            key=f"audio_{qid}"
        )

        if audio_value is not None:
            audio_bytes = audio_value.read()
            st.session_state.abbrev_audio[qid] = audio_bytes
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ Audio recorded!")
            # Mark that this question has audio
            if not st.session_state.abbrev_answers[qid]:
                st.session_state.abbrev_answers[qid] = "[Audio response]"
        else:
            # Check if audio was previously recorded
            if st.session_state.abbrev_audio.get(qid):
                st.info("Audio previously recorded.")
    else:
        # Text input
        text_answer = st.text_area(
            question["prompt"],
            value=st.session_state.abbrev_answers[qid],
            height=120,
            help=question["help"],
            key=f"text_{qid}",
            label_visibility="collapsed"
        )
        st.session_state.abbrev_answers[qid] = text_answer

    st.markdown("---")

# Section 3: Services and SNF Days
st.header("3. Services & Duration")

col1, col2 = st.columns(2)

with col1:
    services_discussed = st.text_area(
        "Services Discussed",
        height=100,
        help="List all services that were discussed with the patient/family",
        placeholder="e.g., Physical therapy, occupational therapy, home health aide, meal delivery...",
        key="abbrev_services_discussed"
    )

with col2:
    services_accepted = st.text_area(
        "Services Accepted",
        height=100,
        help="List which services the patient/family agreed to accept",
        placeholder="e.g., Physical therapy 3x/week, home health aide...",
        key="abbrev_services_accepted"
    )

snf_days = st.number_input(
    "How many days was the patient in the SNF?",
    min_value=0,
    max_value=365,
    value=None,
    help="Total number of days from admission to discharge",
    key="abbrev_snf_days"
)

st.markdown("---")

# Submit button
if st.button("💾 Save Case", use_container_width=True, type="primary"):
    # Validation
    errors = []

    if age is None:
        errors.append("Age at SNF Stay is required")
    if not gender:
        errors.append("Gender is required")
    if not race:
        errors.append("Race is required")
    if not state:
        errors.append("SNF State is required")

    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        try:
            # Get current username
            user_name = get_current_username()

            # Create case
            case_id = create_case(
                intake_version="abbrev",
                user_name=user_name,
                age_at_snf_stay=int(age),
                gender=gender,
                race=race,
                state=state,
                snf_days=int(snf_days) if snf_days is not None else None,
                services_discussed=services_discussed if services_discussed else None,
                services_accepted=services_accepted if services_accepted else None,
                answers=st.session_state.abbrev_answers
            )

            # Save audio responses for questions that have audio (no transcription - admin only)
            for qid in ABBREV_QUESTIONS:
                audio_data = st.session_state.abbrev_audio.get(qid)

                if audio_data:
                    save_audio_response(
                        case_id=case_id,
                        question_id=qid,
                        audio_data=audio_data,
                        auto_transcript=None,  # Transcription is admin-only
                        edited_transcript=None
                    )

            st.success(f"✅ Case saved successfully!")

            # Generate follow-up questions using OpenAI
            with st.spinner("Generating follow-up questions..."):
                demographics = {
                    "age_at_snf_stay": int(age),
                    "gender": gender,
                    "race": race,
                    "state": state
                }
                services = {
                    "snf_days": int(snf_days) if snf_days is not None else None,
                    "services_discussed": services_discussed if services_discussed else None,
                    "services_accepted": services_accepted if services_accepted else None
                }

                success, questions, error_msg = generate_follow_up_questions(
                    case_id=case_id,
                    intake_version="abbrev",
                    demographics=demographics,
                    services=services,
                    answers=st.session_state.abbrev_answers
                )

                if success and questions:
                    # Store questions in database with user_name
                    create_follow_up_questions(case_id, questions, user_name)
                    st.success(f"✅ Generated {len(questions)} follow-up questions!")
                    st.info("📋 Go to **Follow-On Questions** page to answer them.")
                    # Store case_id for redirect
                    st.session_state.last_saved_case_id = case_id
                else:
                    st.warning(f"⚠️ Could not generate follow-up questions: {error_msg}")
                    st.info("You can still view your case in the **Case Viewer**.")

            # Clear form data
            st.session_state.abbrev_answers = {qid: "" for qid in ABBREV_QUESTIONS}
            st.session_state.abbrev_audio = {qid: None for qid in ABBREV_QUESTIONS}

        except Exception as e:
            st.error(f"❌ Error saving case: {str(e)}")

# Sidebar info
with st.sidebar:
    st.markdown("### Abbreviated Intake")
    st.markdown(f"**User:** {get_current_username()}")
    st.markdown("""
    This shorter form captures:
    - Patient demographics
    - Case summary
    - Discharge planning details
    - HHA coordination
    - Services discussed/accepted
    """)

    st.markdown("---")
    st.markdown("### Audio Recording")
    st.markdown("""
    - Click **Record Audio** to speak your answer
    - All recordings are saved
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Answer in **past tense**
    - Be as detailed as possible
    - All demographics are required
    - Narrative fields can be left blank if unknown
    """)
