import os
import sys
from pathlib import Path

# Ensure the project root (/app) is on sys.path so "config" and "src" are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402

from src.auth import check_password  # noqa: E402

st.set_page_config(page_title="Interview Analyzer", page_icon="\U0001f916", layout="wide")

if not check_password():
    st.stop()

detail_page = st.Page(
    "views/job_application_detail.py",
    title="Application Details",
    url_path="application-details",
)

pages = {
    "General": [
        st.Page("views/home.py", title="Job Applications", icon="\U0001f4bc"),
    ],
    "Apps": [
        st.Page("views/analysis.py", title="Interview Analyzer", icon="\U0001f916"),
    ],
    "Context": [
        st.Page("views/transcription.py", title="Interviews", icon="\U0001f3a4"),
        st.Page("views/cv.py", title="Curriculum Vitae", icon="\U0001f4c4"),
    ],
}
pg = st.navigation(pages | {"": [detail_page]})
pg.run()
