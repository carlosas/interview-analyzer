import tempfile
import uuid
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from src.models import CV
from src.services import CVService


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestCVService(TestCase):
    """Unit tests for CVService."""

    def setUp(self) -> None:
        self.service = CVService()
        self.dummy_pdf = SimpleUploadedFile(
            name="resume.pdf",
            content=b"%PDF-1.4 fake content",
            content_type="application/pdf",
        )

    @patch.object(CVService, "_extract_text_from_pdf", return_value="extracted text")
    def test_get_cvs_returns_all(self, mock_extract: object) -> None:
        """get_cvs should return all CVs in the database."""
        self.service.create_cv(
            name="CV One",
            pdf_file=SimpleUploadedFile("one.pdf", b"%PDF", content_type="application/pdf"),
        )
        self.service.create_cv(
            name="CV Two",
            pdf_file=SimpleUploadedFile("two.pdf", b"%PDF", content_type="application/pdf"),
        )

        result = self.service.get_cvs()

        self.assertEqual(result.count(), 2)

    @patch.object(CVService, "_extract_text_from_pdf", return_value="extracted text")
    def test_get_cv_returns_by_id(self, mock_extract: object) -> None:
        """get_cv should return the CV matching the given ID."""
        cv = self.service.create_cv(name="My CV", pdf_file=self.dummy_pdf)

        result = self.service.get_cv(cv.id)

        self.assertEqual(result.id, cv.id)
        self.assertEqual(result.name, "My CV")

    def test_get_cv_not_found(self) -> None:
        """get_cv should raise CV.DoesNotExist for an invalid UUID."""
        non_existent_id = uuid.uuid4()

        with self.assertRaises(CV.DoesNotExist):
            self.service.get_cv(non_existent_id)

    @patch.object(CVService, "_extract_text_from_pdf", return_value="Parsed PDF text here")
    def test_create_cv_extracts_text(self, mock_extract: object) -> None:
        """create_cv should call _extract_text_from_pdf and store the extracted text."""
        cv = self.service.create_cv(name="Test CV", pdf_file=self.dummy_pdf)

        self.assertEqual(cv.name, "Test CV")
        self.assertEqual(cv.filename, "resume.pdf")
        self.assertEqual(cv.text_content, "Parsed PDF text here")
        self.assertTrue(cv.pdf_file.name)
        self.assertIsNotNone(cv.id)

    @patch.object(CVService, "_extract_text_from_pdf", return_value="text")
    def test_update_cv_name(self, mock_extract: object) -> None:
        """update_cv should update the specified fields on the CV."""
        cv = self.service.create_cv(name="Original", pdf_file=self.dummy_pdf)

        updated_cv = self.service.update_cv(cv.id, name="Updated Name")

        self.assertEqual(updated_cv.name, "Updated Name")
        cv.refresh_from_db()
        self.assertEqual(cv.name, "Updated Name")

    @patch.object(CVService, "_extract_text_from_pdf", return_value="text")
    def test_delete_cv(self, mock_extract: object) -> None:
        """delete_cv should remove the CV from the database."""
        cv = self.service.create_cv(name="To Delete", pdf_file=self.dummy_pdf)
        cv_id = cv.id

        self.service.delete_cv(cv_id)

        self.assertFalse(CV.objects.filter(pk=cv_id).exists())
