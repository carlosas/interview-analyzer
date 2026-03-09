import tempfile
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from src.models import Interview
from src.services import CVService, InterviewService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestInterviewService(TestCase):
    """Unit tests for InterviewService."""

    def setUp(self) -> None:
        self.service = InterviewService()
        self.dummy_audio = SimpleUploadedFile(
            name="interview.mp3",
            content=b"fake audio content",
            content_type="audio/mpeg",
        )

    def _create_interview(
        self,
        filename: str = "interview.mp3",
        status: str = Interview.Status.PENDING,
        **kwargs: object,
    ) -> Interview:
        audio = SimpleUploadedFile(
            name=filename,
            content=b"fake audio",
            content_type="audio/mpeg",
        )
        interview = Interview.objects.create(
            audio_filename=filename,
            audio_file=audio,
            status=status,
            **kwargs,
        )
        return interview

    def test_get_interviews_returns_all(self) -> None:
        """get_interviews with empty filters should return all interviews."""
        self._create_interview(filename="one.mp3")
        self._create_interview(filename="two.mp3")

        result = self.service.get_interviews({})

        self.assertEqual(result.count(), 2)

    def test_get_interviews_filter_by_status(self) -> None:
        """get_interviews should filter by status when provided."""
        self._create_interview(filename="pending.mp3", status=Interview.Status.PENDING)
        self._create_interview(filename="completed.mp3", status=Interview.Status.COMPLETED)
        self._create_interview(filename="failed.mp3", status=Interview.Status.FAILED)

        result = self.service.get_interviews({"status": Interview.Status.COMPLETED})

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().status, Interview.Status.COMPLETED)  # type: ignore[union-attr]

    def test_get_interviews_filter_by_date_range(self) -> None:
        """get_interviews should filter by from_date and to_date."""
        now = timezone.now()
        interview = self._create_interview(filename="recent.mp3")
        # Manually set created_at to a known date for reliable filtering
        Interview.objects.filter(pk=interview.pk).update(created_at=now - timedelta(days=5))

        old_interview = self._create_interview(filename="old.mp3")
        Interview.objects.filter(pk=old_interview.pk).update(created_at=now - timedelta(days=30))

        result = self.service.get_interviews(
            {
                "from_date": now - timedelta(days=10),
                "to_date": now,
            }
        )

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().audio_filename, "recent.mp3")  # type: ignore[union-attr]

    def test_get_interview_by_id(self) -> None:
        """get_interview should return the interview matching the given ID."""
        interview = self._create_interview(filename="target.mp3")

        result = self.service.get_interview(interview.id)

        self.assertEqual(result.id, interview.id)
        self.assertEqual(result.audio_filename, "target.mp3")

    def test_get_interview_not_found(self) -> None:
        """get_interview should raise DoesNotExist for an invalid UUID."""
        with self.assertRaises(Interview.DoesNotExist):
            self.service.get_interview(uuid.uuid4())

    @patch.object(CVService, "_extract_text_from_pdf", return_value="cv text")
    def test_create_interview_sets_pending_status(self, mock_extract: object) -> None:
        """create_interview should set the initial status to PENDING."""
        cv_service = CVService()
        cv = cv_service.create_cv(
            name="Test CV",
            pdf_file=SimpleUploadedFile("cv.pdf", b"%PDF", content_type="application/pdf"),
        )

        interview = self.service.create_interview(
            audio_file=self.dummy_audio,
            cv_id=cv.id,
            analysis_prompt="Analyze this",
        )

        self.assertEqual(interview.status, Interview.Status.PENDING)
        self.assertEqual(interview.audio_filename, "interview.mp3")
        self.assertEqual(interview.analysis_prompt, "Analyze this")
        self.assertEqual(interview.cv_id, cv.id)
