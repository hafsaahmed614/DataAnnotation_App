"""
Session Timer Component for SNF Patient Navigator Case Collection App.

Provides auto-save functionality and session timeout warnings for intake forms.
Streamlit Cloud has a maximum session timeout of ~30 minutes.
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import json

# Session timeout settings (in seconds)
SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes max for Streamlit Cloud
WARNING_THRESHOLD_SECONDS = 25 * 60  # Show warning at 25 minutes (5 min before timeout)
AUTO_SAVE_INTERVAL_SECONDS = 2 * 60  # Auto-save every 2 minutes


def init_session_timer():
    """Initialize session timer state variables."""
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = datetime.utcnow()
    if 'last_activity_time' not in st.session_state:
        st.session_state.last_activity_time = datetime.utcnow()
    if 'last_auto_save_time' not in st.session_state:
        st.session_state.last_auto_save_time = datetime.utcnow()


def update_activity_time():
    """Update the last activity timestamp. Call this when user interacts with form."""
    st.session_state.last_activity_time = datetime.utcnow()


def get_time_remaining() -> int:
    """
    Get remaining session time in seconds.

    Returns:
        Seconds remaining until session timeout
    """
    if 'session_start_time' not in st.session_state:
        init_session_timer()

    elapsed = (datetime.utcnow() - st.session_state.session_start_time).total_seconds()
    remaining = SESSION_TIMEOUT_SECONDS - elapsed
    return max(0, int(remaining))


def should_show_warning() -> bool:
    """
    Check if session timeout warning should be displayed.

    Warning is suppressed if user has been active recently (within last 60 seconds),
    allowing the warning to auto-dismiss when user continues working.
    """
    remaining = get_time_remaining()

    # Check if we're in the warning zone (less than 5 minutes remaining)
    in_warning_zone = remaining <= (SESSION_TIMEOUT_SECONDS - WARNING_THRESHOLD_SECONDS)

    if not in_warning_zone:
        return False

    # Check for recent activity - if user has been active in last 60 seconds,
    # suppress the warning (it will reappear if they stop working)
    if 'last_activity_time' in st.session_state:
        seconds_since_activity = (datetime.utcnow() - st.session_state.last_activity_time).total_seconds()
        if seconds_since_activity < 60:
            return False

    return True


def should_auto_save() -> bool:
    """Check if enough time has passed for auto-save."""
    if 'last_auto_save_time' not in st.session_state:
        return False

    elapsed = (datetime.utcnow() - st.session_state.last_auto_save_time).total_seconds()
    return elapsed >= AUTO_SAVE_INTERVAL_SECONDS


def mark_auto_saved():
    """Mark that an auto-save just occurred."""
    st.session_state.last_auto_save_time = datetime.utcnow()


def format_time_remaining(seconds: int) -> str:
    """Format seconds as MM:SS string."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def render_session_timer_warning():
    """
    Render the session timeout warning banner if needed.
    Returns True if warning is being shown.
    """
    remaining = get_time_remaining()

    if should_show_warning():
        time_str = format_time_remaining(remaining)

        if remaining <= 60:
            # Critical warning - less than 1 minute
            st.error(f"""
                **Session expiring in {time_str}!**

                Your session will timeout soon. Click the **Save Draft** button at the bottom of the page to avoid losing your work!
            """)
        elif remaining <= 180:
            # Urgent warning - less than 3 minutes
            st.warning(f"""
                **Session expiring in {time_str}**

                Please use the **Save Draft** button at the bottom of the page or submit your case soon to avoid losing work.
            """)
        else:
            # Standard warning - 5 minutes or less
            st.warning(f"""
                **Session expires in {time_str}**

                Your work is being auto-saved, but please complete your case or use the **Save Draft** button at the bottom soon.
            """)
        return True
    return False


def render_auto_save_status(last_save_success: bool = True):
    """
    Render a subtle auto-save status indicator.

    Args:
        last_save_success: Whether the last auto-save was successful
    """
    if 'last_auto_save_time' in st.session_state:
        elapsed = (datetime.utcnow() - st.session_state.last_auto_save_time).total_seconds()
        if elapsed < 5:  # Show for 5 seconds after save
            if last_save_success:
                st.caption("Draft auto-saved")
            else:
                st.caption("Auto-save failed - please save manually")


def get_draft_info_message(draft_updated_at: datetime) -> str:
    """
    Generate a message about when the draft was last saved.

    Args:
        draft_updated_at: The timestamp when draft was last updated

    Returns:
        Human-readable time string
    """
    now = datetime.utcnow()
    diff = now - draft_updated_at

    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def render_resume_draft_banner(draft, intake_type: str, on_resume_callback=None, on_discard_callback=None):
    """
    Render a banner prompting user to resume or discard a saved draft.

    Args:
        draft: The DraftCase object
        intake_type: "Abbreviated" or "Full" for display
        on_resume_callback: Function to call when Resume is clicked
        on_discard_callback: Function to call when Discard is clicked

    Returns:
        Tuple of (resume_clicked, discard_clicked)
    """
    if draft is None:
        return False, False

    time_ago = get_draft_info_message(draft.updated_at)

    # Count answered questions
    answers = json.loads(draft.answers_json) if draft.answers_json else {}
    answered_count = sum(1 for v in answers.values() if v and v.strip())

    st.info(f"""
        **You have an unfinished {intake_type} Intake draft** (last saved {time_ago})

        {answered_count} question(s) answered. Would you like to resume or start fresh?
    """)

    col1, col2, col3 = st.columns([1, 1, 2])

    resume_clicked = False
    discard_clicked = False

    with col1:
        if st.button("Resume Draft", type="primary", key="resume_draft_btn"):
            resume_clicked = True
            if on_resume_callback:
                on_resume_callback()

    with col2:
        if st.button("Start Fresh", key="discard_draft_btn"):
            discard_clicked = True
            if on_discard_callback:
                on_discard_callback()

    return resume_clicked, discard_clicked


def inject_periodic_save_js(interval_seconds: int = 30):
    """Inject JavaScript that auto-saves textarea content.

    Streamlit's st.text_area only sends its value to the server when the
    widget loses focus (blur).  If the user types and then refreshes or
    navigates away without clicking elsewhere, the value is never sent and
    work is lost.  This is especially common for the *last* question on a
    page — there is no "next field" to click so the textarea never blurs.

    Three mechanisms work together to prevent data loss:

      1. **Debounced input save** — listens for typing in any textarea and,
         after the user stops for 3 seconds, briefly blurs/re-focuses to
         flush the value to Streamlit.  This is the primary safeguard.
      2. **Periodic interval** — every *interval_seconds* (default 30 s),
         blurs the active textarea as a safety net for idle sessions.
      3. **beforeunload** — best-effort blur on page refresh / tab close.
    """
    js = f"""
    <script>
    (function() {{
        const INTERVAL_MS = {interval_seconds * 1000};
        const DEBOUNCE_MS = 3000;
        const doc = window.parent.document;

        function blurAndRefocus() {{
            const el = doc.activeElement;
            if (el && el.tagName === 'TEXTAREA') {{
                const start = el.selectionStart;
                const end = el.selectionEnd;
                el.blur();
                setTimeout(function() {{
                    el.focus();
                    el.setSelectionRange(start, end);
                }}, 120);
            }}
        }}

        // 1. Debounced save: blur/refocus 3 s after the user stops typing.
        //    This ensures the last-edited textarea value is flushed to
        //    Streamlit even if the user never clicks away from it.
        if (!window._debounceSaveSetup) {{
            window._debounceSaveSetup = true;
            var debounceTimer = null;
            doc.addEventListener('input', function(e) {{
                if (e.target.tagName === 'TEXTAREA') {{
                    clearTimeout(debounceTimer);
                    var target = e.target;
                    debounceTimer = setTimeout(function() {{
                        // Only blur if the same textarea is still focused
                        if (doc.activeElement === target) {{
                            var s = target.selectionStart;
                            var end = target.selectionEnd;
                            target.blur();
                            setTimeout(function() {{
                                target.focus();
                                target.setSelectionRange(s, end);
                            }}, 120);
                        }}
                    }}, DEBOUNCE_MS);
                }}
            }}, true);
        }}

        // 2. Periodic auto-save trigger (safety net for idle sessions)
        if (!window._periodicSaveInterval) {{
            window._periodicSaveInterval = setInterval(blurAndRefocus, INTERVAL_MS);
        }}

        // 3. Best-effort save on page unload
        window.parent.addEventListener('beforeunload', blurAndRefocus);
    }})();
    </script>
    """
    components.html(js, height=0, width=0)
