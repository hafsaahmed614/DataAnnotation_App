"""
SNF Patient Navigator Case Collection - Abbreviated Intake Page

Shorter intake form capturing essential case information with conversational
narrative prompts. Supports both typed and audio-recorded answers.
Includes auto-save and session timeout handling.
"""

import streamlit as st
import json
from db import (
    create_case, save_audio_response, init_db, get_setting, create_follow_up_questions,
    save_draft_case, get_draft_case, delete_draft_case, has_draft_case
)
from auth import require_auth, get_current_username, init_session_state
from openai_integration import generate_follow_up_questions
from session_timer import (
    init_session_timer, update_activity_time, should_auto_save, mark_auto_saved,
    render_session_timer_warning, render_auto_save_status, render_resume_draft_banner
)

# Page configuration
st.set_page_config(
    page_title="Abbreviated Intake | SNF Navigator",
    page_icon="📝",
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

# Initialize session timer and update activity (page reruns on user interaction)
init_session_timer()
update_activity_time()

# Get current username for draft operations
current_user = get_current_username()

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

# Sample case data for demo purposes
SAMPLE_CASE_DATA = {
    "demographics": {
        "age": 65,
        "gender": "Male",
        "race": "White",
        "state": "Pennsylvania"
    },
    "services": {
        "snf_days": 90,
        "services_discussed": "In home wound care services",
        "services_accepted": "In home wound care services"
    },
    "answers": {
        "aq1": "Patient was admitted to a SNF for short-term skilled care following hospital discharge. He required physical therapy after a recent leg amputation, while also receiving ongoing wound care on his remaining leg. The primary goal was for him to return home to his wife once physical therapy was completed and his wounds had sufficiently healed. Upon discharge, the plan was to arrange in-home wound care services once a week and home health visits three times per week.",
        "aq2": "SNF social worker identified the patient as short-term, planning discharge after physical therapy and wound healing. However, discharge timing changed due to the need for a wheelchair ramp at home. With a CHC waiver, insurance covered home modifications, but discharge was delayed until ramp installation was completed. This pushed back the discharged date by a month and half",
        "aq3": "To ensure a safe discharge, the patient needed a ramp installed at home, home health set up and ready to start with 24 hours after discharge, and the agreed upon in home wound care services in place and first appointment scheduled.",
        "aq4": "At the first meeting with the social worker and patient, there wasn't a firm discharge date but rather an expectation of a couple weeks. This timeline was based on his physical therapy progress and healing wounds. Once ramp was ready, he could discharge.",
        "aq5": "While the patient was still in the facility, the SNF team, family, home health, and wound care providers were all on the same page. This coordination ahead of time made for a smooth transition back to his residence.",
        "aq6": "The SNF required that the patient's wounds were healing, in-home wound care was arranged, and home health services were ready before discharging home",
        "aq7": "HHA was already established for the patient before his stay at the SNF, since he'd had it following his leg amputation. The HHA was OSTPA and they were ready to see him within 24 hours of discharge and start services right away.",
        "aq8": "The HHA was given the contact information for the in-home wound care provider, allowing them to coordinate directly and share any needed updates. In addition, the HHA received facility records and the discharge summary to support the home care plan."
    }
}

# Users allowed to access the demo feature (Load Sample Case button)
DEMO_ALLOWED_USERS = [
    "Hafsa Ahmed",
    "Mohsin Ansari",
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

# Initialize draft-related session state
if 'abbrev_draft_checked' not in st.session_state:
    st.session_state.abbrev_draft_checked = False
if 'abbrev_draft_loaded' not in st.session_state:
    st.session_state.abbrev_draft_loaded = False
if 'abbrev_demographics' not in st.session_state:
    st.session_state.abbrev_demographics = {
        'age': None,
        'gender': '',
        'race': '',
        'state': '',
        'snf_name': ''
    }
if 'abbrev_services' not in st.session_state:
    st.session_state.abbrev_services = {
        'snf_days': None,
        'services_discussed': '',
        'services_accepted': '',
        'services_utilized_after_discharge': ''
    }

# Check if sample case load was requested (must happen before widgets are created)
if st.session_state.get('load_sample_case_requested', False):
    # Load demographics
    st.session_state.abbrev_demographics = {
        'age': SAMPLE_CASE_DATA["demographics"]["age"],
        'gender': SAMPLE_CASE_DATA["demographics"]["gender"],
        'race': SAMPLE_CASE_DATA["demographics"]["race"],
        'state': SAMPLE_CASE_DATA["demographics"]["state"]
    }
    # Set widget keys for demographics
    st.session_state.abbrev_age = SAMPLE_CASE_DATA["demographics"]["age"]
    st.session_state.abbrev_gender = SAMPLE_CASE_DATA["demographics"]["gender"]
    st.session_state.abbrev_race = SAMPLE_CASE_DATA["demographics"]["race"]
    st.session_state.abbrev_state = SAMPLE_CASE_DATA["demographics"]["state"]
    # Load services
    st.session_state.abbrev_services = {
        'snf_days': SAMPLE_CASE_DATA["services"]["snf_days"],
        'services_discussed': SAMPLE_CASE_DATA["services"]["services_discussed"],
        'services_accepted': SAMPLE_CASE_DATA["services"]["services_accepted"]
    }
    # Set widget keys for services
    st.session_state.abbrev_snf_days = SAMPLE_CASE_DATA["services"]["snf_days"]
    st.session_state.abbrev_services_discussed = SAMPLE_CASE_DATA["services"]["services_discussed"]
    st.session_state.abbrev_services_accepted = SAMPLE_CASE_DATA["services"]["services_accepted"]
    # Load answers
    for qid, answer_text in SAMPLE_CASE_DATA["answers"].items():
        st.session_state.abbrev_answers[qid] = answer_text
        st.session_state[f"text_{qid}"] = answer_text
    # Clear the flag
    st.session_state.load_sample_case_requested = False


def save_current_draft():
    """Save current form state as draft."""
    try:
        # Get audio flags (which questions have audio)
        audio_flags = {qid: bool(st.session_state.abbrev_audio.get(qid))
                       for qid in ABBREV_QUESTIONS}

        save_draft_case(
            user_name=current_user,
            intake_version="abbrev",
            age_at_snf_stay=st.session_state.abbrev_demographics.get('age'),
            gender=st.session_state.abbrev_demographics.get('gender') or None,
            race=st.session_state.abbrev_demographics.get('race') or None,
            state=st.session_state.abbrev_demographics.get('state') or None,
            snf_name=st.session_state.abbrev_demographics.get('snf_name') or None,
            snf_days=st.session_state.abbrev_services.get('snf_days'),
            services_discussed=st.session_state.abbrev_services.get('services_discussed') or None,
            services_accepted=st.session_state.abbrev_services.get('services_accepted') or None,
            services_utilized_after_discharge=st.session_state.abbrev_services.get('services_utilized_after_discharge') or None,
            answers=st.session_state.abbrev_answers,
            audio_flags=audio_flags
        )
        return True
    except Exception as e:
        st.error(f"Failed to save draft: {str(e)}")
        return False


def load_draft_to_session(draft):
    """Load draft data into session state."""
    # Load demographics
    st.session_state.abbrev_demographics = {
        'age': draft.age_at_snf_stay,
        'gender': draft.gender or '',
        'race': draft.race or '',
        'state': draft.state or '',
        'snf_name': getattr(draft, 'snf_name', '') or ''
    }

    # Also set the widget keys directly so Streamlit uses these values
    if draft.age_at_snf_stay is not None:
        st.session_state.abbrev_age = draft.age_at_snf_stay
    if draft.gender:
        st.session_state.abbrev_gender = draft.gender
    if draft.race:
        st.session_state.abbrev_race = draft.race
    if draft.state:
        st.session_state.abbrev_state = draft.state
    if getattr(draft, 'snf_name', None):
        st.session_state.abbrev_snf_name = draft.snf_name

    # Load services
    st.session_state.abbrev_services = {
        'snf_days': draft.snf_days,
        'services_discussed': draft.services_discussed or '',
        'services_accepted': draft.services_accepted or '',
        'services_utilized_after_discharge': getattr(draft, 'services_utilized_after_discharge', '') or ''
    }

    # Also set service widget keys
    if draft.snf_days is not None:
        st.session_state.abbrev_snf_days = draft.snf_days
    if draft.services_discussed:
        st.session_state.abbrev_services_discussed = draft.services_discussed
    if draft.services_accepted:
        st.session_state.abbrev_services_accepted = draft.services_accepted
    if getattr(draft, 'services_utilized_after_discharge', None):
        st.session_state.abbrev_services_utilized = draft.services_utilized_after_discharge

    # Load answers - set both the dict and the individual widget keys
    answers = json.loads(draft.answers_json) if draft.answers_json else {}
    for qid in ABBREV_QUESTIONS:
        answer_text = answers.get(qid, "")
        st.session_state.abbrev_answers[qid] = answer_text
        # Set the text area widget key directly
        st.session_state[f"text_{qid}"] = answer_text

    st.session_state.abbrev_draft_loaded = True


def clear_form_state():
    """Clear all form state for fresh start."""
    st.session_state.abbrev_answers = {qid: "" for qid in ABBREV_QUESTIONS}
    st.session_state.abbrev_audio = {qid: None for qid in ABBREV_QUESTIONS}
    st.session_state.abbrev_demographics = {
        'age': None,
        'gender': '',
        'race': '',
        'state': '',
        'snf_name': ''
    }
    st.session_state.abbrev_services = {
        'snf_days': None,
        'services_discussed': '',
        'services_accepted': '',
        'services_utilized_after_discharge': ''
    }
    st.session_state.abbrev_draft_loaded = False

    # Clear widget keys to ensure fresh form
    for key in ['abbrev_age', 'abbrev_gender', 'abbrev_race', 'abbrev_state', 'abbrev_snf_name',
                'abbrev_snf_days', 'abbrev_services_discussed', 'abbrev_services_accepted',
                'abbrev_services_utilized']:
        if key in st.session_state:
            del st.session_state[key]
    # Clear text area widget keys
    for qid in ABBREV_QUESTIONS:
        if f"text_{qid}" in st.session_state:
            del st.session_state[f"text_{qid}"]


# Check for existing draft on first load
if not st.session_state.abbrev_draft_checked:
    existing_draft = get_draft_case(current_user, "abbrev")
    if existing_draft:
        st.session_state.abbrev_pending_draft = existing_draft
    st.session_state.abbrev_draft_checked = True

# Title
st.title("📝 Abbreviated Intake")

# Session timeout warning (if applicable)
render_session_timer_warning()

# Handle pending draft - show resume/discard banner
if hasattr(st.session_state, 'abbrev_pending_draft') and st.session_state.abbrev_pending_draft and not st.session_state.abbrev_draft_loaded:
    draft = st.session_state.abbrev_pending_draft

    resume_clicked, discard_clicked = render_resume_draft_banner(draft, "Abbreviated")

    if resume_clicked:
        load_draft_to_session(draft)
        st.session_state.abbrev_pending_draft = None
        st.rerun()
    elif discard_clicked:
        delete_draft_case(current_user, "abbrev")
        clear_form_state()
        st.session_state.abbrev_pending_draft = None
        st.rerun()

st.markdown(f"""
Logged in as: **{get_current_username()}**

This form captures essential case information through a brief set of questions.
All questions are in **past tense** — please describe what happened in completed cases.

You can **type** your answers or **record audio**.

*Case start date is automatically set to January 1, 2025.*
""")
st.markdown("---")

# Auto-save status indicator
render_auto_save_status()

# Section 1: Demographics
st.header("1. Patient Demographics")
st.markdown("*All demographic fields are required.*")

col1, col2 = st.columns(2)

# Initialize widget keys if not already set (fresh form)
if 'abbrev_age' not in st.session_state:
    st.session_state.abbrev_age = st.session_state.abbrev_demographics.get('age')
if 'abbrev_gender' not in st.session_state:
    default_gender = st.session_state.abbrev_demographics.get('gender', '')
    st.session_state.abbrev_gender = default_gender if default_gender in GENDER_OPTIONS else ""
if 'abbrev_race' not in st.session_state:
    default_race = st.session_state.abbrev_demographics.get('race', '')
    st.session_state.abbrev_race = default_race if default_race in RACE_OPTIONS else ""
if 'abbrev_state' not in st.session_state:
    default_state = st.session_state.abbrev_demographics.get('state', '')
    st.session_state.abbrev_state = default_state if default_state in US_STATES else ""
if 'abbrev_snf_name' not in st.session_state:
    st.session_state.abbrev_snf_name = st.session_state.abbrev_demographics.get('snf_name', '')

with col1:
    age = st.number_input(
        "Age at SNF Stay",
        min_value=0,
        max_value=120,
        help="Patient's age in years during the SNF stay",
        placeholder="Enter age...",
        key="abbrev_age"
    )

    gender = st.selectbox(
        "Gender",
        options=[""] + GENDER_OPTIONS,
        help="Patient's gender",
        key="abbrev_gender"
    )

with col2:
    race = st.selectbox(
        "Race",
        options=[""] + RACE_OPTIONS,
        help="Patient's race/ethnicity",
        key="abbrev_race"
    )

    state = st.selectbox(
        "SNF State",
        options=[""] + US_STATES,
        help="State where the SNF is located",
        key="abbrev_state"
    )

# SNF Name field (full width)
snf_name = st.text_input(
    "SNF Name",
    help="Name of the Skilled Nursing Facility",
    placeholder="Enter the name of the SNF...",
    key="abbrev_snf_name"
)

# Update session state demographics for draft saving
st.session_state.abbrev_demographics['age'] = age
st.session_state.abbrev_demographics['gender'] = gender
st.session_state.abbrev_demographics['race'] = race
st.session_state.abbrev_demographics['state'] = state
st.session_state.abbrev_demographics['snf_name'] = snf_name

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
            # Use the file's actual MIME type for playback (browsers record in WebM, not WAV)
            st.audio(audio_bytes, format=audio_value.type if hasattr(audio_value, 'type') else "audio/webm")
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
            height=120,
            help=question["help"],
            key=f"text_{qid}",
            label_visibility="collapsed"
        )
        st.session_state.abbrev_answers[qid] = text_answer

    st.markdown("---")

# Section 3: Services and SNF Days
st.header("3. Services & Duration")

# Initialize widget keys if not already set (fresh form)
if 'abbrev_services_discussed' not in st.session_state:
    st.session_state.abbrev_services_discussed = st.session_state.abbrev_services.get('services_discussed', '')
if 'abbrev_services_accepted' not in st.session_state:
    st.session_state.abbrev_services_accepted = st.session_state.abbrev_services.get('services_accepted', '')
if 'abbrev_snf_days' not in st.session_state:
    st.session_state.abbrev_snf_days = st.session_state.abbrev_services.get('snf_days')
if 'abbrev_services_utilized' not in st.session_state:
    st.session_state.abbrev_services_utilized = st.session_state.abbrev_services.get('services_utilized_after_discharge', '')

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
    help="Total number of days from admission to discharge",
    key="abbrev_snf_days"
)

services_utilized_after_discharge = st.text_area(
    "Did the patient utilize the discussed services after discharge? If no, please explain why.",
    height=100,
    help="Describe whether the patient used the services after leaving the SNF and any reasons if they did not",
    placeholder="e.g., Yes, patient utilized all services as planned. / No, patient declined home health due to...",
    key="abbrev_services_utilized"
)

# Update session state services for draft saving
st.session_state.abbrev_services['snf_days'] = snf_days
st.session_state.abbrev_services['services_discussed'] = services_discussed
st.session_state.abbrev_services['services_accepted'] = services_accepted
st.session_state.abbrev_services['services_utilized_after_discharge'] = services_utilized_after_discharge

st.markdown("---")

# Auto-save check (trigger every 2 minutes)
if should_auto_save():
    if save_current_draft():
        mark_auto_saved()

# Buttons row: Save Draft and Save Case
col_draft, col_save = st.columns(2)

with col_draft:
    if st.button("📄 Save Draft", use_container_width=True):
        if save_current_draft():
            st.success("Draft saved successfully!")
            mark_auto_saved()

with col_save:
    save_case_clicked = st.button("💾 Save Case", use_container_width=True, type="primary")

if save_case_clicked:
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
            # Create case
            case_id = create_case(
                intake_version="abbrev",
                user_name=current_user,
                age_at_snf_stay=int(age),
                gender=gender,
                race=race,
                state=state,
                snf_name=snf_name if snf_name else None,
                snf_days=int(snf_days) if snf_days is not None else None,
                services_discussed=services_discussed if services_discussed else None,
                services_accepted=services_accepted if services_accepted else None,
                services_utilized_after_discharge=services_utilized_after_discharge if services_utilized_after_discharge else None,
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

            # Delete draft after successful case save
            delete_draft_case(current_user, "abbrev")

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
                    create_follow_up_questions(case_id, questions, current_user)
                    st.success(f"✅ Generated {len(questions)} follow-up questions!")
                    st.info("📋 Go to **Follow-On Questions** page to answer them.")
                    # Store case_id for redirect
                    st.session_state.last_saved_case_id = case_id
                else:
                    st.warning(f"⚠️ Could not generate follow-up questions: {error_msg}")
                    st.info("You can still view your case in the **Case Viewer**.")

            # Clear form data and draft state
            clear_form_state()
            st.session_state.abbrev_draft_checked = False

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

    # Only show Demo Mode for allowed users
    if current_user in DEMO_ALLOWED_USERS:
        st.markdown("---")
        st.markdown("### Demo Mode")
        if st.button("📋 Load Sample Case", use_container_width=True):
            st.session_state.load_sample_case_requested = True
            st.rerun()
        st.caption("Fills form with sample data for demo purposes. Review and click Save Case when ready.")

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
