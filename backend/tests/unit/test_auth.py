from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings


@override_settings(LOGIN_USER="testuser", LOGIN_PASSWORD="testpass")
class TestAuthHelpers(TestCase):
    """Unit tests for auth rate limiting logic."""

    @patch("src.auth.get_redis_connection")
    @patch("src.auth.st")
    def test_check_password_returns_true_when_authenticated(
        self, mock_st: MagicMock, mock_redis: MagicMock
    ) -> None:
        """check_password should return True if session is already authenticated."""
        mock_st.session_state = {"authenticated": True}

        from src.auth import check_password

        result = check_password()
        self.assertTrue(result)

    @patch("src.auth.get_redis_connection")
    @patch("src.auth.st")
    def test_check_password_returns_false_when_locked_out(
        self, mock_st: MagicMock, mock_redis: MagicMock
    ) -> None:
        """check_password should return False when account is locked out."""
        mock_st.session_state = {}
        mock_conn = MagicMock()
        mock_redis.return_value = mock_conn
        mock_conn.exists.return_value = True
        mock_conn.ttl.return_value = 25

        from src.auth import check_password

        result = check_password()
        self.assertFalse(result)
        mock_st.error.assert_called_once()

    @patch("src.auth.get_redis_connection")
    @patch("src.auth.st")
    def test_check_password_returns_false_when_no_submission(
        self, mock_st: MagicMock, mock_redis: MagicMock
    ) -> None:
        """check_password should return False and show form when not authenticated."""
        mock_st.session_state = {}
        mock_conn = MagicMock()
        mock_redis.return_value = mock_conn
        mock_conn.exists.return_value = False

        # Mock the form context manager
        mock_form = MagicMock()
        mock_st.form.return_value.__enter__ = MagicMock(return_value=mock_form)
        mock_st.form.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.form_submit_button = MagicMock(return_value=False)

        from src.auth import check_password

        result = check_password()
        self.assertFalse(result)
