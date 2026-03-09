import tempfile
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from src.models import Interview
from src.orchestrator import InterviewOrchestrator
from src.services import CVService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestInterviewOrchestrator(TestCase):
    """Unit tests for InterviewOrchestrator."""

    @patch("src.orchestrator.LLMService")
    def test_process_new_interview_full_pipeline(self, mock_llm_cls: MagicMock) -> None:
        """process_new_interview should transition through TRANSCRIBING -> ANALYZING -> COMPLETED."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.return_value = "Transcribed text"
        mock_llm.analyze_interview.return_value = {"summary": "Good interview"}

        orchestrator = InterviewOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        interview = orchestrator.process_new_interview(audio_file=audio)

        interview.refresh_from_db()
        self.assertEqual(interview.status, Interview.Status.COMPLETED)
        self.assertEqual(interview.transcription, "Transcribed text")
        self.assertEqual(interview.analysis, {"summary": "Good interview"})

    @patch("src.orchestrator.LLMService")
    def test_process_new_interview_saves_transcription(self, mock_llm_cls: MagicMock) -> None:
        """process_new_interview should save the transcription."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.return_value = "The candidate discussed Python."
        mock_llm.analyze_interview.return_value = {"summary": "analysis"}

        orchestrator = InterviewOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        interview = orchestrator.process_new_interview(audio_file=audio)

        interview.refresh_from_db()
        self.assertEqual(interview.transcription, "The candidate discussed Python.")

    @patch("src.orchestrator.LLMService")
    @patch.object(CVService, "_extract_text_from_pdf", return_value="CV text content")
    def test_process_new_interview_with_cv(
        self, mock_extract: MagicMock, mock_llm_cls: MagicMock
    ) -> None:
        """process_new_interview should pass CV text to analyze_interview when a CV is linked."""
        cv_service = CVService()
        cv = cv_service.create_cv(
            name="Test CV",
            pdf_file=SimpleUploadedFile("cv.pdf", b"%PDF", content_type="application/pdf"),
        )

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.return_value = "Transcription"
        mock_llm.analyze_interview.return_value = {"summary": "analysis"}

        orchestrator = InterviewOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        orchestrator.process_new_interview(audio_file=audio, cv_id=cv.id)

        mock_llm.analyze_interview.assert_called_once_with(
            transcription="Transcription",
            prompt="",
            cv_text="CV text content",
        )

    @patch("src.orchestrator.LLMService")
    def test_process_new_interview_sets_failed_on_error(self, mock_llm_cls: MagicMock) -> None:
        """process_new_interview should set status to FAILED when an exception occurs."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.side_effect = RuntimeError("API connection failed")

        orchestrator = InterviewOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        interview = orchestrator.process_new_interview(audio_file=audio)

        interview.refresh_from_db()
        self.assertEqual(interview.status, Interview.Status.FAILED)
        self.assertIn("API connection failed", interview.error_message)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestReanalyzeInterview(TestCase):
    """Unit tests for InterviewOrchestrator.reanalyze_interview."""

    @patch("src.orchestrator.LLMService")
    def test_reanalyze_skips_transcription(self, mock_llm_cls: MagicMock) -> None:
        """reanalyze_interview should only call analyze, not transcribe."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.return_value = {"summary": "re-analysis"}

        audio = SimpleUploadedFile("audio.mp3", b"fake", content_type="audio/mpeg")
        interview = Interview.objects.create(
            audio_filename="audio.mp3",
            audio_file=audio,
            status=Interview.Status.COMPLETED,
            transcription="Existing transcription",
        )

        orchestrator = InterviewOrchestrator()
        result = orchestrator.reanalyze_interview(
            interview_id=interview.id,
            new_prompt="New analysis prompt",
        )

        mock_llm.transcribe_audio.assert_not_called()
        mock_llm.analyze_interview.assert_called_once_with(
            transcription="Existing transcription",
            prompt="New analysis prompt",
            cv_text="",
        )

        result.refresh_from_db()
        self.assertEqual(result.status, Interview.Status.COMPLETED)
        self.assertEqual(result.analysis, {"summary": "re-analysis"})
        self.assertEqual(result.analysis_prompt, "New analysis prompt")

    @patch("src.orchestrator.LLMService")
    def test_reanalyze_sets_failed_on_error(self, mock_llm_cls: MagicMock) -> None:
        """reanalyze_interview should set status to FAILED on exception."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.side_effect = RuntimeError("LLM error")

        audio = SimpleUploadedFile("audio.mp3", b"fake", content_type="audio/mpeg")
        interview = Interview.objects.create(
            audio_filename="audio.mp3",
            audio_file=audio,
            status=Interview.Status.COMPLETED,
            transcription="Some transcription",
        )

        orchestrator = InterviewOrchestrator()
        result = orchestrator.reanalyze_interview(
            interview_id=interview.id,
            new_prompt="Prompt",
        )

        result.refresh_from_db()
        self.assertEqual(result.status, Interview.Status.FAILED)
        self.assertIn("LLM error", result.error_message)
