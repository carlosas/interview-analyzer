import streamlit as st
import os
import redis
import time


class AuthService:
    def __init__(self):
        self.redis_host = os.environ.get("REDIS_HOST", "localhost")
        try:
            self.r = redis.Redis(host=self.redis_host,
                                 port=6379, db=0, decode_responses=True)
            # Check connection
            self.r.ping()
            self.redis_available = True
        except redis.ConnectionError:
            self.redis_available = False

        self.lock_key = "login_lock"
        self.fail_key = "login_failures"
        self.lock_duration = 30
        self.max_failures = 3

    def is_redis_available(self):
        return self.redis_available

    def get_redis_host(self):
        return self.redis_host

    def get_lock_status(self):
        """
        Returns (is_locked, ttl)
        """
        if not self.redis_available:
            return False, 0

        if self.r.exists(self.lock_key):
            return True, self.r.ttl(self.lock_key)
        return False, 0

    def verify_credentials(self, username, password):
        env_user = os.environ.get("LOGIN_USER")
        env_password = os.environ.get("LOGIN_PASSWORD")

        if not env_user or not env_password:
            raise ValueError(
                "Login credentials are not configured in the environment.")

        if username == env_user and password == env_password:
            if self.redis_available:
                self.r.delete(self.fail_key)
            return True
        return False

    def record_failure(self):
        """
        Increments failure count. Returns (is_locked, duration_if_locked).
        """
        if not self.redis_available:
            return False, 0

        failures = self.r.incr(self.fail_key)
        if failures >= self.max_failures:
            self.r.setex(self.lock_key, self.lock_duration, "locked")
            self.r.delete(self.fail_key)
            return True, self.lock_duration

        return False, self.max_failures - failures


def require_auth():
    """
    Streamlit UI helper that delegates logic to AuthService.
    Stops execution if not authenticated.
    """
    # If already correctly authenticated, return True
    if st.session_state.get("password_correct", False):
        return True

    auth_service = AuthService()

    if not auth_service.is_redis_available():
        st.error(
            f"Cannot connect to Redis at {auth_service.get_redis_host()}. Login unavailable.")
        st.stop()
        return False

    # Check for Global Lock
    is_locked, ttl = auth_service.get_lock_status()
    if is_locked:
        st.error(
            f"⚠️ Too many failed attempts. Login locked. Please wait {ttl} seconds.")

    # Strict mode check (indirectly handled by verify_credentials but good to show error early if possible,
    # though verify_credentials raises ValueError which we can catch)

    st.header("Login Request")

    with st.form("credentials"):
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        submit = st.form_submit_button("Login")

        if submit:
            if is_locked:
                pass
            else:
                try:
                    if auth_service.verify_credentials(username, password):
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        locked_now, info = auth_service.record_failure()
                        if locked_now:
                            st.error(
                                f"❌ Incorrect. Login locked for {info} seconds.")
                        else:
                            st.error(
                                f"😕 User not known or password incorrect. {info} attempts remaining.")
                except ValueError as e:
                    st.error(str(e))
                    st.stop()

    st.stop()
    return False


# Backward compatibility alias if needed, or just replace usage
check_password = require_auth
