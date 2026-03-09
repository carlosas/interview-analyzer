import logging
import uuid

from django.core.files.uploadedfile import UploadedFile

from src.models import Interview
from src.services import CVService, InterviewService, LLMService

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """Synchronous interview processing pipeline (replaces Celery tasks)."""

    def __init__(self) -> None:
        self.interview_service = InterviewService()
        self.cv_service = CVService()
        self.llm_service = LLMService()

    def create(
        self,
        audio_file: UploadedFile,
        cv_id: uuid.UUID | None = None,
        prompt: str = "",
    ) -> Interview:
        """Create a new interview record."""
        return self.interview_service.create_interview(
            audio_file=audio_file,
            cv_id=cv_id,
            analysis_prompt=prompt,
        )

    def transcribe(self, interview: Interview) -> Interview:
        """Transcribe the interview audio. Updates the interview in-place and in DB."""
        interview.status = Interview.Status.TRANSCRIBING
        interview.save(update_fields=["status", "updated_at"])

        transcription = self.llm_service.transcribe_audio(interview.audio_file.path)
        interview.transcription = transcription
        interview.save(update_fields=["transcription", "updated_at"])
        return interview

    def analyze(self, interview: Interview, prompt: str = "") -> Interview:
        """Analyze the interview transcription. Updates the interview in-place and in DB."""
        interview.status = Interview.Status.ANALYZING
        interview.save(update_fields=["status", "updated_at"])

        cv_text = interview.cv.text_content if interview.cv else ""
        analysis = self.llm_service.analyze_interview(
            transcription=interview.transcription,
            prompt=prompt or interview.analysis_prompt,
            cv_text=cv_text,
        )
        interview.analysis = analysis
        interview.status = Interview.Status.COMPLETED
        interview.save(update_fields=["analysis", "status", "updated_at"])
        return interview

    def fail(self, interview: Interview, error: Exception) -> Interview:
        """Mark the interview as failed."""
        logger.exception("Failed to process interview %s.", interview.id)
        interview.status = Interview.Status.FAILED
        interview.error_message = str(error)
        interview.save(update_fields=["status", "error_message", "updated_at"])
        return interview

    def process_new_interview(
        self,
        audio_file: object,
        cv_id: uuid.UUID | None = None,
        prompt: str = "",
    ) -> Interview:
        """Full pipeline: create -> transcribe -> analyze. Used by tests."""
        interview = self.interview_service.create_interview(
            audio_file=audio_file,  # type: ignore[arg-type]
            cv_id=cv_id,
            analysis_prompt=prompt,
        )
        try:
            self.transcribe(interview)
            self.analyze(interview, prompt)
        except Exception as exc:
            self.fail(interview, exc)
        return interview

    def reanalyze_interview(
        self,
        interview_id: uuid.UUID,
        new_prompt: str,
        cv_id: uuid.UUID | None = None,
    ) -> Interview:
        """Re-analyze existing transcription with a new prompt. Used by tests."""
        interview = self.interview_service.get_interview(interview_id)
        interview.analysis_prompt = new_prompt
        if cv_id:
            interview.cv_id = cv_id
        interview.save(update_fields=["analysis_prompt", "cv_id", "updated_at"])

        try:
            self.analyze(interview, new_prompt)
        except Exception as exc:
            self.fail(interview, exc)
        return interview
