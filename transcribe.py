"""
Transcription module for SNF Patient Navigator Case Collection App.
Uses OpenAI Whisper for local speech-to-text transcription.
Supports admin-configurable model sizes.
"""

import os
import tempfile
import streamlit as st

# Lazy load whisper to avoid startup delays
_whisper_model = None
_current_model_name = None


def get_configured_model_size() -> str:
    """
    Get the configured Whisper model size from database settings.

    Returns:
        Model size string (tiny, base, small, medium, large)
    """
    try:
        from db import get_setting
        return get_setting("whisper_model_size", "base")
    except Exception:
        return "base"


def get_whisper_model(model_name: str = None):
    """
    Get or load the Whisper model (singleton pattern).
    Uses admin-configured model size if not specified.

    Args:
        model_name: Whisper model size ("tiny", "base", "small", "medium", "large")
                   If None, uses the configured setting from admin panel.

    Returns:
        Loaded Whisper model
    """
    global _whisper_model, _current_model_name

    # Use configured model size if not specified
    if model_name is None:
        model_name = get_configured_model_size()

    # Reload model if size changed
    if _whisper_model is not None and _current_model_name != model_name:
        _whisper_model = None  # Force reload with new size

    if _whisper_model is None:
        try:
            import whisper
            with st.spinner(f"Loading Whisper '{model_name}' model (first time only)..."):
                _whisper_model = whisper.load_model(model_name)
                _current_model_name = model_name
        except ImportError:
            st.error("Whisper not installed. Please install with: pip install openai-whisper")
            return None
        except Exception as e:
            st.error(f"Failed to load Whisper model: {e}")
            return None

    return _whisper_model


def transcribe_audio(audio_bytes: bytes, model_name: str = None) -> str | None:
    """
    Transcribe audio bytes to text using Whisper.

    Args:
        audio_bytes: Raw audio data (WAV format from st.audio_input)
        model_name: Whisper model size. If None, uses admin-configured setting.

    Returns:
        Transcribed text or None if transcription failed
    """
    model = get_whisper_model(model_name)
    if model is None:
        return None

    try:
        # Write audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            # Transcribe
            with st.spinner("Transcribing audio..."):
                result = model.transcribe(tmp_path, language="en")
                return result.get("text", "").strip()
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None


def transcribe_audio_file(file_path: str, model_name: str = None) -> str | None:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        file_path: Path to the audio file
        model_name: Whisper model size. If None, uses admin-configured setting.

    Returns:
        Transcribed text or None if transcription failed
    """
    model = get_whisper_model(model_name)
    if model is None:
        return None

    try:
        with st.spinner("Transcribing audio..."):
            result = model.transcribe(file_path, language="en")
            return result.get("text", "").strip()
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None


def show_audio_input_with_transcription(
    question_id: str,
    question_label: str,
    existing_text: str = ""
) -> tuple[str | None, bytes | None, str | None]:
    """
    Display an audio input widget with transcription and text editing.

    Args:
        question_id: Unique ID for this question (for Streamlit keys)
        question_label: Label to display for the question
        existing_text: Existing text answer (if any)

    Returns:
        Tuple of (final_text, audio_bytes, auto_transcript)
        - final_text: The text answer (typed or from transcript)
        - audio_bytes: Raw audio data if recorded
        - auto_transcript: Original Whisper transcript if audio was recorded
    """
    # Initialize session state for this question
    audio_key = f"audio_{question_id}"
    transcript_key = f"transcript_{question_id}"
    edited_key = f"edited_{question_id}"

    if transcript_key not in st.session_state:
        st.session_state[transcript_key] = None
    if edited_key not in st.session_state:
        st.session_state[edited_key] = existing_text

    # Text input option
    st.markdown(f"**{question_label}**")

    col1, col2 = st.columns([3, 1])

    with col1:
        input_method = st.radio(
            "Answer method:",
            ["Type", "Record Audio", "Both"],
            key=f"method_{question_id}",
            horizontal=True
        )

    audio_bytes = None
    auto_transcript = None

    # Show audio recorder if selected
    if input_method in ["Record Audio", "Both"]:
        st.markdown("##### Record your answer")
        audio_value = st.audio_input(
            "Click to record",
            key=audio_key
        )

        if audio_value is not None:
            audio_bytes = audio_value.read()
            # Use the file's actual MIME type for playback (browsers record in WebM, not WAV)
            st.audio(audio_bytes, format=audio_value.type if hasattr(audio_value, 'type') else "audio/webm")

            # Transcribe button
            if st.button(f"Transcribe Recording", key=f"transcribe_{question_id}"):
                transcript = transcribe_audio(audio_bytes)
                if transcript:
                    st.session_state[transcript_key] = transcript
                    st.session_state[edited_key] = transcript
                    st.success("Transcription complete!")

            # Show transcript if available
            if st.session_state[transcript_key]:
                auto_transcript = st.session_state[transcript_key]
                st.markdown("**Original Transcript:**")
                st.info(auto_transcript)

    # Show text area for typing or editing
    if input_method in ["Type", "Both"] or st.session_state[transcript_key]:
        if st.session_state[transcript_key]:
            st.markdown("##### Edit transcript:")
        else:
            st.markdown("##### Type your answer:")

        final_text = st.text_area(
            "Answer",
            value=st.session_state[edited_key],
            key=f"text_{question_id}",
            label_visibility="collapsed",
            height=150
        )
        st.session_state[edited_key] = final_text
    else:
        final_text = st.session_state[edited_key]

    return final_text, audio_bytes, auto_transcript
