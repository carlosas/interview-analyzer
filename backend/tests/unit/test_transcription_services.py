import tempfile
import uuid
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from src.models import Transcription
from src.services import TranscriptionService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestTranscriptionService(TestCase):
    """Unit tests for TranscriptionService."""

    def setUp(self) -> None:
        self.service = TranscriptionService()

    def _create_transcription(
        self,
        filename: str = "interview.mp3",
        name: str = "Interview",
        status: str = Transcription.Status.PENDING,
        **kwargs: object,
    ) -> Transcription:
        audio = SimpleUploadedFile(
            name=filename,
            content=b"fake audio",
            content_type="audio/mpeg",
        )
        return Transcription.objects.create(
            name=name,
            audio_filename=filename,
            audio_file=audio,
            status=status,
            **kwargs,
        )

    def test_get_transcriptions_returns_all(self) -> None:
        """get_transcriptions with empty filters should return all transcriptions."""
        self._create_transcription(filename="one.mp3")
        self._create_transcription(filename="two.mp3")

        result = self.service.get_transcriptions({})

        self.assertEqual(result.count(), 2)

    def test_get_transcriptions_filter_by_status(self) -> None:
        """get_transcriptions should filter by status when provided."""
        self._create_transcription(filename="pending.mp3", status=Transcription.Status.PENDING)
        self._create_transcription(filename="completed.mp3", status=Transcription.Status.COMPLETED)
        self._create_transcription(filename="failed.mp3", status=Transcription.Status.FAILED)

        result = self.service.get_transcriptions({"status": Transcription.Status.COMPLETED})

        self.assertEqual(result.count(), 1)
        self.assertEqual(
            result.first().status,  # type: ignore[union-attr]
            Transcription.Status.COMPLETED,
        )

    def test_get_transcriptions_filter_by_date_range(self) -> None:
        """get_transcriptions should filter by from_date and to_date."""
        now = timezone.now()
        recent = self._create_transcription(filename="recent.mp3")
        Transcription.objects.filter(pk=recent.pk).update(created_at=now - timedelta(days=5))

        old = self._create_transcription(filename="old.mp3")
        Transcription.objects.filter(pk=old.pk).update(created_at=now - timedelta(days=30))

        result = self.service.get_transcriptions(
            {
                "from_date": now - timedelta(days=10),
                "to_date": now,
            }
        )

        self.assertEqual(result.count(), 1)
        self.assertEqual(
            result.first().audio_filename,  # type: ignore[union-attr]
            "recent.mp3",
        )

    def test_get_transcription_by_id(self) -> None:
        """get_transcription should return the transcription matching the given ID."""
        transcription = self._create_transcription(filename="target.mp3")

        result = self.service.get_transcription(transcription.id)

        self.assertEqual(result.id, transcription.id)
        self.assertEqual(result.audio_filename, "target.mp3")

    def test_get_transcription_not_found(self) -> None:
        """get_transcription should raise DoesNotExist for an invalid UUID."""
        with self.assertRaises(Transcription.DoesNotExist):
            self.service.get_transcription(uuid.uuid4())

    def test_create_transcription_sets_pending_status(self) -> None:
        """create_transcription should set the initial status to PENDING."""
        audio = SimpleUploadedFile(
            name="interview.mp3",
            content=b"fake audio content",
            content_type="audio/mpeg",
        )

        transcription = self.service.create_transcription(name="My Interview", audio_file=audio)

        self.assertEqual(transcription.status, Transcription.Status.PENDING)
        self.assertEqual(transcription.name, "My Interview")
        self.assertEqual(transcription.audio_filename, "interview.mp3")

    def test_get_completed_transcriptions(self) -> None:
        """get_completed_transcriptions should only return completed transcriptions."""
        self._create_transcription(filename="pending.mp3", status=Transcription.Status.PENDING)
        self._create_transcription(filename="completed.mp3", status=Transcription.Status.COMPLETED)
        self._create_transcription(filename="failed.mp3", status=Transcription.Status.FAILED)

        result = self.service.get_completed_transcriptions()

        self.assertEqual(result.count(), 1)
        self.assertEqual(
            result.first().audio_filename,  # type: ignore[union-attr]
            "completed.mp3",
        )
