import logging
import uuid

from django.core.files.uploadedfile import UploadedFile

from src.models import Analysis, Transcription
from src.services import AnalysisService, LLMService, TranscriptionService

logger = logging.getLogger(__name__)


class TranscriptionOrchestrator:
    """Synchronous transcription processing pipeline."""

    def __init__(self) -> None:
        self.transcription_service = TranscriptionService()
        self.llm_service = LLMService()

    def create(self, name: str, audio_file: UploadedFile) -> Transcription:
        """Create a new transcription record."""
        return self.transcription_service.create_transcription(name=name, audio_file=audio_file)

    def transcribe(self, transcription: Transcription) -> Transcription:
        """Transcribe the audio. Updates the transcription in-place and in DB."""
        transcription.status = Transcription.Status.TRANSCRIBING
        transcription.save(update_fields=["status", "updated_at"])

        text = self.llm_service.transcribe_audio(transcription.audio_file.path)
        transcription.transcription = text
        transcription.status = Transcription.Status.COMPLETED
        transcription.save(update_fields=["transcription", "status", "updated_at"])
        return transcription

    def fail(self, transcription: Transcription, error: Exception) -> Transcription:
        """Mark the transcription as failed."""
        logger.exception("Failed to transcribe %s.", transcription.id)
        transcription.status = Transcription.Status.FAILED
        transcription.error_message = str(error)
        transcription.save(update_fields=["status", "error_message", "updated_at"])
        return transcription


class AnalysisOrchestrator:
    """Synchronous analysis processing pipeline."""

    def __init__(self) -> None:
        self.analysis_service = AnalysisService()
        self.llm_service = LLMService()

    def create(
        self,
        transcription_id: uuid.UUID,
        prompt: str = "",
        cv_id: uuid.UUID | None = None,
    ) -> Analysis:
        """Create a new analysis record."""
        return self.analysis_service.create_analysis(
            transcription_id=transcription_id,
            prompt=prompt,
            cv_id=cv_id,
        )

    def analyze(self, analysis: Analysis) -> Analysis:
        """Analyze the transcription. Updates the analysis in-place and in DB."""
        analysis.status = Analysis.Status.ANALYZING
        analysis.save(update_fields=["status", "updated_at"])

        cv_text = analysis.cv.text_content if analysis.cv else ""
        result = self.llm_service.analyze_interview(
            transcription=analysis.transcription.transcription,
            prompt=analysis.prompt,
            cv_text=cv_text,
        )
        analysis.result = result
        analysis.status = Analysis.Status.COMPLETED
        analysis.save(update_fields=["result", "status", "updated_at"])
        return analysis

    def fail(self, analysis: Analysis, error: Exception) -> Analysis:
        """Mark the analysis as failed."""
        logger.exception("Failed to analyze %s.", analysis.id)
        analysis.status = Analysis.Status.FAILED
        analysis.error_message = str(error)
        analysis.save(update_fields=["status", "error_message", "updated_at"])
        return analysis
