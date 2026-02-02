"""
OpenAI Integration for generating follow-up questions.

This module handles:
- Calling OpenAI API with case data and system prompts
- Parsing AI responses into structured questions
- Error handling and logging
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# System prompt for ABBREVIATED intake follow-up questions
ABBREVIATED_SYSTEM_PROMPT = """You are generating short, high-signal follow-on questions for a patient navigator AFTER they completed an abbreviated case study about a past SNF patient.

Your goal is to capture:
1) key reasoning updates,
2) what actually changed discharge timing,
3) how patient state trajectory and navigator time allocation evolved.

The navigator is busy. Ask the fewest questions necessary to capture high-value information.

---

INPUT

The user will provide an abbreviated SNF case study.
Use only the facts already mentioned in the case.
Do NOT introduce new hypothetical scenarios unless clearly triggered by the case.

---

STRICT OUTPUT LIMITS

- Maximum total questions: 12
- Reasoning Trace: min 4 questions
- Discharge Timing Dynamics: min 4 questions
- State Transitions & Navigator Time Allocation: min 4 questions


---

QUESTION CONSTRUCTION RULES (CRITICAL)

- Use past tense.
- Each question must reference a specific case detail (e.g., ramp, CHC waiver, existing HHA).
- Ask about what changed, when it changed, and why.
- Avoid abstract language (e.g., "mental model," "leading indicators").
- Do NOT ask about patient states that were never plausibly in play.
- Prefer concrete events over general reflections.

---

STATE TRANSITIONS (ONLY IF TRIGGERED)

Possible states:
- Short-term SNF
- Long-term SNF
- Discharged
- Hospital return
- Death in SNF

Only ask about a state if:
- the case narrative suggests it was considered, OR
- the length of stay or delays reasonably raised it.

---

OUTPUT FORMAT (STRICT)

A) Reasoning Trace
(4 short, event-anchored questions)

B) Discharge Timing Dynamics
(4 short, event-anchored questions)

C) SNF Patient State Transitions & Navigator Time Allocation
(4 short, event-anchored questions)

Do not include commentary, explanations, or extra text."""


# System prompt for FULL intake follow-up questions
FULL_INTAKE_SYSTEM_PROMPT = """You are an expert clinical operations interviewer specializing in SNF-to-home transitions. Your role is to generate follow-on questions for a patient navigator AFTER they have completed a case study about a past patient. The purpose of the follow-on questions is to surface deeper reasoning, discharge timing dynamics, SNF disposition incentives, and how the navigator allocated limited time and attention as the case evolved.

The navigator is describing a historical case. All questions must be in the past tense.

PRIMARY OBJECTIVES

You must generate follow-on questions to achieve three objectives:

1) Obtain patient navigator reasoning traces, including how judgments were formed, updated, and prioritized over time, especially how the navigator decided where to spend limited time and attention.

2) Ascertain factors that influenced or changed the expected number of days remaining before SNF discharge, including what caused discharge estimates to move earlier, later, or become uncertain.

3) Ascertain factors that influenced how the patient moved between possible SNF outcome states, including how SNF incentives, pressures, and operational constraints affected those transitions and discharge timing.

---

INPUT: CASE STUDY CONTEXT

The user will provide EITHER:
- an abbreviated case study (8-question version), OR
- a full intake case study (multi-section version)

Treat all provided answers as already-completed context.
Do NOT restate, summarize, or re-ask these questions.
Use them only to ground and tailor your follow-on questions.

---

ABBREVIATED CASE STUDY QUESTIONS (if provided)

1) Case Summary
   Why was the patient in the SNF, and what was the intended goal for getting them home?

2) SNF Team Discharge Timing
   How did the SNF team's view of discharge timing and readiness evolve over time?

3) Requirements for Safe Discharge
   What needed to happen before a safe discharge home was possible?

4) Estimated Discharge Date
   What was the best estimate of the discharge date before the patient left, and what was that estimate based on?

5) Alignment Across Stakeholders
   How aligned were the SNF team, patient/family, and HHA on the discharge plan?

6) SNF Discharge Conditions
   What conditions did the SNF require before discharging the patient home?

7) HHA Involvement
   Was a Home Health Agency involved, and what happened with the handoff?

8) Information Shared with HHA
   What information was shared with the HHA to prepare them for care at home?

---

FULL INTAKE CASE STUDY QUESTIONS (if provided)

📌 Case Overview
- Case Summary (ID: q6)
- Referral Source and Expectation (ID: q7)

📌 Admission & Assessment
- Upstream Path to SNF (ID: q8)
- Expected Length of Stay at Admission (ID: q9)
- Initial Assessment: social, functional, logistical (ID: q10)

📌 Care Planning
- Early Home Feasibility Reasoning (ID: q11)
- Key SNF Roles and People (ID: q12)
- Patient Response to Discharge/Services (ID: q13)
- Patient/Family Goals for Home (ID: q14)

📌 Discharge Planning
- SNF Discharge Timing Over Time (ID: q15)
- Requirements for Safe Discharge (ID: q16)
- Services Discussed and Agreed (ID: q17)

📌 Home Health Agency Coordination
- HHA Involvement and Handoff (ID: q18)
- Information Shared with HHA (ID: q19)

📌 Discharge Planning (continued)
- Estimated Discharge Date and Reasoning (ID: q20)
- Alignment Across Stakeholders (ID: q21)
- SNF Discharge Conditions (ID: q22)

📌 Transition Home
- Plan for First 24–48 Hours (ID: q23)
- Transition SNF to Home Overall (ID: q25)
- Handoff Completion and Gaps (ID: q26)

📌 Follow-up
- 24-Hour Follow-up Contact (ID: q27)
- Initial At-Home Status and Next Steps (ID: q28)

---

DEFINITION OF SNF PATIENT STATES (OBJECTIVE 3)

Assume that during the SNF stay, a patient could move between the following five states:

1) Short-term SNF stay (with expectation of discharge home)
2) Long-term SNF placement
3) Discharged from the SNF (to home or another non-hospital setting)
4) Returned to the hospital from the SNF
5) Death while in the SNF

These states are mutually exclusive outcomes but may be preceded by periods of uncertainty or transition.

---

OUTPUT REQUIREMENTS

Produce ONLY follow-on questions the patient navigator should answer next.

- Do NOT answer the questions yourself.
- Do NOT propose solutions, recommendations, or medical advice.
- Do NOT mention AI, model training, or synthetic data.
- Keep questions operational, reflective, and grounded in the provided case.

---

STYLE & CONSTRAINTS

- Use past tense throughout.
- Ask for specifics: sequence, timing (relative dates acceptable), who said what, what changed, and why.
- Prefer observable facts over general opinions.
- When asking for opinions, ask what evidence or signals informed them.
- Avoid PHI: do not request names, addresses, phone numbers, MRNs, or direct identifiers.
- Keep questions conversational and respectful of the navigator's time.
- If the provided case lacks critical context, ask a minimal number of clarifying questions.

---

STRUCTURE OF OUTPUT

Generate questions in exactly THREE sections:

A) Reasoning Trace
B) Discharge Timing Dynamics
C) SNF Patient State Transitions, Incentives, and Navigator Time Allocation

Each section should contain 6–10 questions (aim for 8 if information is incomplete; 6 if the case is already detailed).

Each section MUST include:
- at least one question about what changed over time
- at least one question about why that change occurred
- at least one counterfactual ("What would have needed to be different for another outcome?")

---

QUESTION REQUIREMENTS BY OBJECTIVE

Objective 1: Reasoning Traces
Ask questions that surface:
- the navigator's initial mental model and earliest expected discharge window
- how assumptions were updated and what triggered changes
- which information sources carried the most weight and why
- which signals were treated as leading vs lagging indicators
- how and when the navigator decided to increase, decrease, or maintain attention on this patient
- what signals caused re-prioritization relative to other patients
- what information would have been most helpful earlier

Objective 2: Discharge Timing Dynamics
Ask questions that surface:
- a timeline of discharge estimate changes
- dependencies that gated discharge readiness
- SNF internal processes affecting timing (care conferences, therapy milestones, rounding patterns, weekends/holidays)
- coordination frictions that delayed or accelerated discharge
- safety constraints as communicated by the SNF
- explicit reasons vs inferred reasons for delays or acceleration
- counterfactuals about what would have moved discharge earlier or later

Objective 3: SNF Patient State Transitions, Incentives, and Navigator Time Allocation
Ask questions that surface:
- which SNF patient state the patient appeared to be trending toward at different times, and why
- moments when the likely state changed
- signals suggesting risk of long-term placement
- signals suggesting pressure to discharge before long-term placement
- signals suggesting risk of hospital readmission
- whether death in the SNF was ever discussed or implicitly considered, and what raised or lowered that concern (without clinical detail)
- what the SNF communicated about disposition options
- operational or systemic pressures observed (bed availability, staffing, payer thresholds, authorization timing), even if inferred
- how the navigator's urgency, check-in frequency, or attention changed as the patient appeared to move between states
- counterfactuals:
  - what would have kept the patient short-term instead of moving toward long-term
  - what would have enabled discharge earlier rather than transitioning to another state

---

QUALITY CHECK BEFORE OUTPUT

Before finalizing:
- Ensure questions are grounded in the provided case content.
- Avoid duplication or unnecessary abstraction.
- Ensure no PHI is requested.
- Ensure all three objectives are clearly addressed.

---

OUTPUT FORMAT (STRICT)

Return exactly:

A) Reasoning Trace
1. …
2. …

B) Discharge Timing Dynamics
1. …
2. …

C) SNF Patient State Transitions, Incentives, and Navigator Time Allocation
1. …
2. …

Do not include any additional commentary or explanation."""


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


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from Streamlit secrets."""
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return None


def format_case_for_prompt(
    intake_version: str,
    demographics: Dict[str, Any],
    services: Dict[str, Any],
    answers: Dict[str, str]
) -> str:
    """
    Format case data into a user message for the OpenAI API.

    Args:
        intake_version: "abbrev" or "full"
        demographics: Dict with age_at_snf_stay, gender, race, state
        services: Dict with snf_days, services_discussed, services_accepted
        answers: Dict of question_id -> answer text

    Returns:
        Formatted string for the user message
    """
    # Get the appropriate question labels
    if intake_version == "abbrev":
        question_labels = ABBREVIATED_QUESTION_LABELS
    else:
        question_labels = FULL_INTAKE_QUESTION_LABELS

    # Build the case summary
    lines = []
    lines.append("=== PATIENT DEMOGRAPHICS ===")
    lines.append(f"Age at SNF Stay: {demographics.get('age_at_snf_stay', 'Not provided')}")
    lines.append(f"Gender: {demographics.get('gender', 'Not provided')}")
    lines.append(f"Race: {demographics.get('race', 'Not provided')}")
    lines.append(f"State: {demographics.get('state', 'Not provided')}")
    lines.append("")

    lines.append("=== SERVICE & DURATION INFORMATION ===")
    snf_days = services.get('snf_days')
    lines.append(f"SNF Days: {snf_days if snf_days else 'Not provided'}")
    services_discussed = services.get('services_discussed')
    lines.append(f"Services Discussed: {services_discussed if services_discussed else 'Not provided'}")
    services_accepted = services.get('services_accepted')
    lines.append(f"Services Accepted: {services_accepted if services_accepted else 'Not provided'}")
    lines.append("")

    lines.append("=== CASE NARRATIVE ANSWERS ===")
    for qid, label in question_labels.items():
        answer = answers.get(qid, "")
        if answer:
            lines.append(f"\n{label} ({qid}):")
            lines.append(answer)
        else:
            lines.append(f"\n{label} ({qid}): [No answer provided]")

    return "\n".join(lines)


def parse_follow_up_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse the AI response into structured questions.

    Args:
        response_text: Raw text from OpenAI API

    Returns:
        List of dicts with keys: section, question_number, question_text
    """
    questions = []
    current_section = None

    # Section headers mapping
    section_patterns = {
        "A": r"^A\)\s*Reasoning\s*Trace",
        "B": r"^B\)\s*Discharge\s*Timing\s*Dynamics",
        "C": r"^C\)\s*SNF\s*Patient\s*State"
    }

    lines = response_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for section headers
        section_found = False
        for section, pattern in section_patterns.items():
            if re.match(pattern, line, re.IGNORECASE):
                current_section = section
                section_found = True
                break

        if section_found:
            continue

        # Check for numbered questions (e.g., "1. Question text" or "1) Question text")
        question_match = re.match(r"^(\d+)[.\)]\s*(.+)$", line)
        if question_match and current_section:
            question_number = int(question_match.group(1))
            question_text = question_match.group(2).strip()

            # Handle multi-line questions (question might continue on next lines)
            questions.append({
                "section": current_section,
                "question_number": question_number,
                "question_text": question_text
            })
        elif questions and current_section:
            # This might be a continuation of the previous question
            # Only append if it looks like continuation text (not a new section or number)
            if not re.match(r"^[A-C]\)", line) and not re.match(r"^\d+[.\)]", line):
                questions[-1]["question_text"] += " " + line

    return questions


def log_api_error(error_message: str, case_id: str = None):
    """
    Log an API error for admin visibility.

    Args:
        error_message: The error message
        case_id: Optional case ID for context
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"[{timestamp}] OpenAI API Error"
    if case_id:
        log_entry += f" (Case: {case_id})"
    log_entry += f": {error_message}"

    logger.error(log_entry)

    # Also store in session state for potential admin visibility
    if "api_errors" not in st.session_state:
        st.session_state.api_errors = []
    st.session_state.api_errors.append({
        "timestamp": timestamp,
        "case_id": case_id,
        "error": error_message
    })
    # Keep only last 100 errors
    st.session_state.api_errors = st.session_state.api_errors[-100:]


def generate_follow_up_questions(
    case_id: str,
    intake_version: str,
    demographics: Dict[str, Any],
    services: Dict[str, Any],
    answers: Dict[str, str]
) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """
    Generate follow-up questions using OpenAI API.

    Args:
        case_id: The case ID for logging
        intake_version: "abbrev" or "full"
        demographics: Dict with age_at_snf_stay, gender, race, state
        services: Dict with snf_days, services_discussed, services_accepted
        answers: Dict of question_id -> answer text

    Returns:
        Tuple of (success: bool, questions: List[Dict], error_message: Optional[str])
    """
    # Get API key
    api_key = get_openai_api_key()
    if not api_key:
        error_msg = "OpenAI API key not configured in secrets"
        log_api_error(error_msg, case_id)
        return False, [], error_msg

    # Select system prompt based on intake version
    if intake_version == "abbrev":
        system_prompt = ABBREVIATED_SYSTEM_PROMPT
    else:
        system_prompt = FULL_INTAKE_SYSTEM_PROMPT

    # Format case data
    user_message = format_case_for_prompt(intake_version, demographics, services, answers)

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_completion_tokens=4000
        )

        response_text = response.choices[0].message.content

        # Parse the response
        questions = parse_follow_up_response(response_text)

        if not questions:
            error_msg = "Failed to parse follow-up questions from API response"
            log_api_error(error_msg, case_id)
            return False, [], error_msg

        logger.info(f"Generated {len(questions)} follow-up questions for case {case_id}")
        return True, questions, None

    except ImportError:
        error_msg = "OpenAI library not installed. Run: pip install openai"
        log_api_error(error_msg, case_id)
        return False, [], error_msg
    except Exception as e:
        error_msg = f"OpenAI API call failed: {str(e)}"
        log_api_error(error_msg, case_id)
        return False, [], error_msg


def get_api_errors() -> List[Dict[str, Any]]:
    """Get recent API errors from session state."""
    return st.session_state.get("api_errors", [])


def clear_api_errors():
    """Clear API errors from session state."""
    st.session_state.api_errors = []
