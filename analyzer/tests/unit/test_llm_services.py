import json
from unittest.mock import MagicMock, mock_open, patch

from django.test import TestCase, override_settings

from src.services import LLMService


@override_settings(OPENAI_API_KEY="test-fake-key")
class TestLLMServiceTranscribe(TestCase):
    """Unit tests for LLMService.transcribe_audio."""

    def setUp(self) -> None:
        self.service = LLMService()

    @patch("builtins.open", mock_open(read_data=b"audio bytes"))
    @patch("openai.OpenAI")
    def test_transcribe_audio_calls_whisper(self, mock_openai_cls: MagicMock) -> None:
        """transcribe_audio should call Whisper API and return the transcription text."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_transcription = MagicMock()
        mock_transcription.text = "Hello, this is a test interview."
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        result = self.service.transcribe_audio("/fake/path/audio.mp3")

        self.assertEqual(result, "Hello, this is a test interview.")
        mock_openai_cls.assert_called_once_with(api_key="test-fake-key")
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args
        self.assertEqual(call_kwargs.kwargs["model"], "whisper-1")


@override_settings(OPENAI_API_KEY="test-fake-key")
class TestLLMServiceAnalyze(TestCase):
    """Unit tests for LLMService.analyze_interview."""

    def setUp(self) -> None:
        self.service = LLMService()

    @patch("langchain_openai.ChatOpenAI")
    def test_analyze_interview_returns_structured_json(self, mock_chat_cls: MagicMock) -> None:
        """analyze_interview should return parsed JSON from the LLM response."""
        analysis_json = {
            "executive_summary": "Good candidate",
            "technical_skills": [{"skill": "Python", "assessment": "Strong"}],
            "soft_skills": [{"skill": "Communication", "assessment": "Excellent"}],
            "behavioral_analysis": "Demonstrates STAR method well",
            "sentiment": "positive",
            "recommendations": ["Practice system design"],
        }
        mock_llm = MagicMock()
        mock_chat_cls.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.content = json.dumps(analysis_json)
        mock_llm.invoke.return_value = mock_response

        result = self.service.analyze_interview(
            transcription="Interview transcription here",
            prompt="Focus on technical skills",
        )

        self.assertEqual(result, analysis_json)
        mock_chat_cls.assert_called_once()
        mock_llm.invoke.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    def test_analyze_interview_with_cv_text(self, mock_chat_cls: MagicMock) -> None:
        """analyze_interview should include CV text in the human message when provided."""
        mock_llm = MagicMock()
        mock_chat_cls.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.content = json.dumps({"summary": "analysis"})
        mock_llm.invoke.return_value = mock_response

        self.service.analyze_interview(
            transcription="Transcription text",
            prompt="",
            cv_text="Candidate has 5 years Python experience",
        )

        invoke_args = mock_llm.invoke.call_args[0][0]
        human_message = invoke_args[1]  # Second message is HumanMessage
        human_content = str(human_message.content)
        self.assertIn("Candidate has 5 years Python experience", human_content)
        self.assertIn("CV/Resume", human_content)

    @patch("langchain_openai.ChatOpenAI")
    def test_analyze_interview_handles_non_json_response(self, mock_chat_cls: MagicMock) -> None:
        """analyze_interview should return raw string when response is not valid JSON."""
        mock_llm = MagicMock()
        mock_chat_cls.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.content = "This is not JSON, just plain text analysis."
        mock_llm.invoke.return_value = mock_response

        result = self.service.analyze_interview(
            transcription="Some transcription",
        )

        self.assertIsInstance(result, str)
        self.assertEqual(result, "This is not JSON, just plain text analysis.")
