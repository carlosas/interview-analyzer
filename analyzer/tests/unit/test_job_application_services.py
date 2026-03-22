import uuid

from django.test import TestCase

from src.models import JobApplication
from src.services import JobApplicationService


class TestJobApplicationService(TestCase):
    """Unit tests for JobApplicationService."""

    def setUp(self) -> None:
        self.service = JobApplicationService()

    def test_create_job_application(self) -> None:
        """create should persist a new job application with defaults."""
        app = self.service.create(
            company_name="Acme Corp",
            job_title="Backend Engineer",
        )

        self.assertIsNotNone(app.id)
        self.assertEqual(app.company_name, "Acme Corp")
        self.assertEqual(app.job_title, "Backend Engineer")
        self.assertEqual(app.status, JobApplication.Status.APPLIED)
        self.assertEqual(app.notes, "")

    def test_create_with_all_fields(self) -> None:
        """create should accept optional notes and status."""
        app = self.service.create(
            company_name="BigCo",
            job_title="SRE",
            status=JobApplication.Status.PHONE_SCREEN,
            notes="Recruiter reached out on LinkedIn",
        )

        self.assertEqual(app.status, JobApplication.Status.PHONE_SCREEN)
        self.assertEqual(app.notes, "Recruiter reached out on LinkedIn")

    def test_get_all_returns_all(self) -> None:
        """get_all with no filters should return all applications."""
        self.service.create(company_name="A", job_title="X")
        self.service.create(company_name="B", job_title="Y")

        result = self.service.get_all()

        self.assertEqual(result.count(), 2)

    def test_get_all_filter_by_status(self) -> None:
        """get_all should filter by status when provided."""
        self.service.create(company_name="A", job_title="X")
        self.service.create(
            company_name="B", job_title="Y",
            status=JobApplication.Status.OFFER,
        )

        result = self.service.get_all(status=JobApplication.Status.OFFER)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().company_name, "B")

    def test_get_all_order_by(self) -> None:
        """get_all should respect order_by parameter."""
        self.service.create(company_name="Zebra", job_title="X")
        self.service.create(company_name="Apple", job_title="Y")

        result = list(self.service.get_all(order_by="company_name"))

        self.assertEqual(result[0].company_name, "Apple")
        self.assertEqual(result[1].company_name, "Zebra")

    def test_get_by_id(self) -> None:
        """get_by_id should return the matching application."""
        app = self.service.create(company_name="Test", job_title="Dev")

        result = self.service.get_by_id(app.id)

        self.assertEqual(result.id, app.id)

    def test_get_by_id_not_found(self) -> None:
        """get_by_id should raise DoesNotExist for invalid UUID."""
        with self.assertRaises(JobApplication.DoesNotExist):
            self.service.get_by_id(uuid.uuid4())

    def test_update(self) -> None:
        """update should modify specified fields."""
        app = self.service.create(company_name="Old", job_title="Dev")

        updated = self.service.update(
            app.id,
            company_name="New",
            status=JobApplication.Status.TECHNICAL_INTERVIEW,
        )

        self.assertEqual(updated.company_name, "New")
        self.assertEqual(updated.status, JobApplication.Status.TECHNICAL_INTERVIEW)
        app.refresh_from_db()
        self.assertEqual(app.company_name, "New")

    def test_create_with_transcription_link(self) -> None:
        """create should link to an existing transcription via FK."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from src.models import Transcription

        transcription = Transcription.objects.create(
            name="Mock Interview",
            audio_filename="mock.mp3",
            audio_file=SimpleUploadedFile("mock.mp3", b"audio", content_type="audio/mpeg"),
            status=Transcription.Status.COMPLETED,
        )

        app = self.service.create(
            company_name="LinkedCo",
            job_title="Dev",
            transcription_id=transcription.id,
        )

        app.refresh_from_db()
        self.assertEqual(app.transcription_id, transcription.id)

    def test_update_sets_fk_fields(self) -> None:
        """update should set and clear FK links."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from src.models import Transcription

        transcription = Transcription.objects.create(
            name="Interview",
            audio_filename="i.mp3",
            audio_file=SimpleUploadedFile("i.mp3", b"audio", content_type="audio/mpeg"),
            status=Transcription.Status.COMPLETED,
        )
        app = self.service.create(company_name="Co", job_title="Dev")

        # Set link
        updated = self.service.update(app.id, transcription_id=transcription.id)
        self.assertEqual(updated.transcription_id, transcription.id)

        # Clear link
        updated = self.service.update(app.id, transcription_id=None)
        self.assertIsNone(updated.transcription_id)

    def test_delete(self) -> None:
        """delete should remove the application from the database."""
        app = self.service.create(company_name="Gone", job_title="Dev")
        app_id = app.id

        self.service.delete(app_id)

        self.assertFalse(JobApplication.objects.filter(pk=app_id).exists())
