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

STATUS_COLORS: dict[str, str] = {
    "applied": "blue",
    "phone_screen": "orange",
    "technical_interview": "violet",
    "offer": "rainbow",
    "accepted": "green",
    "rejected": "red",
}

STATUS_OPTIONS = [s.value for s in JobApplication.Status]
STATUS_LABELS = {s.value: s.label for s in JobApplication.Status}

SORT_OPTIONS: dict[str, str] = {
    "Newest First": "-created_at",
    "Oldest First": "created_at",
    "Company Name (A-Z)": "company_name",
    "Company Name (Z-A)": "-company_name",
}

st.title("💼 Job Applications")

# --- Sidebar: Create + Filter/Sort ---
st.sidebar.header("Job Applications")

if st.sidebar.button("➕ Add Application", key="btn_new_job_app"):
    st.session_state["job_app_mode"] = "new"

st.sidebar.divider()

# Filter
filter_options = ["All"] + [STATUS_LABELS[s] for s in STATUS_OPTIONS]
selected_filter = st.sidebar.selectbox(
    "Filter by Status",
    filter_options,
    key="job_app_filter",
)

# Sort
selected_sort = st.sidebar.selectbox(
    "Sort by",
    list(SORT_OPTIONS.keys()),
    key="job_app_sort",
)

# --- Main content ---

if st.session_state.get("job_app_mode") == "new":
    # Create new job application form
    st.subheader("Add New Application")

    company_name = st.text_input("Company Name *", key="new_company_name")
    job_title = st.text_input("Job Title *", key="new_job_title")

    status = st.selectbox(
        "Status",
        STATUS_OPTIONS,
        format_func=lambda s: STATUS_LABELS[s],
        key="new_status",
    )

    notes = st.text_area("Notes (optional)", key="new_notes")

    # Optional links
    transcriptions = list(transcription_service.get_completed_transcriptions())
    transcription_options = ["None"] + [
        f"{t.name} ({t.created_at:%Y-%m-%d})" for t in transcriptions
    ]
    transcription_choice = st.selectbox(
        "Link Interview (optional)",
        transcription_options,
        key="new_transcription_link",
    )

    analyses = list(analysis_service.get_analyses({}))
    analysis_options = ["None"] + [f"{a.transcription.name} ({a.status})" for a in analyses]
    analysis_choice = st.selectbox(
        "Link Analysis (optional)",
        analysis_options,
        key="new_analysis_link",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", key="btn_save_job_app"):
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
                job_app_service.create(
                    company_name=company_name.strip(),
                    job_title=job_title.strip(),
                    status=status,
                    notes=notes,
                    transcription_id=transcription_id,
                    analysis_id=analysis_id,
                )
                st.session_state.pop("job_app_mode", None)
                st.rerun()
    with col2:
        if st.button("Cancel", key="btn_cancel_job_app"):
            st.session_state.pop("job_app_mode", None)
            st.rerun()

else:
    # Build query
    status_filter = None
    if selected_filter != "All":
        # Reverse lookup: label -> value
        label_to_value = {v: k for k, v in STATUS_LABELS.items()}
        status_filter = label_to_value[selected_filter]

    order_by = SORT_OPTIONS[selected_sort]
    applications = list(job_app_service.get_all(status=status_filter, order_by=order_by))

    if not applications:
        st.info(
            "No job applications yet. Click '➕ Add Application' in the sidebar to get started."
        )
    else:
        for app in applications:
            color = STATUS_COLORS.get(app.status, "gray")
            with st.container(border=True):
                col_company, col_title, col_badge, col_status, col_action = st.columns(
                    [3, 3, 1.5, 2.5, 1]
                )

                with col_company:
                    st.markdown(f"**{app.company_name}**")

                with col_title:
                    st.markdown(app.job_title)

                with col_badge:
                    st.markdown(f":{color}[{STATUS_LABELS[app.status]}]")

                with col_status:
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(app.status),
                        format_func=lambda s: STATUS_LABELS[s],
                        key=f"status_{app.id}",
                        label_visibility="collapsed",
                    )
                    if new_status != app.status:
                        job_app_service.update(app.id, status=new_status)
                        st.rerun()

                with col_action:
                    if st.button("→", key=f"detail_{app.id}", help="View details"):
                        st.session_state["selected_job_app_id"] = str(app.id)
                        st.switch_page("views/job_application_detail.py")
