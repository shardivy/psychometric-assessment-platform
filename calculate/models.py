import uuid

from django.db import models

from assessments.models import AssessmentBlueprintItem, AssessmentVersion, Section

class CalculationFormula(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    case_number = models.PositiveIntegerField(
        unique=True
    )

    case_name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    formula = models.TextField(
        help_text="Mathematical formula expression"
    )

    variables = models.JSONField(
        default=list,
        blank=True
    )

    result_unit = models.CharField(
        max_length=50,
        default="percentage"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "calculation_formulas"
        ordering = ["case_number"]

    def __str__(self):
        return f"Case {self.case_number} - {self.case_name}"
   
    
class AssessmentSectionCalculationRule(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.CASCADE,
        related_name="section_calculation_rules"
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="calculation_rules"
    )

    calculation_formula = models.ForeignKey(
        CalculationFormula,
        on_delete=models.PROTECT,
        related_name="section_rules"
    )

    grade = models.ForeignKey(
        "assessments.Grade",
        on_delete=models.PROTECT,
        related_name="section_calculation_rules",
        null=True,
        blank=True
    )

    board = models.CharField(
        max_length=20,
        choices=AssessmentBlueprintItem.Board.choices,
        default=AssessmentBlueprintItem.Board.ALL
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "assessment_section_calculation_rules"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "section",
                    "grade",
                    "board",
                ],
                condition=models.Q(
                    grade__isnull=False
                ),
                name="unique_section_formula_grade_board",
            ),

            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "section",
                    "board",
                ],
                condition=models.Q(
                    grade__isnull=True
                ),
                name="unique_section_formula_all_grades_board",
            ),
        ]

        indexes = [
            models.Index(fields=["assessment_version","section",]),
            models.Index(fields=["grade","board",]),
            models.Index(fields=["calculation_formula",]),
            models.Index(fields=["status",]),
        ]

    def __str__(self):

        grade_name = (
            self.grade.grade_name
            if self.grade
            else "All Grades"
        )

        return (
            f"{self.assessment_version} | "
            f"{self.section.name} | "
            f"{grade_name} | "
            f"{self.board} | "
            f"{self.calculation_formula.case_name}"
        )
