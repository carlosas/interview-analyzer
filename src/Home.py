import streamlit as st
from auth import check_password

st.set_page_config(
    page_title="Interview-Analyzer",
    page_icon="🤖",
)


# Hide sidebar if not logged in (Separation of Concerns: UI logic here, Auth logic in check_password)
if not st.session_state.get("password_correct", False):
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

check_password()

# Navigation Structure
pages = {
    "General": [
        st.Page("views/home.py", title="Home", icon="🏠"),
    ],
    "Apps": [
        st.Page("views/interview_analyzer.py", title="Interview Analyzer", icon="🤖"),
    ],
    "Context": [
        st.Page("views/cv.py", title="Curriculum Vitae", icon="📄"),
    ]
}

pg = st.navigation(pages)
pg.run()
