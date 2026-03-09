import uuid
from datetime import datetime
from typing import Any, NotRequired, TypedDict

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet

from src.models import CV, Interview


class InterviewQueryFilters(TypedDict):
    status: NotRequired[str]
    from_date: NotRequired[datetime]
    to_date: NotRequired[datetime]


class CVService:
    def get_cvs(self) -> QuerySet[CV]:
        return CV.objects.all()

    def get_cv(self, cv_id: uuid.UUID) -> CV:
        return CV.objects.get(pk=cv_id)

    def create_cv(self, name: str, pdf_file: UploadedFile) -> CV:
        text_content = self._extract_text_from_pdf(pdf_file)
        cv = CV.objects.create(
            name=name,
            filename=pdf_file.name or "",
            pdf_file=pdf_file,
            text_content=text_content,
        )
        return cv

    def update_cv(self, cv_id: uuid.UUID, **kwargs: Any) -> CV:
        cv = CV.objects.get(pk=cv_id)
        for key, value in kwargs.items():
            setattr(cv, key, value)
        cv.save()
        return cv

    def delete_cv(self, cv_id: uuid.UUID) -> None:
        cv = CV.objects.get(pk=cv_id)
        cv.pdf_file.delete(save=False)
        cv.delete()

    def _extract_text_from_pdf(self, pdf_file: UploadedFile) -> str:
        from pypdf import PdfReader

        reader = PdfReader(pdf_file)
        text_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)


class InterviewService:
    def get_interviews(self, filters: InterviewQueryFilters) -> QuerySet[Interview]:
        queryset = Interview.objects.all()

        if "status" in filters:
            queryset = queryset.filter(status=filters["status"])
        if "from_date" in filters:
            queryset = queryset.filter(created_at__gte=filters["from_date"])
        if "to_date" in filters:
            queryset = queryset.filter(created_at__lte=filters["to_date"])

        return queryset

    def get_interview(self, interview_id: uuid.UUID) -> Interview:
        return Interview.objects.get(pk=interview_id)

    def create_interview(
        self,
        audio_file: UploadedFile,
        cv_id: uuid.UUID | None = None,
        analysis_prompt: str = "",
    ) -> Interview:
        interview = Interview.objects.create(
            audio_filename=audio_file.name or "",
            audio_file=audio_file,
            analysis_prompt=analysis_prompt,
            cv_id=cv_id,
            status=Interview.Status.PENDING,
        )
        return interview


class LLMService:
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file using OpenAI Whisper API."""
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return transcription.text

    def analyze_interview(
        self, transcription: str, prompt: str = "", cv_text: str = ""
    ) -> dict[str, Any] | str:
        """Analyze interview transcription using GPT-4o via LangChain."""
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY,  # type: ignore[arg-type]
        )

        system_prompt = self._build_system_prompt(prompt)
        human_content = self._build_human_message(transcription, cv_text)

        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_content),
            ]
        )

        import json

        content = str(response.content)
        try:
            result: dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError:
            return content

    def _build_system_prompt(self, custom_prompt: str = "") -> str:
        if custom_prompt:
            return custom_prompt
        return (
            "You are an expert interview analyst. Analyze the following interview "
            "transcription and provide a detailed analysis."
        )

    def _build_human_message(self, transcription: str, cv_text: str = "") -> str:
        message = f"Interview Transcription:\n{transcription}"
        if cv_text:
            message += (
                f"\n\nCandidate's CV/Resume:\n{cv_text}\n\n"
                "Please also identify any discrepancies between the CV claims "
                "and interview responses."
            )
        return message
