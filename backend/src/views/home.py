import streamlit as st

st.title("\U0001f916 Interview Analyzer")

st.markdown(
    """
Welcome to the **Interview Analyzer** - an AI-powered tool for analyzing job interviews.

Upload audio recordings to transcribe them, then create AI-powered analyses
to help you make better hiring decisions.
"""
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("\U0001f3a4 Transcription")
    st.markdown(
        "Upload interview recordings in **MP3**, **WAV**, **M4A**, or **MP4** format "
        "and get automatic speech-to-text transcription powered by **OpenAI Whisper**."
    )

with col2:
    st.subheader("\U0001f4ca Analysis")
    st.markdown(
        "Analyze any transcription using **GPT-4o** via LangChain for structured insights. "
        "Run multiple analyses with different prompts or CVs."
    )

with col3:
    st.subheader("\U0001f4c4 CV Management")
    st.markdown(
        "Upload candidate CVs in **PDF** format. "
        "Attach them to analyses for cross-referencing with interview responses."
    )

st.divider()

st.subheader("Analysis Capabilities")

st.markdown(
    """
- **Executive Summary** - High-level overview of the interview
- **Technical Skills Assessment** - Evaluation of technical competencies
- **Soft Skills Evaluation** - Communication, teamwork, leadership
- **Behavioral Analysis** - STAR method assessment
- **Sentiment Analysis** - Overall interview tone
- **Recommendations** - Actionable improvement suggestions
- **CV Comparison** - Cross-reference with uploaded resumes
"""
)

st.divider()

st.info(
    "Use the sidebar navigation to access **Transcription**, **Analysis**, or manage **CVs**.",
    icon="\u2139\ufe0f",
)
