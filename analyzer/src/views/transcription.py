import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402

from src.orchestrator import TranscriptionOrchestrator  # noqa: E402
from src.services import TranscriptionService  # noqa: E402

transcription_service = TranscriptionService()
orchestrator = TranscriptionOrchestrator()

st.title("\U0001f3a4 Interviews")

# --- Sidebar ---
st.sidebar.header("Interview Management")

if st.sidebar.button("Create New Interview", key="btn_new_transcription"):
    st.session_state["transcription_mode"] = "new"
    st.session_state.pop("selected_transcription_idx", None)

transcriptions = list(transcription_service.get_transcriptions({}))
if transcriptions:
    transcription_options = [f"{t.name} ({t.status})" for t in transcriptions]
    selected_transcription_idx = st.sidebar.selectbox(
        "Select an interview",
        range(len(transcription_options)),
        format_func=lambda i: transcription_options[i],
        key="transcription_select",
    )
    if st.session_state.get("transcription_mode") != "new":
        st.session_state["selected_transcription_idx"] = selected_transcription_idx

# --- Main content ---

if st.session_state.get("transcription_mode") == "new" or not transcriptions:
    # New transcription form
    st.subheader("Upload Audio for Transcription")

    interview_name = st.text_input("Interview Name", key="interview_name_input")

    audio_file = st.file_uploader(
        "Upload audio file",
        type=["mp3", "wav", "m4a", "mp4"],
        key="audio_upload",
    )

    if st.button("Transcribe", type="primary", key="btn_transcribe"):
        if not interview_name.strip():
            st.error("Please enter a name for the interview.")
        elif audio_file is None:
            st.error("Please upload an audio file.")
        else:
            django_file = SimpleUploadedFile(
                name=audio_file.name,
                content=audio_file.getvalue(),
                content_type=audio_file.type or "audio/mpeg",
            )

            with st.status("Transcribing audio...", expanded=True) as status:
                try:
                    st.write("Creating transcription record...")
                    transcription = orchestrator.create(
                        name=interview_name.strip(), audio_file=django_file
                    )

                    st.write("Transcribing audio (this may take a few minutes)...")
                    orchestrator.transcribe(transcription)

                    status.update(label="Transcription complete!", state="complete", expanded=False)
                    st.session_state.pop("transcription_mode", None)
                    st.rerun()
                except Exception as exc:
                    orchestrator.fail(transcription, exc)
                    status.update(label="Transcription failed", state="error")
                    st.error(f"Transcription failed: {exc}")

elif "selected_transcription_idx" in st.session_state and transcriptions:
    # View existing transcription
    transcription = transcriptions[st.session_state["selected_transcription_idx"]]
    transcription.refresh_from_db()

    st.subheader(f"Interview: {transcription.name}")
    st.caption(
        f"File: **{transcription.audio_filename}** | Status: **{transcription.get_status_display()}** "
        f"| Created: {transcription.created_at:%Y-%m-%d %H:%M}"
    )

    if transcription.status == "completed":
        with st.expander("Transcription Text", expanded=False):
            st.text_area(
                "Transcription",
                value=transcription.transcription,
                height=400,
                disabled=True,
                key="view_transcription",
            )

    elif transcription.status == "failed":
        st.error(f"Transcription failed: {transcription.error_message}")

    else:
        st.info(f"Status: {transcription.get_status_display()}")

    # Delete button
    st.divider()
    if st.button("Delete Interview", type="secondary", key="btn_delete_transcription"):
        st.session_state["confirm_delete_transcription"] = True

    if st.session_state.get("confirm_delete_transcription"):
        st.warning("Are you sure? This will also delete all analyses linked to this interview.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key="btn_confirm_delete"):
                transcription.audio_file.delete(save=False)
                transcription.delete()
                st.session_state.pop("confirm_delete_transcription", None)
                st.session_state.pop("selected_transcription_idx", None)
                st.success("Interview deleted.")
                st.rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_delete"):
                st.session_state.pop("confirm_delete_transcription", None)
                st.rerun()
