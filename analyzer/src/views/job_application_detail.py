import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402

from src.models import JobApplication  # noqa: E402
from src.services import (  # noqa: E402
    AnalysisService,
    JobApplicationService,
    TranscriptionService,
)

job_app_service = JobApplicationService()
transcription_service = TranscriptionService()
analysis_service = AnalysisService()

STATUS_OPTIONS = [s.value for s in JobApplication.Status]
STATUS_LABELS = {s.value: s.label for s in JobApplication.Status}

st.title("💼 Application Details")

# --- Check for selected application ---
app_id = st.session_state.get("selected_job_app_id")
if not app_id:
    st.warning("No application selected.")
    if st.button("← Back to Applications"):
        st.switch_page("views/home.py")
    st.stop()

try:
    app = job_app_service.get_by_id(app_id)
except JobApplication.DoesNotExist:
    st.error("Application not found.")
    if st.button("← Back to Applications"):
        st.session_state.pop("selected_job_app_id", None)
        st.switch_page("views/home.py")
    st.stop()

# --- Back button ---
if st.button("← Back to Applications", key="btn_back"):
    st.session_state.pop("selected_job_app_id", None)
    st.session_state.pop("confirm_delete_job_app", None)
    st.switch_page("views/home.py")

st.divider()

# --- Editable fields ---
company_name = st.text_input("Company Name", value=app.company_name, key="detail_company")
job_title = st.text_input("Job Title", value=app.job_title, key="detail_job_title")

status = st.selectbox(
    "Status",
    STATUS_OPTIONS,
    index=STATUS_OPTIONS.index(app.status),
    format_func=lambda s: STATUS_LABELS[s],
    key="detail_status",
)

notes = st.text_area("Notes", value=app.notes, height=200, key="detail_notes")

# --- Linked Transcription ---
transcriptions = list(transcription_service.get_completed_transcriptions())
transcription_options = ["None"] + [
    f"{t.name} ({t.created_at:%Y-%m-%d})" for t in transcriptions
]
current_transcription_idx = 0
if app.transcription_id:
    for i, t in enumerate(transcriptions):
        if t.id == app.transcription_id:
            current_transcription_idx = i + 1
            break

transcription_choice = st.selectbox(
    "Linked Interview",
    transcription_options,
    index=current_transcription_idx,
    key="detail_transcription",
)

# --- Linked Analysis ---
analyses = list(analysis_service.get_analyses({}))
analysis_options = ["None"] + [
    f"{a.transcription.name} ({a.status})" for a in analyses
]
current_analysis_idx = 0
if app.analysis_id:
    for i, a in enumerate(analyses):
        if a.id == app.analysis_id:
            current_analysis_idx = i + 1
            break

analysis_choice = st.selectbox(
    "Linked Analysis",
    analysis_options,
    index=current_analysis_idx,
    key="detail_analysis",
)

# --- Timestamps ---
st.caption(
    f"Created: {app.created_at:%Y-%m-%d %H:%M} | "
    f"Updated: {app.updated_at:%Y-%m-%d %H:%M}"
)

# --- Save ---
st.divider()
if st.button("Save Changes", type="primary", key="btn_save_detail"):
    if not company_name.strip():
        st.error("Company Name is required.")
    elif not job_title.strip():
        st.error("Job Title is required.")
    else:
        transcription_id = (
            transcriptions[transcription_options.index(transcription_choice) - 1].id
            if transcription_choice != "None"
            else None
        )
        analysis_id = (
            analyses[analysis_options.index(analysis_choice) - 1].id
            if analysis_choice != "None"
            else None
        )
        job_app_service.update(
            app.id,
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            status=status,
            notes=notes,
            transcription_id=transcription_id,
            analysis_id=analysis_id,
        )
        st.success("Changes saved!")
        st.rerun()

# --- Delete ---
if st.button("Delete Application", type="secondary", key="btn_delete_job_app"):
    st.session_state["confirm_delete_job_app"] = True

if st.session_state.get("confirm_delete_job_app"):
    st.warning("Are you sure you want to delete this application?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", key="btn_confirm_delete_job_app"):
            job_app_service.delete(app.id)
            st.session_state.pop("confirm_delete_job_app", None)
            st.session_state.pop("selected_job_app_id", None)
            st.switch_page("views/home.py")
    with col2:
        if st.button("Cancel", key="btn_cancel_delete_job_app"):
            st.session_state.pop("confirm_delete_job_app", None)
            st.rerun()
