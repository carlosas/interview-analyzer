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

st.title("\U0001f3a4 Transcription")

# --- Sidebar: transcription history ---
st.sidebar.header("Transcription History")

transcriptions = list(transcription_service.get_transcriptions({}))
transcription_options: list[str] = ["+ New Transcription"] + [
    f"{t.audio_filename} ({t.status})" for t in transcriptions
]

selected_idx = st.sidebar.selectbox(
    "Select a transcription",
    range(len(transcription_options)),
    format_func=lambda i: transcription_options[i],
    key="transcription_select",
)

# --- Main content ---

if selected_idx == 0:
    # New transcription form
    st.subheader("Upload Audio for Transcription")

    audio_file = st.file_uploader(
        "Upload audio file",
        type=["mp3", "wav", "m4a", "mp4"],
        key="audio_upload",
    )

    if st.button("Transcribe", type="primary", key="btn_transcribe"):
        if audio_file is None:
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
                    transcription = orchestrator.create(audio_file=django_file)

                    st.write("Transcribing audio (this may take a few minutes)...")
                    orchestrator.transcribe(transcription)

                    status.update(
                        label="Transcription complete!", state="complete", expanded=False
                    )
                    st.rerun()
                except Exception as exc:
                    orchestrator.fail(transcription, exc)
                    status.update(label="Transcription failed", state="error")
                    st.error(f"Transcription failed: {exc}")

else:
    # View existing transcription
    transcription = transcriptions[selected_idx - 1]
    transcription.refresh_from_db()

    st.subheader(f"Transcription: {transcription.audio_filename}")
    st.caption(
        f"Status: **{transcription.get_status_display()}** "
        f"| Created: {transcription.created_at:%Y-%m-%d %H:%M}"
    )

    if transcription.status == "completed":
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
    if st.button("Delete Transcription", type="secondary", key="btn_delete_transcription"):
        st.session_state["confirm_delete_transcription"] = True

    if st.session_state.get("confirm_delete_transcription"):
        st.warning("Are you sure? This will also delete all analyses linked to this transcription.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key="btn_confirm_delete"):
                transcription.audio_file.delete(save=False)
                transcription.delete()
                st.session_state.pop("confirm_delete_transcription", None)
                st.success("Transcription deleted.")
                st.rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_delete"):
                st.session_state.pop("confirm_delete_transcription", None)
                st.rerun()
