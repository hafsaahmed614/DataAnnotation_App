"""
SNF Patient Navigator Case Collection - Abbreviated Intake Page

Shorter intake form capturing essential case information with conversational
narrative prompts. All questions are in past tense.
"""

import streamlit as st
from db import create_case, init_db

# Page configuration
st.set_page_config(
    page_title="Abbreviated Intake | SNF Navigator",
    page_icon="📝",
    layout="wide"
)

# Ensure database is initialized
init_db()

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

# Title
st.title("📝 Abbreviated Intake")
st.markdown("""
This form captures essential case information through a brief set of questions.
All questions are in **past tense** — please describe what happened in completed cases.

*Case start date is automatically set to January 1, 2025.*
""")
st.markdown("---")

# Form
with st.form("abbreviated_intake_form", clear_on_submit=False):
    
    # Section 0: User Identification
    st.header("0. Your Information")
    st.markdown("*Enter your ID number to associate this case with you.*")
    
    user_id = st.text_input(
        "Your ID Number",
        help="Enter your unique ID number. You'll need this to view your cases later.",
        placeholder="Enter your ID number..."
    )
    
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
            placeholder="Enter age..."
        )
        
        gender = st.selectbox(
            "Gender",
            options=[""] + GENDER_OPTIONS,
            index=0,
            help="Patient's gender"
        )
    
    with col2:
        race = st.selectbox(
            "Race",
            options=[""] + RACE_OPTIONS,
            index=0,
            help="Patient's race/ethnicity"
        )
        
        state = st.selectbox(
            "SNF State",
            options=[""] + US_STATES,
            index=0,
            help="State where the SNF is located"
        )
    
    st.markdown("---")
    
    # Section 2: Narrative Questions
    st.header("2. Case Narrative")
    st.markdown("*Please provide detailed responses to each question.*")
    
    answers = {}
    
    for qid, question in ABBREV_QUESTIONS.items():
        st.subheader(question["label"])
        answers[qid] = st.text_area(
            question["prompt"],
            height=120,
            help=question["help"],
            key=f"narrative_{qid}"
        )
    
    st.markdown("---")
    
    # Section 3: Services and SNF Days
    st.header("3. Services & Duration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        services_discussed = st.text_area(
            "Services Discussed",
            height=100,
            help="List all services that were discussed with the patient/family",
            placeholder="e.g., Physical therapy, occupational therapy, home health aide, meal delivery..."
        )
    
    with col2:
        services_accepted = st.text_area(
            "Services Accepted",
            height=100,
            help="List which services the patient/family agreed to accept",
            placeholder="e.g., Physical therapy 3x/week, home health aide..."
        )
    
    snf_days = st.number_input(
        "How many days was the patient in the SNF?",
        min_value=0,
        max_value=365,
        value=None,
        help="Total number of days from admission to discharge"
    )
    
    st.markdown("---")
    
    # Submit button
    submitted = st.form_submit_button("💾 Save Case", use_container_width=True, type="primary")
    
    if submitted:
        # Validation
        errors = []
        
        if not user_id or not user_id.strip():
            errors.append("Your ID Number is required")
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
                    user_id=user_id.strip(),
                    age_at_snf_stay=int(age),
                    gender=gender,
                    race=race,
                    state=state,
                    snf_days=int(snf_days) if snf_days is not None else None,
                    services_discussed=services_discussed if services_discussed else None,
                    services_accepted=services_accepted if services_accepted else None,
                    answers=answers
                )
                
                st.success(f"✅ Case saved successfully!")
                st.info(f"📋 **Case ID**: `{case_id}`")
                
                # Option to copy case ID
                st.code(case_id, language=None)
                st.caption("👆 Copy this Case ID to reference this case later in the Case Viewer.")
                
            except Exception as e:
                st.error(f"❌ Error saving case: {str(e)}")

# Sidebar info
with st.sidebar:
    st.markdown("### Abbreviated Intake")
    st.markdown("""
    This shorter form captures:
    - Your ID number
    - Patient demographics
    - Case summary
    - Discharge planning details
    - HHA coordination
    - Services discussed/accepted
    """)
    
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Enter your ID number first
    - Answer in **past tense**
    - Be as detailed as possible
    - All demographics are required
    - Narrative fields can be left blank if unknown
    """)