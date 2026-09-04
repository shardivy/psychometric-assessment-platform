import uuid
from django.db import models

from assessments.models import AssessmentBlueprintItem, AssessmentVersion, Question, Section
from accounts.models import User
from students.models import StudentRegistration


class AssessmentAssignment(models.Model):
    """
    Represents an assessment assigned to a student.
    Created before the student starts the assessment.
    """

    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        STARTED = "STARTED", "Started"
        SUBMITTED = "SUBMITTED", "Submitted"
        EVALUATED = "EVALUATED", "Evaluted"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    student_registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name="assessment_assignments"
    )

    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.PROTECT,
        related_name="assessment_assignments"
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assessments"
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True
    )

    allowed_attempts = models.PositiveIntegerField(
        default=1
    )

    attempts_used = models.PositiveIntegerField(
        default=0
    )

    assignment_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED
    )
    
    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "assessment_assignments"

        verbose_name = "Assessment Assignment"
        verbose_name_plural = "Assessment Assignments"

        ordering = ["-assigned_at"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["student_registration"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["assignment_status"]),
            models.Index(fields=["assigned_at"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student_registration",
                    "assessment_version"
                ],
                name="unique_student_assessment_assignment"
            )
        ]

    def __str__(self):
        return (
            f"{self.student_registration.registration_number} - "
            f"{self.assessment_version.version_number}"
        )
        

class AssessmentAttempt(models.Model):
    """
    Represents one assessment attempt by a student.
    Created when the student clicks 'Start Assessment'.
    """

    class AttemptStatus(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not Started"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PAUSED = "PAUSED", "Paused"
        SUBMITTED = "SUBMITTED", "Submitted"
        AUTO_SUBMITTED = "AUTO_SUBMITTED", "Auto Submitted"
        EVALUATED = "EVALUATED", "Evaluated"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    assessment_assignment = models.ForeignKey(
        AssessmentAssignment,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    attempt_number = models.PositiveIntegerField(
        default=1
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )
    
    last_activity_at = models.DateTimeField(
        auto_now=True
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    total_time_taken_seconds = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Total duration in seconds"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    device_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Desktop, Mobile, Tablet"
    )

    browser = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    auto_submitted = models.BooleanField(
        default=False
    )

    attempt_status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.NOT_STARTED
    )
    
    assessment_snapshot_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores assessment configuration snapshot at the time of attempt."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "assessment_attempts"

        verbose_name = "Assessment Attempt"
        verbose_name_plural = "Assessment Attempts"

        ordering = ["-started_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_assignment",
                    "attempt_number"
                ],
                name="unique_attempt_number_per_assignment"
            )
        ]

        indexes = [
            models.Index(fields=["assessment_assignment"]),
            models.Index(fields=["attempt_status"]),
            models.Index(fields=["started_at"]),
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["last_activity_at"]),
        ]

    def __str__(self):
        return (
            f"Attempt {self.attempt_number} - "
            f"{self.assessment_assignment.student_registration.registration_number}"
        )
        
class StudentResponse(models.Model):
    """
    Stores the student's response for each question
    in an assessment attempt.
    """

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    assessment_attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="responses"
    )

    assessment_blueprint_item = models.ForeignKey(
        AssessmentBlueprintItem,
        on_delete=models.PROTECT,
        related_name="responses"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="responses"
    )

    selected_response_json = models.JSONField(
        help_text="Stores student's answer in JSON format"
    )

    is_skipped = models.BooleanField(
        default=False
    )

    is_marked_for_review = models.BooleanField(
        default=False
    )
    
    answered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Time spent on this question"
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "student_responses"

        verbose_name = "Response"
        verbose_name_plural = "Responses"

        ordering = [
            "assessment_attempt",
            "assessment_blueprint_item"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_attempt",
                    "assessment_blueprint_item"
                ],
                name="unique_response_per_question_attempt"
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment_attempt"]),
            models.Index(fields=["assessment_blueprint_item"]),
            models.Index(fields=["question"]),
            models.Index(fields=["is_skipped"]),
            models.Index(fields=["is_marked_for_review"]),
            models.Index(fields=["answered_at"]),
        ]

    def __str__(self):
        return (
            f"{self.assessment_attempt.id} - "
            f"{self.question.question_code}"
        )
