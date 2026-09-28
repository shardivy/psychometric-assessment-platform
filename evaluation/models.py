from django.db import models
import uuid

from assessments.models import AssessmentBlueprintItem, AssessmentVersion, InterpretationRule, Section, SubSection
from accounts.models import User
from calculate.models import CalculationFormula
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

    evaluated_at = models.DateTimeField(null=True, blank=True)

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
        
        
class StudentSubsectionEvaluation(models.Model):

    class EvaluationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        RE_EVALUATED = "RE_EVALUATED", "Re-Evaluated"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # -----------------------------------------
    # Student Attempt
    # -----------------------------------------

    assessment_attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="subsection_evaluations"
    )

    # -----------------------------------------
    # Assessment Information
    # -----------------------------------------

    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.PROTECT,
        related_name="subsection_evaluations"
    )

    student_registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name="subsection_evaluations"
    )

    # -----------------------------------------
    # Blueprint Structure
    # -----------------------------------------

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="student_subsection_evaluations"
    )

    subsection = models.ForeignKey(
        SubSection,
        on_delete=models.PROTECT,
        related_name="student_evaluations"
    )

    grade = models.ForeignKey(
        "assessments.Grade",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="student_subsection_evaluations"
    )

    board = models.CharField(
        max_length=20,
        choices=AssessmentBlueprintItem.Board.choices,
        default=AssessmentBlueprintItem.Board.ALL
    )

    # -----------------------------------------
    # Formula Used
    # -----------------------------------------

    calculation_formula = models.ForeignKey(
        CalculationFormula,
        on_delete=models.PROTECT,
        related_name="student_evaluations"
    )

    formula_case_number = models.PositiveIntegerField()

    formula_expression = models.TextField()

    # -----------------------------------------
    # Question Statistics
    # -----------------------------------------

    total_questions = models.PositiveIntegerField(
        default=0
    )

    answered_questions = models.PositiveIntegerField(
        default=0
    )

    skipped_questions = models.PositiveIntegerField(
        default=0
    )

    correct_answers = models.PositiveIntegerField(
        default=0
    )

    incorrect_answers = models.PositiveIntegerField(
        default=0
    )

    # -----------------------------------------
    # Score Information
    # -----------------------------------------

    raw_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    min_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    max_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    evaluation_score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    # -----------------------------------------
    # Formula Input Snapshot
    # -----------------------------------------

    formula_input_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Actual values supplied to the formula"
    )

    # -----------------------------------------
    # Evaluation
    # -----------------------------------------

    evaluation_status = models.CharField(
        max_length=20,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING
    )

    evaluation_engine_version = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    evaluated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "student_subsection_evaluations"

        verbose_name = "Student Subsection Evaluation"
        verbose_name_plural = "Student Subsection Evaluations"

        ordering = [
            "assessment_attempt",
            "section",
            "subsection",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_attempt",
                    "subsection",
                ],
                name="unique_subsection_evaluation_per_attempt"
            )
        ]

        indexes = [
            models.Index(fields=["assessment_attempt"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["student_registration"]),
            models.Index(fields=["section"]),
            models.Index(fields=["subsection"]),
            models.Index(fields=["calculation_formula"]),
            models.Index(fields=["evaluation_status"]),
        ]

    def __str__(self):
        return (
            f"{self.student_registration.registration_number} | "
            f"{self.section.name} | "
            f"{self.subsection.name} | "
            f"{self.evaluation_score}"
        )
        
class StudentSubsectionInterpretation(models.Model):
    """
    Maps a student's calculated subsection evaluation
    to the interpretation rule applicable to that score.
    """

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    student_subsection_evaluation = models.OneToOneField(
        StudentSubsectionEvaluation,
        on_delete=models.CASCADE,
        related_name="interpretation"
    )

    interpretation_rule = models.ForeignKey(
        InterpretationRule,
        on_delete=models.PROTECT,
        related_name="student_subsection_interpretations"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "student_subsection_interpretations"

        verbose_name = "Student Subsection Interpretation"
        verbose_name_plural = "Student Subsection Interpretations"

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(fields=["student_subsection_evaluation"]),
            models.Index(fields=["interpretation_rule"]),
        ]

    def __str__(self):
        return (
            f"{self.student_subsection_evaluation} | "
            f"{self.interpretation_rule}"
        )
            