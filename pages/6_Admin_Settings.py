"""
SNF Patient Navigator Case Collection - Admin Settings Page

Allows administrators to configure application settings including
Whisper transcription model selection.
"""

import streamlit as st
from db import (
    init_db, get_setting, set_setting, get_whisper_settings,
    get_all_users, get_all_user_names, get_audio_responses_for_case,
    get_all_case_ids, get_case_by_id, get_follow_up_question_by_id
)
from auth import require_auth, get_current_username, init_session_state

# Page configuration
st.set_page_config(
    page_title="Admin Settings | SNF Navigator",
    page_icon="⚙️",
    layout="wide"
)

# Custom CSS to rename "app" to "Dashboard" in sidebar
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child a span {
        font-size: 0;
    }
    [data-testid="stSidebarNav"] li:first-child a span::after {
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

# Check admin password
def check_admin():
    """Check if user has entered admin password."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    return st.session_state.admin_authenticated


def admin_login():
    """Show admin login form."""
    st.warning("This page requires administrator access.")

    admin_password = st.text_input(
        "Enter Admin Password:",
        type="password",
        key="admin_password_input"
    )

    if st.button("Verify", type="primary"):
        # Check against secrets or environment variable
        try:
            correct_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
        except Exception:
            correct_password = "admin123"  # Default for development

        if admin_password == correct_password:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Incorrect admin password.")


# Title
st.title("⚙️ Admin Settings")
st.markdown(f"Logged in as: **{get_current_username()}**")
st.markdown("---")

# Admin authentication
if not check_admin():
    admin_login()
    st.stop()

st.success("Administrator access granted.")
st.markdown("---")

# Whisper Model Settings
st.header("🎙️ Transcription Settings")
st.markdown("""
Configure the speech-to-text transcription model used for audio recordings.
Changes apply to all users immediately.
""")

# Get current settings
current_settings = get_whisper_settings()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Model Provider")

    model_versions = {
        "openai-whisper": "OpenAI Whisper (Local)",
        "granite-3.3": "IBM Granite 3.3 (Coming Soon)"
    }

    current_version = current_settings.get("model_version", "openai-whisper")

    selected_version = st.selectbox(
        "Select Model Provider:",
        options=list(model_versions.keys()),
        index=list(model_versions.keys()).index(current_version) if current_version in model_versions else 0,
        format_func=lambda x: model_versions[x],
        help="Choose the transcription model provider. Granite 3.3 support coming soon."
    )

    if selected_version == "granite-3.3":
        st.info("Granite 3.3 support is planned for a future update.")

with col2:
    st.subheader("Model Size")

    model_sizes = {
        "tiny": "Tiny (~39M parameters) - Fastest, lowest accuracy",
        "base": "Base (~74M parameters) - Good balance (Default)",
        "small": "Small (~244M parameters) - Better accuracy",
        "medium": "Medium (~769M parameters) - High accuracy",
        "large": "Large (~1.5B parameters) - Best accuracy, slowest"
    }

    current_size = current_settings.get("model_size", "base")

    selected_size = st.selectbox(
        "Select Model Size:",
        options=list(model_sizes.keys()),
        index=list(model_sizes.keys()).index(current_size) if current_size in model_sizes else 1,
        format_func=lambda x: model_sizes[x],
        help="Larger models are more accurate but slower and require more memory."
    )

st.markdown("---")

# Model size comparison table
st.subheader("Model Comparison")
st.markdown("""
| Model | Parameters | English-only | Multilingual | Required VRAM | Relative Speed |
|-------|------------|--------------|--------------|---------------|----------------|
| tiny | 39 M | ✓ | ✓ | ~1 GB | ~32x |
| base | 74 M | ✓ | ✓ | ~1 GB | ~16x |
| small | 244 M | ✓ | ✓ | ~2 GB | ~6x |
| medium | 769 M | ✓ | ✓ | ~5 GB | ~2x |
| large | 1550 M | - | ✓ | ~10 GB | 1x |

*Note: Speed is relative to the large model. Actual performance depends on hardware.*
""")

st.markdown("---")

# Save button
if st.button("💾 Save Settings", type="primary", use_container_width=True):
    try:
        set_setting("whisper_model_size", selected_size)
        set_setting("whisper_model_version", selected_version)
        st.success("Settings saved successfully!")
        st.info("Note: The new model will be loaded the next time a transcription is requested. The first transcription may take longer as the model downloads.")
    except Exception as e:
        st.error(f"Failed to save settings: {e}")

st.markdown("---")

# Current Settings Display
st.header("📊 Current Settings")
col1, col2 = st.columns(2)

with col1:
    st.metric("Model Provider", current_settings.get("model_version", "openai-whisper"))

with col2:
    st.metric("Model Size", current_settings.get("model_size", "base"))

st.markdown("---")

# User Statistics
st.header("👥 User Statistics")

try:
    users = get_all_users()
    user_names_with_cases = get_all_user_names()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Registered Users", len(users))

    with col2:
        st.metric("Users with Cases", len(user_names_with_cases))

    if users:
        st.subheader("Registered Users")
        for user in users:
            st.text(f"• {user.username}")
except Exception as e:
    st.warning(f"Could not load user statistics: {e}")

st.markdown("---")

# Audio Transcription Manager
st.header("🎧 Audio Transcription Manager")
st.markdown("""
Review and transcribe audio recordings from cases. Select a case to view its audio responses,
play them back, and generate transcripts using Whisper.
""")

# Get all cases with audio
all_case_ids = get_all_case_ids()

if not all_case_ids:
    st.info("No cases found in the database.")
else:
    # Case selector
    selected_case_id = st.selectbox(
        "Select a case to view audio recordings:",
        options=["Select a case..."] + all_case_ids,
        key="admin_audio_case_selector"
    )

    if selected_case_id != "Select a case...":
        # Get case details
        case = get_case_by_id(selected_case_id)
        if case:
            st.markdown(f"**Case:** {selected_case_id} | **User:** {case.user_name} | **Type:** {case.intake_version}")

        # Get audio responses for this case
        audio_responses = get_audio_responses_for_case(selected_case_id)

        if not audio_responses:
            st.info("No audio recordings found for this case.")
        else:
            st.success(f"Found {len(audio_responses)} audio recording(s)")

            # Question labels for display
            QUESTION_LABELS = {
                "aq1": "Case Summary", "aq2": "SNF Team Discharge Timing",
                "aq3": "Requirements for Safe Discharge", "aq4": "Estimated Discharge Date",
                "aq5": "Alignment Across Stakeholders", "aq6": "SNF Discharge Conditions",
                "aq7": "HHA Involvement", "aq8": "Information Shared with HHA",
                "q6": "Case Summary", "q7": "Referral Source", "q8": "Upstream Path to SNF",
                "q9": "Expected Length of Stay", "q10": "Initial Assessment",
                "q11": "Early Home Feasibility", "q12": "Key SNF Roles",
                "q13": "Patient Response", "q14": "Patient/Family Goals",
                "q15": "SNF Discharge Timing", "q16": "Requirements for Discharge",
                "q17": "Services Discussed", "q18": "HHA Involvement",
                "q19": "Information Shared with HHA", "q20": "Estimated Discharge Date",
                "q21": "Alignment Across Stakeholders", "q22": "SNF Discharge Conditions",
                "q23": "Plan for First 24-48 Hours", "q25": "Transition Overall",
                "q26": "Handoff Completion", "q27": "24-Hour Follow-up",
                "q28": "Initial At-Home Status"
            }

            for audio_resp in audio_responses:
                # Determine question label
                q_id = audio_resp.question_id
                if q_id and q_id.startswith("fu_"):
                    # Follow-up question audio
                    fu_id = audio_resp.follow_up_question_id
                    if fu_id:
                        fu_question = get_follow_up_question_by_id(fu_id)
                        if fu_question:
                            label = f"Follow-up {fu_question.section}{fu_question.question_number}"
                        else:
                            label = f"Follow-up Question"
                    else:
                        label = f"Follow-up Question"
                else:
                    label = QUESTION_LABELS.get(q_id, q_id or "Unknown")

                with st.expander(f"🎤 {label} (v{audio_resp.version_number})", expanded=False):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Audio playback
                        if audio_resp.audio_data:
                            st.markdown("**Audio Recording:**")
                            st.audio(audio_resp.audio_data, format="audio/webm")
                        else:
                            st.warning("No audio data available")

                    with col2:
                        st.markdown(f"**Question ID:** `{q_id}`")
                        st.markdown(f"**Version:** {audio_resp.version_number}")
                        st.markdown(f"**Created:** {audio_resp.created_at.strftime('%Y-%m-%d %H:%M') if audio_resp.created_at else 'N/A'}")

                    # Transcription section
                    st.markdown("---")

                    # Show existing transcript if available
                    if audio_resp.auto_transcript:
                        st.markdown("**Auto Transcript:**")
                        st.info(audio_resp.auto_transcript)

                    if audio_resp.edited_transcript:
                        st.markdown("**Edited Transcript:**")
                        st.success(audio_resp.edited_transcript)

                    # Transcribe button
                    if audio_resp.audio_data and not audio_resp.auto_transcript:
                        if st.button(f"🔄 Transcribe", key=f"transcribe_{audio_resp.id}"):
                            try:
                                from transcribe import transcribe_audio
                                from db import SessionLocal, AudioResponse

                                transcript = transcribe_audio(audio_resp.audio_data)
                                if transcript:
                                    # Update the database directly
                                    session = SessionLocal()
                                    try:
                                        db_audio = session.query(AudioResponse).filter(
                                            AudioResponse.id == audio_resp.id
                                        ).first()
                                        if db_audio:
                                            db_audio.auto_transcript = transcript
                                            session.commit()
                                            st.success("Transcription complete!")
                                            st.info(transcript)
                                            st.rerun()
                                    finally:
                                        session.close()
                                else:
                                    st.error("Transcription failed. Check if Whisper is installed.")
                            except Exception as e:
                                st.error(f"Error during transcription: {e}")
                    elif audio_resp.auto_transcript:
                        st.success("✅ Already transcribed")

                    # Edit transcript
                    if audio_resp.auto_transcript:
                        edited = st.text_area(
                            "Edit transcript:",
                            value=audio_resp.edited_transcript or audio_resp.auto_transcript,
                            height=100,
                            key=f"edit_{audio_resp.id}"
                        )

                        if st.button(f"💾 Save Edit", key=f"save_edit_{audio_resp.id}"):
                            try:
                                from db import SessionLocal, AudioResponse

                                session = SessionLocal()
                                try:
                                    db_audio = session.query(AudioResponse).filter(
                                        AudioResponse.id == audio_resp.id
                                    ).first()
                                    if db_audio:
                                        db_audio.edited_transcript = edited
                                        session.commit()
                                        st.success("Transcript saved!")
                                        st.rerun()
                                finally:
                                    session.close()
                            except Exception as e:
                                st.error(f"Error saving transcript: {e}")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### Admin Settings")
    st.markdown("""
    Configure application-wide settings:

    - **Transcription Model**: Choose Whisper model size
    - **Model Provider**: OpenAI Whisper (local)
    - **Audio Manager**: Review and transcribe recordings

    **Note**: Larger models provide better accuracy but require more memory and processing time.
    """)

    st.markdown("---")
    st.markdown("### Audio Transcription")
    st.markdown("""
    The Audio Manager lets you:
    - Select a case to view recordings
    - Play back audio responses
    - Generate transcripts with Whisper
    - Edit and save transcripts
    """)

    st.markdown("---")
    st.markdown("### Model Tips")
    st.markdown("""
    - **tiny/base**: Quick transcriptions
    - **small**: Balanced accuracy/speed
    - **medium/large**: Best for complex audio
    """)

    if st.button("Logout Admin", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()
