import tempfile
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from src.models import Analysis, Transcription
from src.orchestrator import AnalysisOrchestrator, TranscriptionOrchestrator
from src.services import CVService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestTranscriptionOrchestrator(TestCase):
    """Unit tests for TranscriptionOrchestrator."""

    @patch("src.orchestrator.LLMService")
    def test_transcribe_completes_successfully(self, mock_llm_cls: MagicMock) -> None:
        """transcribe should transition PENDING -> TRANSCRIBING -> COMPLETED."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.return_value = "Transcribed text"

        orchestrator = TranscriptionOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        transcription = orchestrator.create(name="Test Interview", audio_file=audio)
        orchestrator.transcribe(transcription)

        transcription.refresh_from_db()
        self.assertEqual(transcription.status, Transcription.Status.COMPLETED)
        self.assertEqual(transcription.transcription, "Transcribed text")

    @patch("src.orchestrator.LLMService")
    def test_transcribe_saves_transcription_text(self, mock_llm_cls: MagicMock) -> None:
        """transcribe should save the transcription text to the database."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.return_value = "The candidate discussed Python."

        orchestrator = TranscriptionOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        transcription = orchestrator.create(name="Test Interview", audio_file=audio)
        orchestrator.transcribe(transcription)

        transcription.refresh_from_db()
        self.assertEqual(transcription.transcription, "The candidate discussed Python.")

    @patch("src.orchestrator.LLMService")
    def test_fail_sets_failed_status(self, mock_llm_cls: MagicMock) -> None:
        """fail should set status to FAILED and store the error message."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.transcribe_audio.side_effect = RuntimeError("API connection failed")

        orchestrator = TranscriptionOrchestrator()
        audio = SimpleUploadedFile("test.mp3", b"fake audio", content_type="audio/mpeg")
        transcription = orchestrator.create(name="Test Interview", audio_file=audio)

        try:
            orchestrator.transcribe(transcription)
        except RuntimeError as exc:
            orchestrator.fail(transcription, exc)

        transcription.refresh_from_db()
        self.assertEqual(transcription.status, Transcription.Status.FAILED)
        self.assertIn("API connection failed", transcription.error_message)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestAnalysisOrchestrator(TestCase):
    """Unit tests for AnalysisOrchestrator."""

    def _create_completed_transcription(self, text: str = "Some transcription") -> Transcription:
        audio = SimpleUploadedFile("audio.mp3", b"fake", content_type="audio/mpeg")
        return Transcription.objects.create(
            name="Test Interview",
            audio_filename="audio.mp3",
            audio_file=audio,
            transcription=text,
            status=Transcription.Status.COMPLETED,
        )

    @patch("src.orchestrator.LLMService")
    def test_analyze_completes_successfully(self, mock_llm_cls: MagicMock) -> None:
        """analyze should transition PENDING -> ANALYZING -> COMPLETED."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.return_value = {"summary": "Good interview"}

        transcription = self._create_completed_transcription()
        orchestrator = AnalysisOrchestrator()
        analysis = orchestrator.create(transcription_id=transcription.id)
        orchestrator.analyze(analysis)

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, Analysis.Status.COMPLETED)
        self.assertEqual(analysis.result, {"summary": "Good interview"})

    @patch("src.orchestrator.LLMService")
    @patch.object(CVService, "_extract_text_from_pdf", return_value="CV text content")
    def test_analyze_with_cv(self, mock_extract: MagicMock, mock_llm_cls: MagicMock) -> None:
        """analyze should pass CV text to analyze_interview when a CV is linked."""
        cv_service = CVService()
        cv = cv_service.create_cv(
            name="Test CV",
            pdf_file=SimpleUploadedFile("cv.pdf", b"%PDF", content_type="application/pdf"),
        )

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.return_value = {"summary": "analysis"}

        transcription = self._create_completed_transcription(text="Transcription")
        orchestrator = AnalysisOrchestrator()
        analysis = orchestrator.create(
            transcription_id=transcription.id,
            cv_id=cv.id,
        )
        orchestrator.analyze(analysis)

        mock_llm.analyze_interview.assert_called_once_with(
            transcription="Transcription",
            prompt="",
            cv_text="CV text content",
        )

    @patch("src.orchestrator.LLMService")
    def test_analyze_does_not_call_transcribe(self, mock_llm_cls: MagicMock) -> None:
        """analyze should only call analyze_interview, not transcribe_audio."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.return_value = {"summary": "re-analysis"}

        transcription = self._create_completed_transcription(text="Existing transcription")
        orchestrator = AnalysisOrchestrator()
        analysis = orchestrator.create(
            transcription_id=transcription.id,
            prompt="New analysis prompt",
        )
        orchestrator.analyze(analysis)

        mock_llm.transcribe_audio.assert_not_called()
        mock_llm.analyze_interview.assert_called_once_with(
            transcription="Existing transcription",
            prompt="New analysis prompt",
            cv_text="",
        )

    @patch("src.orchestrator.LLMService")
    def test_fail_sets_failed_status(self, mock_llm_cls: MagicMock) -> None:
        """fail should set status to FAILED and store the error message."""
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.analyze_interview.side_effect = RuntimeError("LLM error")

        transcription = self._create_completed_transcription()
        orchestrator = AnalysisOrchestrator()
        analysis = orchestrator.create(transcription_id=transcription.id)

        try:
            orchestrator.analyze(analysis)
        except RuntimeError as exc:
            orchestrator.fail(analysis, exc)

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, Analysis.Status.FAILED)
        self.assertIn("LLM error", analysis.error_message)
