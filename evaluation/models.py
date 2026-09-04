from django.db import models
import uuid

from assessments.models import AssessmentVersion, InterpretationRule
from accounts.models import User
from students.models import StudentRegistration
from runtime.models import AssessmentAttempt

class EvaluationResult(models.Model):
    class EvaluationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        RE_EVALUATED = "RE_EVALUATED", "Re-Evaluated"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    assessment_attempt = models.OneToOneField(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="evaluation_result"
    )

    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.PROTECT,
        related_name="evaluation_results"
    )

    student_registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name="evaluation_results"
    )

    total_questions = models.PositiveIntegerField()

    answered_questions = models.PositiveIntegerField()

    skipped_questions = models.PositiveIntegerField(default=0)

    correct_answers = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    incorrect_answers = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    obtained_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    overall_rating = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    overall_level = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    overall_percentile = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    evaluation_engine_version = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    evaluation_summary_json = models.JSONField(
        null=True,
        blank=True
    )

    evaluation_status = models.CharField(
        max_length=20,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING
    )

    evaluated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluated_results"
    )

    evaluated_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluation_results"
        verbose_name = "Evaluation Result"
        verbose_name_plural = "Evaluation Results"

        ordering = [
            "-evaluated_at"
        ]

        indexes = [
            models.Index(fields=["assessment_attempt"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["student_registration"]),
            models.Index(fields=["evaluation_status"]),
            models.Index(fields=["evaluated_at"]),
            models.Index(fields=["percentage"]),
        ]

    def __str__(self):
        return (
            f"{self.student_registration.registration_number} | "
            f"{self.assessment_version.version_number} | "
            f"{self.percentage}%"
        )
        
            