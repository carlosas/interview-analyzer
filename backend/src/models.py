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


class Interview(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TRANSCRIBING = "transcribing", "Transcribing"
        ANALYZING = "analyzing", "Analyzing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_filename = models.CharField(max_length=500)
    audio_file = models.FileField(upload_to="interviews/audio/")
    analysis_prompt = models.TextField(blank=True, default="")
    transcription = models.TextField(blank=True, default="")
    analysis = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")
    cv = models.ForeignKey(
        "CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="interviews"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Interview {self.id} - {self.audio_filename} ({self.status})"
