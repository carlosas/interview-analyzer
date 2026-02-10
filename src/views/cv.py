import streamlit as st
from pypdf import PdfReader
import os
import time
from database import Database
from auth import require_auth

# Ensure authentication
require_auth()

st.title("📄 Curriculum Vitae")

db = Database()

# Initialize Session State
if "selected_cv_id" not in st.session_state:
    st.session_state.selected_cv_id = None

# --- Sidebar ---
with st.sidebar:
    if st.button("➕ New CV", type="secondary"):
        st.session_state.selected_cv_id = None
        st.session_state.cv_selector = None
        st.rerun()

    cvs = db.get_all_cvs()
    if cvs:
        # cvs structure: [(id, name, filename, created_at), ...]
        cv_map = {f"{cv[1]} ({os.path.basename(cv[2])})": cv[0] for cv in cvs}

        # Sync: If selected_cv_id is set, ensure selector matches
        if st.session_state.selected_cv_id:
            current_label = next(
                (k for k, v in cv_map.items() if v == st.session_state.selected_cv_id), None)
            if current_label:
                st.session_state.cv_selector = current_label

        def on_cv_change():
            if st.session_state.cv_selector:
                st.session_state.selected_cv_id = cv_map[st.session_state.cv_selector]
            else:
                st.session_state.selected_cv_id = None

        st.selectbox(
            "Uploaded CVs:",
            options=list(cv_map.keys()),
            index=None,
            key="cv_selector",
            on_change=on_cv_change,
            placeholder="Choose a CV..."
        )
    else:
        st.caption("No CVs uploaded yet.")

# --- Main Content ---
selected_cv = None
if st.session_state.selected_cv_id and cvs:
    selected_cv = next(
        (c for c in cvs if c[0] == st.session_state.selected_cv_id), None)

if selected_cv:
    # Fetch full details including text_content
    full_cv = db.get_cv(selected_cv[0])

    if full_cv:
        cv_id, name, filename, text_content, created_at = full_cv

        st.info(f"Viewing: {name}")

        # Layout: Metadata and Actions
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Filename:** {os.path.basename(filename)}")
            st.markdown(f"**Uploaded:** {created_at}")

        with col2:
            # Download Button
            if os.path.exists(filename):
                try:
                    with open(filename, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_data,
                        file_name=os.path.basename(filename),
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            else:
                st.warning("⚠️ File not found.")

            # Delete Button
            @st.dialog("Confirm Deletion")
            def delete_dialog(cv_id):
                st.warning(
                    "Are you sure you want to delete this CV? This action cannot be undone.")
                if st.button("Delete", type="primary"):
                    if db.delete_cv(cv_id):
                        if os.path.exists(filename):
                            try:
                                os.remove(filename)
                            except Exception as e:
                                print(f"Error deleting file {filename}: {e}")

                        st.success("CV deleted.")
                        st.session_state.selected_cv_id = None
                        st.session_state.cv_selector = None
                        st.rerun()
                    else:
                        st.error("Failed to delete CV.")

            if st.button("🗑️ Delete CV", type="primary", use_container_width=True):
                delete_dialog(cv_id)

        st.divider()

        # Editable Text Area
        with st.expander("📝 Extracted Text (Editable)", expanded=False):
            new_text = st.text_area(
                "Content", value=text_content, height=400, label_visibility="collapsed")
            if st.button("💾 Save Text", type="primary"):
                if db.update_cv_text(cv_id, new_text):
                    st.success("Text updated successfully!")
                    time.sleep(1)  # Give user time to see success message
                    st.rerun()
                else:
                    st.error("Failed to update text.")

    else:
        st.error("CV not found in database.")

elif st.session_state.selected_cv_id:
    # ID set but not found
    st.session_state.selected_cv_id = None
    st.rerun()

else:
    # --- Upload Section ---
    st.subheader("Upload New CV")
    with st.form("upload_cv_form"):
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        cv_name = st.text_input("CV Name (e.g., 'Software Engineer 2024')")
        submitted = st.form_submit_button("Save CV")

        if submitted:
            if not uploaded_file:
                st.error("Please upload a file.")
            elif not cv_name:
                st.error("Please enter a name for the CV.")
            else:
                # Save file
                uploads_dir = "uploads"
                os.makedirs(uploads_dir, exist_ok=True)

                timestamp = int(time.time())
                filename = f"{timestamp}_{uploaded_file.name}"
                filepath = os.path.join(uploads_dir, filename)

                try:
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Extract text content
                    text_content = ""
                    try:
                        reader = PdfReader(filepath)
                        for page in reader.pages:
                            text_content += page.extract_text() + "\n"
                    except Exception as e:
                        print(f"Error extracting PDF text: {e}")

                    # Save to DB
                    cv_id = db.save_cv(cv_name, filepath, text_content)
                    if cv_id:
                        st.success("CV saved successfully!")
                        st.session_state.selected_cv_id = cv_id
                        # We don't set cv_selector here, we let the sync logic handle it on rerun
                        st.rerun()
                    else:
                        st.error("Failed to save CV to database.")
                except Exception as e:
                    st.error(f"Error saving file: {e}")
