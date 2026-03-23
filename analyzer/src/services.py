import uuid
from datetime import datetime
from typing import Any, NotRequired, TypedDict

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet

from src.models import CV, Analysis, JobApplication, Transcription


class TranscriptionQueryFilters(TypedDict):
    status: NotRequired[str]
    from_date: NotRequired[datetime]
    to_date: NotRequired[datetime]


class AnalysisQueryFilters(TypedDict):
    status: NotRequired[str]
    transcription_id: NotRequired[uuid.UUID]
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


class TranscriptionService:
    def get_transcriptions(self, filters: TranscriptionQueryFilters) -> QuerySet[Transcription]:
        queryset = Transcription.objects.all()

        if "status" in filters:
            queryset = queryset.filter(status=filters["status"])
        if "from_date" in filters:
            queryset = queryset.filter(created_at__gte=filters["from_date"])
        if "to_date" in filters:
            queryset = queryset.filter(created_at__lte=filters["to_date"])

        return queryset

    def get_transcription(self, transcription_id: uuid.UUID) -> Transcription:
        return Transcription.objects.get(pk=transcription_id)

    def create_transcription(self, name: str, audio_file: UploadedFile) -> Transcription:
        return Transcription.objects.create(
            name=name,
            audio_filename=audio_file.name or "",
            audio_file=audio_file,
            status=Transcription.Status.PENDING,
        )

    def get_completed_transcriptions(self) -> QuerySet[Transcription]:
        return Transcription.objects.filter(status=Transcription.Status.COMPLETED)


class AnalysisService:
    def get_analyses(self, filters: AnalysisQueryFilters) -> QuerySet[Analysis]:
        queryset = Analysis.objects.select_related("transcription", "cv").all()

        if "status" in filters:
            queryset = queryset.filter(status=filters["status"])
        if "transcription_id" in filters:
            queryset = queryset.filter(transcription_id=filters["transcription_id"])
        if "from_date" in filters:
            queryset = queryset.filter(created_at__gte=filters["from_date"])
        if "to_date" in filters:
            queryset = queryset.filter(created_at__lte=filters["to_date"])

        return queryset

    def get_analysis(self, analysis_id: uuid.UUID) -> Analysis:
        return Analysis.objects.select_related("transcription", "cv").get(pk=analysis_id)

    def create_analysis(
        self,
        transcription_id: uuid.UUID,
        prompt: str = "",
        cv_id: uuid.UUID | None = None,
    ) -> Analysis:
        return Analysis.objects.create(
            transcription_id=transcription_id,
            prompt=prompt,
            cv_id=cv_id,
            status=Analysis.Status.PENDING,
        )


class JobApplicationService:
    def get_all(
        self,
        status: str | None = None,
        order_by: str = "-created_at",
    ) -> QuerySet[JobApplication]:
        queryset = JobApplication.objects.select_related("transcription", "analysis").all()
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by(order_by)

    def get_by_id(self, job_application_id: uuid.UUID) -> JobApplication:
        return JobApplication.objects.select_related("transcription", "analysis").get(
            pk=job_application_id
        )

    def create(
        self,
        company_name: str,
        job_title: str,
        status: str = JobApplication.Status.APPLIED,
        notes: str = "",
        transcription_id: uuid.UUID | None = None,
        analysis_id: uuid.UUID | None = None,
    ) -> JobApplication:
        return JobApplication.objects.create(
            company_name=company_name,
            job_title=job_title,
            status=status,
            notes=notes,
            transcription_id=transcription_id,
            analysis_id=analysis_id,
        )

    def update(self, job_application_id: uuid.UUID, **kwargs: Any) -> JobApplication:
        app = JobApplication.objects.get(pk=job_application_id)
        for key, value in kwargs.items():
            setattr(app, key, value)
        app.save()
        return app

    def delete(self, job_application_id: uuid.UUID) -> None:
        JobApplication.objects.filter(pk=job_application_id).delete()


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
