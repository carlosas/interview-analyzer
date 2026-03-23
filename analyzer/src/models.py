import uuid

from django.db import models


class CV(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    filename = models.CharField(max_length=500)
    pdf_file = models.FileField(upload_to="cvs/")
    text_content = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "CV"
        verbose_name_plural = "CVs"

    def __str__(self) -> str:
        return f"CV {self.id} - {self.name}"


class Transcription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TRANSCRIBING = "transcribing", "Transcribing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="")
    audio_filename = models.CharField(max_length=500)
    audio_file = models.FileField(upload_to="transcriptions/audio/")
    transcription = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Transcription {self.id} - {self.name} ({self.status})"


class Analysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ANALYZING = "analyzing", "Analyzing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcription = models.ForeignKey(
        "Transcription", on_delete=models.CASCADE, related_name="analyses"
    )
    cv = models.ForeignKey(
        "CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="analyses"
    )
    prompt = models.TextField(blank=True, default="")
    result = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Analyses"

    def __str__(self) -> str:
        return f"Analysis {self.id} - {self.transcription.name} ({self.status})"


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        PHONE_SCREEN = "phone_screen", "Phone Screen"
        TECHNICAL_INTERVIEW = "technical_interview", "Technical Interview"
        OFFER = "offer", "Offer"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    # Deliberate: using default="" instead of null=True per Django TextField convention
    # (avoids two representations of "no data")
    notes = models.TextField(blank=True, default="")
    transcription = models.ForeignKey(
        "Transcription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_applications",
    )
    analysis = models.ForeignKey(
        "Analysis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_applications",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company_name} — {self.job_title} ({self.get_status_display()})"
