import uuid

from django.db import models

from evaluation.models import EvaluationResult
from students.models import StudentRegistration

class ReportTemplate(models.Model):
    """
    Stores reusable report templates/layouts.
    """

    class ReportType(models.TextChoices):
        CAREER_V1 = "CAREER_V1", "Career Report V1"
        CAREER_V2 = "CAREER_V2", "Career Report V2"
        CAREER_V3 = "CAREER_V3", "Career Report V3"
        PERSONALITY = "PERSONALITY", "Personality"
        PSYCHOMETRIC = "PSYCHOMETRIC", "Psychometric"
        ENTERPRISE = "ENTERPRISE", "Enterprise"
        COUNSELLOR = "COUNSELLOR", "Counsellor"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ARCHIVED = "ARCHIVED", "Archived"

    # ---------------------------------
    # Primary Keys
    # ---------------------------------
    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # ---------------------------------
    # Template Information
    # ---------------------------------
    template_code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=255
    )

    report_type = models.CharField(
        max_length=30,
        choices=ReportType.choices
    )

    version = models.CharField(
        max_length=20
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    template_config_json = models.JSONField(
        blank=True,
        null=True
    )

    language = models.CharField(
        max_length=20,
        default="English"
    )

    is_default = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # ---------------------------------
    # Foreign Keys
    # ---------------------------------
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_report_templates",
        null=True, 
        blank=True
    )

    # ---------------------------------
    # Audit Fields
    # ---------------------------------
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ---------------------------------
    # Meta
    # ---------------------------------
    class Meta:
        db_table = "report_templates"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["template_code"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.version})"

class ReportInstance(models.Model):
    class Status(models.TextChoices):
        GENERATING = "GENERATING", "Generating"
        GENERATED = "GENERATED", "Generated"
        FAILED = "FAILED", "Failed"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name="report_instances"
    )

    evaluation_result = models.OneToOneField(
        EvaluationResult,
        on_delete=models.CASCADE,
        related_name="report_instance"
    )

    student_registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name="report_instances"
    )

    report_version = models.CharField(
        max_length=20
    )

    report_title = models.CharField(
        max_length=255
    )

    report_json = models.JSONField()

    report_metadata_json = models.JSONField(
        null=True,
        blank=True
    )

    generated_at = models.DateTimeField()

    generated_by = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Evaluation Engine / AI Engine / Manual"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "report_instances"
        verbose_name = "Report Instance"
        verbose_name_plural = "Report Instances"

        ordering = [
            "-generated_at"
        ]

        indexes = [
            models.Index(fields=["report_template"]),
            models.Index(fields=["evaluation_result"]),
            models.Index(fields=["student_registration"]),
            models.Index(fields=["status"]),
            models.Index(fields=["generated_at"]),
        ]

    def __str__(self):
        return (
            f"{self.student_registration.registration_number} | "
            f"{self.report_title} | "
            f"{self.report_version}"
        )
        
class ReportFile(models.Model):
    """
    Stores generated downloadable report files.
    """

    class FileType(models.TextChoices):
        PDF = "PDF", "PDF"
        HTML = "HTML", "HTML"
        DOCX = "DOCX", "DOCX"

    class StorageProvider(models.TextChoices):
        LOCAL = "LOCAL", "Local"
        AWS_S3 = "AWS_S3", "AWS S3"
        AZURE = "AZURE", "Azure"
        GCS = "GCS", "Google Cloud Storage"

    # -----------------------------
    # Primary Keys
    # -----------------------------
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    report_instance = models.ForeignKey(
        "ReportInstance",
        on_delete=models.CASCADE,
        related_name="report_files"
    )

    # -----------------------------
    # File Information
    # -----------------------------
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices
    )

    file_name = models.CharField(
        max_length=255
    )

    file_path = models.CharField(
        max_length=500
    )

    file_size_kb = models.IntegerField(
        null=True,
        blank=True
    )

    storage_provider = models.CharField(
        max_length=20,
        choices=StorageProvider.choices,
        default=StorageProvider.AWS_S3
    )

    download_count = models.IntegerField(
        default=0
    )

    generated_at = models.DateTimeField()

    # -----------------------------
    # Audit Fields
    # -----------------------------
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )

    # -----------------------------
    # Meta
    # -----------------------------
    class Meta:
        db_table = "report_files"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["report_instance"]),
            models.Index(fields=["file_type"]),
            models.Index(fields=["storage_provider"]),
            models.Index(fields=["generated_at"]),
        ]

    def __str__(self):
        return f"{self.report_instance.id} - {self.file_type}"
