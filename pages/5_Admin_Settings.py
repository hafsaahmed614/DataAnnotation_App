"""
SNF Patient Navigator Case Collection - Admin Settings Page

Allows administrators to configure application settings including
Whisper transcription model selection.
"""

import streamlit as st
from db import (
    init_db, get_setting, set_setting, get_whisper_settings,
    get_all_users, get_all_user_names
)
from auth import require_auth, get_current_username, init_session_state

# Page configuration
st.set_page_config(
    page_title="Admin Settings | SNF Navigator",
    page_icon="⚙️",
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

# Sidebar
with st.sidebar:
    st.markdown("### Admin Settings")
    st.markdown("""
    Configure application-wide settings:

    - **Transcription Model**: Choose Whisper model size
    - **Model Provider**: OpenAI Whisper (local)

    **Note**: Larger models provide better accuracy but require more memory and processing time.
    """)

    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - **tiny/base**: Good for quick transcriptions
    - **small**: Balanced accuracy/speed
    - **medium/large**: Best for complex audio
    """)

    if st.button("Logout Admin", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()
