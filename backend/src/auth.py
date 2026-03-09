import streamlit as st
from django.conf import settings
from django_redis import get_redis_connection

MAX_ATTEMPTS = 3
LOCKOUT_DURATION = 30  # seconds
LOCKOUT_KEY = "login:lockout"
ATTEMPTS_KEY = "login:attempts"


def check_password() -> bool:
    """Show login form, validate credentials with Redis rate limiting."""
    if st.session_state.get("authenticated"):
        return True

    redis_conn = get_redis_connection("default")

    # Check lockout
    if redis_conn.exists(LOCKOUT_KEY):
        ttl = redis_conn.ttl(LOCKOUT_KEY)
        st.error(f"Too many failed attempts. Try again in {ttl} seconds.")
        return False

    st.title("Interview Analyzer")
    st.markdown("Please log in to continue.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        expected_user = getattr(settings, "LOGIN_USER", "admin")
        expected_password = getattr(settings, "LOGIN_PASSWORD", "password")

        if username == expected_user and password == expected_password:
            st.session_state["authenticated"] = True
            redis_conn.delete(ATTEMPTS_KEY)
            st.rerun()

        # Track failed attempts
        attempts = redis_conn.incr(ATTEMPTS_KEY)
        redis_conn.expire(ATTEMPTS_KEY, LOCKOUT_DURATION * 2)

        if attempts >= MAX_ATTEMPTS:
            redis_conn.setex(LOCKOUT_KEY, LOCKOUT_DURATION, "1")
            redis_conn.delete(ATTEMPTS_KEY)
            st.error(f"Account locked for {LOCKOUT_DURATION} seconds.")
        else:
            remaining = MAX_ATTEMPTS - attempts
            st.error(f"Invalid credentials. {remaining} attempt(s) remaining.")

    return False


def require_auth() -> None:
    """Gate a page behind authentication. Calls st.stop() if not authenticated."""
    if not check_password():
        st.stop()
