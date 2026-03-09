import tempfile
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from src.models import Analysis, Transcription
from src.services import AnalysisService, CVService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestAnalysisService(TestCase):
    """Unit tests for AnalysisService."""

    def setUp(self) -> None:
        self.service = AnalysisService()
        self.transcription = self._create_completed_transcription()

    def _create_completed_transcription(self) -> Transcription:
        audio = SimpleUploadedFile("audio.mp3", b"fake", content_type="audio/mpeg")
        return Transcription.objects.create(
            name="Test Interview",
            audio_filename="audio.mp3",
            audio_file=audio,
            transcription="Some transcription text",
            status=Transcription.Status.COMPLETED,
        )

    def _create_analysis(
        self,
        transcription: Transcription | None = None,
        status: str = Analysis.Status.PENDING,
        **kwargs: object,
    ) -> Analysis:
        return Analysis.objects.create(
            transcription=transcription or self.transcription,
            status=status,
            **kwargs,
        )

    def test_get_analyses_returns_all(self) -> None:
        """get_analyses with empty filters should return all analyses."""
        self._create_analysis()
        self._create_analysis()

        result = self.service.get_analyses({})

        self.assertEqual(result.count(), 2)

    def test_get_analyses_filter_by_status(self) -> None:
        """get_analyses should filter by status when provided."""
        self._create_analysis(status=Analysis.Status.PENDING)
        self._create_analysis(status=Analysis.Status.COMPLETED)
        self._create_analysis(status=Analysis.Status.FAILED)

        result = self.service.get_analyses({"status": Analysis.Status.COMPLETED})

        self.assertEqual(result.count(), 1)
        self.assertEqual(
            result.first().status,  # type: ignore[union-attr]
            Analysis.Status.COMPLETED,
        )

    def test_get_analyses_filter_by_transcription_id(self) -> None:
        """get_analyses should filter by transcription_id when provided."""
        other_transcription = self._create_completed_transcription()
        self._create_analysis(transcription=self.transcription)
        self._create_analysis(transcription=other_transcription)

        result = self.service.get_analyses({"transcription_id": self.transcription.id})

        self.assertEqual(result.count(), 1)

    def test_get_analyses_filter_by_date_range(self) -> None:
        """get_analyses should filter by from_date and to_date."""
        now = timezone.now()
        recent = self._create_analysis()
        Analysis.objects.filter(pk=recent.pk).update(created_at=now - timedelta(days=5))

        old = self._create_analysis()
        Analysis.objects.filter(pk=old.pk).update(created_at=now - timedelta(days=30))

        result = self.service.get_analyses(
            {
                "from_date": now - timedelta(days=10),
                "to_date": now,
            }
        )

        self.assertEqual(result.count(), 1)

    def test_get_analysis_by_id(self) -> None:
        """get_analysis should return the analysis matching the given ID."""
        analysis = self._create_analysis()

        result = self.service.get_analysis(analysis.id)

        self.assertEqual(result.id, analysis.id)

    def test_get_analysis_not_found(self) -> None:
        """get_analysis should raise DoesNotExist for an invalid UUID."""
        with self.assertRaises(Analysis.DoesNotExist):
            self.service.get_analysis(uuid.uuid4())

    @patch.object(CVService, "_extract_text_from_pdf", return_value="cv text")
    def test_create_analysis_sets_pending_status(self, mock_extract: object) -> None:
        """create_analysis should set the initial status to PENDING."""
        cv_service = CVService()
        cv = cv_service.create_cv(
            name="Test CV",
            pdf_file=SimpleUploadedFile("cv.pdf", b"%PDF", content_type="application/pdf"),
        )

        analysis = self.service.create_analysis(
            transcription_id=self.transcription.id,
            prompt="Analyze this",
            cv_id=cv.id,
        )

        self.assertEqual(analysis.status, Analysis.Status.PENDING)
        self.assertEqual(analysis.prompt, "Analyze this")
        self.assertEqual(analysis.cv_id, cv.id)
        self.assertEqual(analysis.transcription_id, self.transcription.id)
