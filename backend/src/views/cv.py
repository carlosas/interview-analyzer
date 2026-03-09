import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402

from src.services import CVService  # noqa: E402

cv_service = CVService()

st.title("\U0001f4c4 Curriculum Vitae")

# --- Sidebar ---
st.sidebar.header("CV Management")

if st.sidebar.button("Create New CV", key="btn_new_cv"):
    st.session_state["cv_mode"] = "new"
    st.session_state.pop("selected_cv_idx", None)

cvs = list(cv_service.get_cvs())
if cvs:
    cv_options = [f"{cv.name} ({cv.filename})" for cv in cvs]
    selected_cv_idx = st.sidebar.selectbox(
        "Select a CV",
        range(len(cv_options)),
        format_func=lambda i: cv_options[i],
        key="cv_select",
    )
    if st.session_state.get("cv_mode") != "new":
        st.session_state["selected_cv_idx"] = selected_cv_idx

# --- Main content ---

if st.session_state.get("cv_mode") == "new" or not cvs:
    # Create new CV
    st.subheader("Upload New CV")

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="cv_upload")
    cv_name = st.text_input("CV Name", key="cv_name_input")

    if st.button("Upload", type="primary", key="btn_upload_cv"):
        if pdf_file is None:
            st.error("Please upload a PDF file.")
        elif not cv_name.strip():
            st.error("Please enter a name for the CV.")
        else:
            with st.spinner("Extracting text from PDF..."):
                django_file = SimpleUploadedFile(
                    name=pdf_file.name,
                    content=pdf_file.getvalue(),
                    content_type="application/pdf",
                )
                cv = cv_service.create_cv(name=cv_name.strip(), pdf_file=django_file)
            st.success(f"CV '{cv.name}' uploaded successfully!")
            st.session_state.pop("cv_mode", None)
            st.rerun()

elif "selected_cv_idx" in st.session_state and cvs:
    cv = cvs[st.session_state["selected_cv_idx"]]
    cv.refresh_from_db()

    st.subheader(f"CV: {cv.name}")
    st.caption(f"File: **{cv.filename}** | Uploaded: {cv.created_at:%Y-%m-%d %H:%M}")

    # Download button
    if cv.pdf_file:
        try:
            with open(cv.pdf_file.path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=cv.filename,
                mime="application/pdf",
                key="btn_download_cv",
            )
        except FileNotFoundError:
            st.warning("PDF file not found on disk.")

    # Editable text content
    with st.expander("Extracted Text", expanded=False):
        edited_text = st.text_area(
            "Text content",
            value=cv.text_content,
            height=300,
            key="cv_text_edit",
        )
        if st.button("Save Text", key="btn_save_text"):
            cv_service.update_cv(cv.id, text_content=edited_text)
            st.success("Text content updated.")
            st.rerun()

    # Delete button
    st.divider()
    if st.button("Delete CV", type="secondary", key="btn_delete_cv"):
        st.session_state["confirm_delete_cv"] = True

    if st.session_state.get("confirm_delete_cv"):
        st.warning(
            "Are you sure you want to delete this CV? This will not affect linked interviews."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key="btn_confirm_delete_cv"):
                cv_service.delete_cv(cv.id)
                st.session_state.pop("confirm_delete_cv", None)
                st.session_state.pop("selected_cv_idx", None)
                st.success("CV deleted.")
                st.rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_delete_cv"):
                st.session_state.pop("confirm_delete_cv", None)
                st.rerun()
