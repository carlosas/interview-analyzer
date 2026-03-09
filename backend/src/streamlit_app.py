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

pages = {
    "General": [
        st.Page("views/home.py", title="Home", icon="\U0001f3e0"),
    ],
    "Apps": [
        st.Page("views/interview_analyzer.py", title="Interview Analyzer", icon="\U0001f916"),
    ],
    "Context": [
        st.Page("views/cv.py", title="Curriculum Vitae", icon="\U0001f4c4"),
    ],
}
pg = st.navigation(pages)
pg.run()
