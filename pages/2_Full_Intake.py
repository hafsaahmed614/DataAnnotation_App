"""
SNF Patient Navigator Case Collection - Full Intake Page

Comprehensive intake form with detailed questions about the entire patient journey.
Supports both typed and audio-recorded answers with automatic transcription.
"""

import streamlit as st
from db import create_case, save_audio_response, init_db, get_setting, create_follow_up_questions
from auth import require_auth, get_current_username, init_session_state
from transcribe import transcribe_audio
from openai_integration import generate_follow_up_questions

# Page configuration
st.set_page_config(
    page_title="Full Intake | SNF Navigator",
    page_icon="📋",
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

# Full intake narrative questions with stable IDs
FULL_QUESTIONS = {
    "q6": {
        "label": "Case Summary",
        "prompt": "Please provide a summary of this case: Why was the patient in the SNF, and what was the intended goal for getting them home?",
        "help": "Describe the main reason for the SNF stay and the discharge goal.",
        "section": "overview"
    },
    "q7": {
        "label": "Referral Source and Expectation",
        "prompt": "What was the referral source for this case? What expectations were set at the time of referral?",
        "help": "Describe who referred the patient and what initial expectations were communicated.",
        "section": "overview"
    },
    "q8": {
        "label": "Upstream Path to SNF",
        "prompt": "What was the patient's path to the SNF? Where did they come from, and what timing details do you recall about their journey?",
        "help": "Describe the patient's care journey leading up to the SNF admission.",
        "section": "admission"
    },
    "q9": {
        "label": "Expected Length of Stay at Admission",
        "prompt": "At the time of admission, what was the expected length of stay? How was this communicated?",
        "help": "Describe initial length of stay expectations and how they were determined.",
        "section": "admission"
    },
    "q10": {
        "label": "Initial Assessment",
        "prompt": "What did the initial assessment reveal? Consider social, functional, and logistical factors that were identified.",
        "help": "Describe key findings from the initial patient assessment.",
        "section": "admission"
    },
    "q11": {
        "label": "Early Home Feasibility",
        "prompt": "What was the early reasoning about whether going home was feasible? What factors were considered?",
        "help": "Describe the initial discharge planning considerations.",
        "section": "planning"
    },
    "q12": {
        "label": "Key SNF Roles and People",
        "prompt": "Who were the key SNF staff members or roles involved in this patient's care and discharge planning?",
        "help": "List the important people/roles and their contributions.",
        "section": "planning"
    },
    "q13": {
        "label": "Patient Response",
        "prompt": "How did the patient respond to discussions about going home and receiving services?",
        "help": "Describe the patient's reactions, concerns, and engagement.",
        "section": "planning"
    },
    "q14": {
        "label": "Patient/Family Goals",
        "prompt": "What were the patient's and family's goals for the first period at home after discharge?",
        "help": "Describe their priorities and expectations for the transition home.",
        "section": "planning"
    },
    "q15": {
        "label": "SNF Discharge Timing Over Time",
        "prompt": "How did the SNF team's view of discharge timing and readiness evolve over time? Did expectations change from admission to discharge?",
        "help": "Describe how the timeline and readiness assessment shifted during the stay.",
        "section": "discharge"
    },
    "q16": {
        "label": "Requirements for Safe Discharge",
        "prompt": "What needed to happen before a safe discharge home was possible?",
        "help": "List the conditions, milestones, or preparations required.",
        "section": "discharge"
    },
    "q17": {
        "label": "Services Discussion and Agreement",
        "prompt": "What services were discussed with the patient and family, and which services did they agree to receive?",
        "help": "Describe the services conversation and outcomes in narrative form.",
        "section": "discharge"
    },
    "q18": {
        "label": "HHA Involvement and Handoff",
        "prompt": "Was a Home Health Agency (HHA) involved? If so, which agency, and what happened with the handoff process?",
        "help": "Describe the HHA coordination and transition process.",
        "section": "hha"
    },
    "q19": {
        "label": "Information Shared with HHA",
        "prompt": "What information was shared with the HHA to prepare them for the patient's care at home?",
        "help": "Describe the content and method of information transfer.",
        "section": "hha"
    },
    "q20": {
        "label": "Estimated Discharge Date and Reasoning",
        "prompt": "What was your best estimate of the discharge date before the patient actually left? What was that estimate based on?",
        "help": "Describe your prediction and the reasoning behind it.",
        "section": "discharge"
    },
    "q21": {
        "label": "Alignment Across Stakeholders",
        "prompt": "How aligned were the SNF team, patient/family, and HHA on the discharge plan? If there was misalignment, describe the details.",
        "help": "Describe agreement or disagreement among parties involved.",
        "section": "discharge"
    },
    "q22": {
        "label": "SNF Discharge Conditions",
        "prompt": "What conditions did the SNF require to be met before discharging the patient home?",
        "help": "List specific criteria the SNF needed satisfied.",
        "section": "discharge"
    },
    "q23": {
        "label": "Plan for First 24-48 Hours",
        "prompt": "What was the plan for the first 24-48 hours after the patient arrived home?",
        "help": "Describe immediate post-discharge care plans and support.",
        "section": "transition"
    },
    "q25": {
        "label": "Transition SNF to Home Overall",
        "prompt": "How would you describe the overall transition from SNF to home? What went well and what could have been improved?",
        "help": "Provide an overall assessment of the transition quality.",
        "section": "transition"
    },
    "q26": {
        "label": "Handoff Completion and Gaps",
        "prompt": "Were all aspects of the handoff completed as planned? Were there any gaps or missing elements?",
        "help": "Describe what was completed and what was missed.",
        "section": "transition"
    },
    "q27": {
        "label": "24-Hour Follow-up Contact",
        "prompt": "Was there contact with the patient within 24 hours of discharge? If so, what was learned from that contact?",
        "help": "Describe any follow-up communication and findings.",
        "section": "followup"
    },
    "q28": {
        "label": "Initial At-Home Status",
        "prompt": "What was the patient's initial status at home, and what was identified as the next step in their care?",
        "help": "Describe how things were going and what came next.",
        "section": "followup"
    }
}

# Section labels for organization
SECTIONS = {
    "overview": "Case Overview",
    "admission": "Admission & Assessment",
    "planning": "Care Planning",
    "discharge": "Discharge Planning",
    "hha": "Home Health Agency Coordination",
    "transition": "Transition Home",
    "followup": "Follow-up"
}

# Initialize session state for form data
if 'full_answers' not in st.session_state:
    st.session_state.full_answers = {qid: "" for qid in FULL_QUESTIONS}
if 'full_audio' not in st.session_state:
    st.session_state.full_audio = {qid: None for qid in FULL_QUESTIONS}
if 'full_transcripts' not in st.session_state:
    st.session_state.full_transcripts = {qid: None for qid in FULL_QUESTIONS}

# Title
st.title("📋 Full Intake")
st.markdown(f"""
Logged in as: **{get_current_username()}**

This comprehensive form captures detailed information about the entire patient journey.
All questions are in **past tense** — please describe what happened in completed cases.

You can **type** your answers or **record audio** which will be automatically transcribed.

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
        key="full_age"
    )

    gender = st.selectbox(
        "Gender",
        options=[""] + GENDER_OPTIONS,
        index=0,
        help="Patient's gender",
        key="full_gender"
    )

with col2:
    race = st.selectbox(
        "Race",
        options=[""] + RACE_OPTIONS,
        index=0,
        help="Patient's race/ethnicity",
        key="full_race"
    )

    state = st.selectbox(
        "SNF State",
        options=[""] + US_STATES,
        index=0,
        help="State where the SNF is located",
        key="full_state"
    )

st.markdown("---")

# Section 2: Narrative Questions with Audio Support (organized by section)
st.header("2. Case Narrative")
st.markdown("*Answer by typing or recording audio. Audio will be transcribed automatically.*")

# Group questions by section
current_section = None
for qid, question in FULL_QUESTIONS.items():
    section = question["section"]

    # Add section header when section changes
    if section != current_section:
        current_section = section
        st.markdown("---")
        st.subheader(f"📌 {SECTIONS[section]}")

    # Question
    st.markdown(f"**{question['label']}** *(ID: {qid})*")
    st.markdown(f"*{question['prompt']}*")

    # Input method selector
    input_method = st.radio(
        f"Answer method:",
        ["Type", "Record Audio"],
        key=f"method_{qid}",
        horizontal=True,
        label_visibility="collapsed"
    )

    if input_method == "Record Audio":
        # Audio recording
        audio_value = st.audio_input(
            f"Record your answer",
            key=f"audio_{qid}"
        )

        if audio_value is not None:
            audio_bytes = audio_value.read()
            st.session_state.full_audio[qid] = audio_bytes
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ Audio recorded!")
            # Mark that this question has audio
            if not st.session_state.full_answers[qid]:
                st.session_state.full_answers[qid] = "[Audio response]"
        else:
            # Check if audio was previously recorded
            if st.session_state.full_audio.get(qid):
                st.info("Audio previously recorded.")
    else:
        # Text input
        text_answer = st.text_area(
            "Type your answer:",
            value=st.session_state.full_answers[qid],
            height=120,
            help=question["help"],
            key=f"text_{qid}",
            label_visibility="collapsed"
        )
        st.session_state.full_answers[qid] = text_answer

st.markdown("---")

# Section 3: Services and SNF Days
st.header("3. Services & Duration")

col1, col2 = st.columns(2)

with col1:
    services_discussed = st.text_area(
        "Services Discussed",
        height=100,
        help="List all services that were discussed with the patient/family",
        placeholder="e.g., Physical therapy, occupational therapy, home health aide, meal delivery, medication management...",
        key="full_services_discussed"
    )

with col2:
    services_accepted = st.text_area(
        "Services Accepted",
        height=100,
        help="List which services the patient/family agreed to accept",
        placeholder="e.g., Physical therapy 3x/week, home health aide daily, medication delivery...",
        key="full_services_accepted"
    )

snf_days = st.number_input(
    "How many days was the patient in the SNF?",
    min_value=0,
    max_value=365,
    value=None,
    help="Total number of days from admission to discharge",
    key="full_snf_days"
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
                intake_version="full",
                user_name=user_name,
                age_at_snf_stay=int(age),
                gender=gender,
                race=race,
                state=state,
                snf_days=int(snf_days) if snf_days is not None else None,
                services_discussed=services_discussed if services_discussed else None,
                services_accepted=services_accepted if services_accepted else None,
                answers=st.session_state.full_answers
            )

            # Save audio responses for questions that have audio
            for qid in FULL_QUESTIONS:
                audio_data = st.session_state.full_audio.get(qid)
                auto_transcript = st.session_state.full_transcripts.get(qid)

                # Auto-transcribe audio for admin review (user doesn't see this)
                if audio_data and not auto_transcript:
                    try:
                        auto_transcript = transcribe_audio(audio_data)
                        if auto_transcript:
                            st.session_state.full_transcripts[qid] = auto_transcript
                    except Exception:
                        pass  # Continue saving even if transcription fails

                if audio_data or auto_transcript:
                    save_audio_response(
                        case_id=case_id,
                        question_id=qid,
                        audio_data=audio_data,
                        auto_transcript=auto_transcript,
                        edited_transcript=None  # User doesn't edit transcript anymore
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
                    intake_version="full",
                    demographics=demographics,
                    services=services,
                    answers=st.session_state.full_answers
                )

                if success and questions:
                    # Store questions in database
                    create_follow_up_questions(case_id, questions)
                    st.success(f"✅ Generated {len(questions)} follow-up questions!")
                    st.info("📋 Go to **Follow-On Questions** page to answer them.")
                    # Store case_id for redirect
                    st.session_state.last_saved_case_id = case_id
                else:
                    st.warning(f"⚠️ Could not generate follow-up questions: {error_msg}")
                    st.info("You can still view your case in the **Case Viewer**.")

            # Clear form data
            st.session_state.full_answers = {qid: "" for qid in FULL_QUESTIONS}
            st.session_state.full_audio = {qid: None for qid in FULL_QUESTIONS}
            st.session_state.full_transcripts = {qid: None for qid in FULL_QUESTIONS}

        except Exception as e:
            st.error(f"❌ Error saving case: {str(e)}")

# Sidebar info
with st.sidebar:
    st.markdown("### Full Intake")
    st.markdown(f"**User:** {get_current_username()}")
    st.markdown("""
    This comprehensive form captures:
    - Patient demographics
    - Case overview & referral
    - Admission & assessment details
    - Care planning process
    - Discharge planning
    - HHA coordination
    - Transition home
    - Follow-up outcomes
    """)

    st.markdown("---")
    st.markdown("### Question Sections")
    for section_id, section_name in SECTIONS.items():
        count = sum(1 for q in FULL_QUESTIONS.values() if q["section"] == section_id)
        st.markdown(f"- **{section_name}**: {count} questions")

    st.markdown("---")
    st.markdown("### Audio Recording")
    current_model = get_setting("whisper_model_size", "base")
    st.markdown(f"**Whisper Model:** {current_model}")
    st.markdown("""
    - Select **Record Audio** for any question
    - Audio is automatically transcribed on save
    - All recordings are saved
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Answer in **past tense**
    - Be as detailed as possible
    - All demographics are required
    - Use scroll to navigate sections
    """)
