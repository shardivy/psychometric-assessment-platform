import uuid

from django.db import models
from django.conf import settings

from accounts.models import User

class Assessment(models.Model):
    """
    Master Assessment

    Examples:
    - Aptitude Assessment
    - Interest Assessment
    - Personality Assessment
    - Psychometric Assessment
    """

    class AssessmentType(models.TextChoices):
        CAREER = "CAREER", "Career"
        APTITUDE = "APTITUDE", "Aptitude"
        INTEREST = "INTEREST", "Interest"
        PERSONALITY = "PERSONALITY", "Personality"
        PSYCHOMETRIC = "PSYCHOMETRIC", "Psychometric"
        LEARNING_STYLE = "LEARNING_STYLE", "Learning_style"
        CUSTOM = "CUSTOM", "Custom"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    assessment_code = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
        
    )

    name = models.CharField(
        max_length=255
    )
    
    short_name = models.CharField(
        max_length=100, 
        blank=True,
        null=True
    )

    assessment_type = models.CharField(
        max_length=20,
        choices=AssessmentType.choices
    )

    description = models.TextField(
        blank=True,
        null=True
    )
    
    default_language = models.CharField(
        max_length=20,
        default="en"
    )
    
    icon = models.FileField(
        upload_to="assessment/icons/",
        max_length=500,
        blank=True,
        null=True
    )
    
    thumbnail = models.FileField(
        upload_to="assessment/thumbnails/",
        max_length=500,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_assessments",
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
        db_table = "assessments"

        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"

        ordering = ["name"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment_code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["assessment_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.assessment_code})"
    
class AssessmentVersion(models.Model):
    """
    Stores a frozen version of an assessment.
    Once published, the version becomes immutable.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        PUBLISHED = "PUBLISHED", "Published"
        DEPRECATED = "DEPRECATED", "Deprecated"
        ARCHIVED = "ARCHIVED", "Archived"

    # -----------------------------------------------------
    # Primary Key
    # -----------------------------------------------------
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="versions",
        null=True,
        blank=True
    )

    report_template = models.ForeignKey(
        "reports.ReportTemplate",
        on_delete=models.PROTECT,
        related_name="assessment_versions",
        null=True,
        blank=True
    )

    version_number = models.CharField(
        max_length=20,
    )

    version_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    release_date = models.DateField(
        blank=True,
        null=True,
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        blank=True,
        null=True,
    )

    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    total_sections = models.PositiveIntegerField(null=True, blank=True)

    total_subsections = models.PositiveIntegerField(null=True, blank=True)

    total_questions = models.PositiveIntegerField(null=True, blank=True)

    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )

    allow_resume = models.BooleanField(
        default=False,
        null=True,
        blank=True
    )

    allow_review = models.BooleanField(
        default=True,
        null=True,
        blank=True
    )
    
    randomize_sections = models.BooleanField(
        default=False,
        null=True,
        blank=True
    )

    show_result_immediately = models.BooleanField(
        default=False,
    )

    instructions = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_assessment_versions",
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "assessment_versions"

        verbose_name = "Assessment Version"
        verbose_name_plural = "Assessment Versions"

        ordering = [
            "-effective_from",
            "version_number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "version_number"],
                name="unique_assessment_version",
            ),
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment"]),
            models.Index(fields=["version_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["effective_from"]),
            models.Index(fields=["effective_to"]),
        ]

    def __str__(self):
        return f"{self.assessment.name} - {self.version_number}"
    
class Grade(models.Model):
    """
    Master Grade Table.

    Stores all supported academic grades.

    Examples:
    - Grade 6
    - Grade 7
    - Grade 8
    - Grade 9
    - Grade 10
    - Grade 11
    - Grade 12
    """

    class EducationLevel(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        HIGHER_SECONDARY = "HIGHER_SECONDARY", "Higher Secondary"
        UG = "UG", "Undergraduate"
        PG = "PG", "Postgraduate"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # -----------------------------------------------------
    # Primary Key
    # -----------------------------------------------------
    id = models.BigAutoField(
        primary_key=True
    )

    # -----------------------------------------------------
    # Public UUID
    # -----------------------------------------------------
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    grade_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Example: GRADE_10"
    )

    grade_name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Example: Grade 10"
    )

    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.SCHOOL,
    )

    display_order = models.PositiveIntegerField(
        default=1,
        help_text="Used for UI sorting",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "grades"

        verbose_name = "Grade"
        verbose_name_plural = "Grades"

        ordering = [
            "display_order",
            "grade_name",
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["grade_code"]),
            models.Index(fields=["grade_name"]),
            models.Index(fields=["education_level"]),
            models.Index(fields=["status"]),
            models.Index(fields=["display_order"]),
        ]

    def __str__(self):
        return self.grade_name

class Tags(models.Model):
    id = models.BigAutoField(
        primary_key=True
    )
    
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )  
    
    tag_name = models.CharField(
        max_length=255,
        unique=True
    )  
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    class Meta:
        db_table = "tags"

        verbose_name = "Tags"
        verbose_name_plural = "Tags"

        ordering = [
            "tag_name",
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["tag_name"]),
        ]

    def __str__(self):
        return self.tag_name
    
    
    
class QuestionGradeMapping(models.Model):
    """
    Maps Questions to one or more Grades.

    Examples

    Q101
        -> Grade 8
        -> Grade 9

    Q250
        -> Grade 10
    """

    # -----------------------------------------------------
    # Primary Key
    # -----------------------------------------------------
    id = models.BigAutoField(
        primary_key=True
    )

    # -----------------------------------------------------
    # Public UUID
    # -----------------------------------------------------
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    question = models.ForeignKey(
        "assessments.Question",
        on_delete=models.CASCADE,
        related_name="grade_mappings",
    )

    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="question_mappings",
    )
    
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        related_name="tag_mappings",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "question_grade_mappings"

        verbose_name = "Question Grade Mapping"
        verbose_name_plural = "Question Grade Mappings"

        ordering = [
            "grade",
            "question",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "question",
                    "grade",
                    "tag",
                ],
                name="unique_question_grade_tag_mapping",
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["question"]),
            models.Index(fields=["grade"]),
            models.Index(fields=["tag"]),
        ]

    def __str__(self):
        return (
            f"{self.question.question_code} "
            f"- "
            f"{self.grade.grade_name}"
        )   

class Section(models.Model):
    """
    Top-level section of an Assessment Version.

    Examples:
    - Aptitude
    - Interest
    - Personality
    - Psychometric
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    section_code = models.CharField(
        max_length=30,
        help_text="Example: APT, INT, PER"
    )

    name = models.CharField(
        max_length=150
    )
    
    description = models.TextField(
        blank=True,
        null=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(
        default=1,
        help_text="Used for UI sorting",
        null=True,
        blank=True
    )

    is_mandatory = models.BooleanField(
        default=True,
        null=True,
        blank=True
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
        db_table = "sections"

        verbose_name = "Section"
        verbose_name_plural = "Sections"

        ordering = ["display_order", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["section_code"],
                name="unique_section_code_per_version"
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["section_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["display_order"]),
        ]

    def __str__(self):
        return f"{self.name}"
    
class SubSection(models.Model):
    """
    Child section under a Section.

    Examples:
    - Quantitative Reasoning
    - Logical Reasoning
    - Visual Reasoning
    - Mental Agility
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    subsection_code = models.CharField(
        max_length=30,
        help_text="Example: QR, LR, VR, MA"
    )

    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(
        default=1
    )
    
    time_limit_minutes = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    
    question_limit = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    
    randomize_questions = models.BooleanField(
        default=False,
        help_text="Randomize the order of questions in this subsection",
        null=True,
        blank=True
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
        db_table = "subsections"

        verbose_name = "Sub Section"
        verbose_name_plural = "Sub Sections"

        ordering = ["display_order", "name"]

        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["subsection_code"],
        #         name="unique_subsection_code_per_section"
        #     )
        # ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["subsection_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["display_order"]),
        ]

    def __str__(self):
        return f"{self.name}"
        
class Question(models.Model):
    """
    Master Question Library.
    Every question exists only once and can be reused
    across multiple assessments.
    """

    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = "SINGLE_CHOICE", "Single Choice"
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
        TRUE_FALSE = "TRUE_FALSE", "True / False"
        YES_NO = "YES_NO", "Yes / No"
        LIKERT_5 = "LIKERT_5", "Likert (5 Scale)"
        LIKERT_7 = "LIKERT_7", "Likert (7 Scale)"
        INTEGER = "INTEGER", "Integer"
        DECIMAL = "DECIMAL", "Decimal"
        SHORT_TEXT = "SHORT_TEXT", "Short Text"
        LONG_TEXT = "LONG_TEXT", "Long Text"
        IMAGE_SELECTION = "IMAGE_SELECTION", "Image Selection"
        RANK_ORDER = "RANK_ORDER", "Rank Order"
        MATCH_THE_FOLLOWING = "MATCH_THE_FOLLOWING", "Match The Following"
        MATRIX = "MATRIX", "Matrix"
        SLIDER = "SLIDER", "Slider"

    class DifficultyLevel(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    class MediaType(models.TextChoices):
        NONE = "NONE", "None"
        IMAGE = "IMAGE", "Image"
        AUDIO = "AUDIO", "Audio"
        VIDEO = "VIDEO", "Video"
        
    class QuestionStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    # -------------------------------------
    # Primary Key
    # -------------------------------------
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    question_code = models.CharField(
        max_length=30,
        unique=True,
    )

    question_type = models.CharField(
        max_length=30,
        choices=QuestionType.choices,
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
    )

    question_text = models.TextField()

    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.NONE,
    )
    
    media_file = models.FileField(
        upload_to="questions/",
        null=True,
        blank=True,
    )

    media_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    is_mandatory = models.BooleanField(
        default=True,
    )

    explanation = models.TextField(
        blank=True,
        null=True,
    )

    default_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
    )

    negative_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )

    expected_time_seconds = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    language = models.CharField(
        max_length=20,
        default="English",
    )
    
    question_status = models.CharField(
        max_length=20,
        choices=QuestionStatus.choices,
        default=QuestionStatus.DRAFT,
        db_index=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_questions",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "questions"

        verbose_name = "Question"
        verbose_name_plural = "Questions"

        ordering = [
            "question_code",
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["question_code"]),
            models.Index(fields=["question_type"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["language"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.question_code} - {self.question_text[:60]}"
    
class QuestionOption(models.Model):
    """
    Stores options for a question.

    Examples:
    A, B, C, D
    True / False
    Yes / No
    Strongly Agree ... Strongly Disagree
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"
    )

    option_code = models.CharField(
        max_length=20,
        help_text="Example: A, B, C, D"
    )

    option_text = models.TextField(
        blank=True,
        null=True
    )

    option_image = models.FileField(
        blank=True,
        null=True
    )

    option_value = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Internal value if different from option text"
    )

    display_order = models.PositiveIntegerField(
        default=1
    )
    
    is_correct = models.BooleanField(
        default=False,
        help_text="Used for Aptitude / Knowledge based assessments.",
        null=True,
        blank=True
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
        db_table = "question_options"

        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"

        ordering = [
            "question",
            "display_order"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["question", "option_code"],
                name="unique_option_code_per_question"
            ),
            models.UniqueConstraint(
                fields=["question", "display_order"],
                name="unique_option_order_per_question"
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["question"]),
            models.Index(fields=["option_code"]),
            models.Index(fields=["display_order"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.question.question_code} - {self.option_code}"
    
    
class AssessmentBlueprintItem(models.Model):
    class Board(models.TextChoices):
            CBSE = "CBSE", "CBSE"
            ICSE = "ICSE", "ICSE"
            STATE = "STATE", "State Board"
            IB = "IB", "IB"
            IGCSE = "IGCSE", "IGCSE"
            ALL = "ALL", "All Boards"
    
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.CASCADE,
        related_name="blueprint_items"
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="blueprint_items",
        null=True,
        blank=True
    )

    subsection = models.ForeignKey(
        SubSection,
        on_delete=models.CASCADE,
        related_name="blueprint_items",
        null=True,
        blank=True
    )
    
    grade = models.ForeignKey(
        "assessments.Grade",
        on_delete=models.PROTECT,
        related_name="blueprint_items",
        help_text="Applicable Grade (e.g. 8, 9, 10, 11, 12)",
        null=True,
        blank=True
    )

    board = models.CharField(
        max_length=20,
        choices=Board.choices,
        default=Board.ALL,
        blank=True,
        null=True,
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="blueprint_items",
        null=True,
        blank=True
    )

    sequence_no = models.PositiveIntegerField(null=True, blank=True)

    marks_override = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    negative_marks_override = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessment_blueprint_items"
        verbose_name = "Assessment Blueprint Item"
        verbose_name_plural = "Assessment Blueprint Items"
        ordering = [
            "assessment_version",
            "section",
            "subsection",
            "sequence_no",
        ]

        constraints = [

            # Question-level blueprint
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "grade",
                    "board",
                    "section",
                    "subsection",
                    "question",
                ],
                condition=models.Q(
                    question__isnull=False
                ),
                name="unique_blueprint_question",
            ),

            # Grade + Section + SubSection level
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "grade",
                    "board",
                    "section",
                    "subsection",
                ],
                condition=models.Q(
                    question__isnull=True
                ),
                name="unique_blueprint_subsection",
            ),
            
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "grade",
                    "board",
                ],
                condition=models.Q(
                    section__isnull=True,
                    subsection__isnull=True,
                    question__isnull=True,
                ),
                name="unique_blueprint_grade_only",
            ),
        ]

        indexes = [
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["section"]),
            models.Index(fields=["subsection"]),
            models.Index(fields=["question"]),
            models.Index(fields=["sequence_no"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        version_name = (
            self.assessment_version.version_number
            if self.assessment_version
            else "No Version"
        )

        section_name = (
            self.section.name
            if self.section
            else "No Section"
        )

        question_code = (
            self.question.question_code
            if self.question
            else "No Question"
        )

        return (
            f"{version_name} | "
            f"{section_name} | "
            f"{question_code}"
        ) 

class ScoringRule(models.Model):
    """
    Maps a Question Option to a Dimension with
    a score and weight.

    Used by the Evaluation Engine.
    """

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="scoring_rules"
    )

    option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        related_name="scoring_rules",
        null=True,
        blank=True
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_correct = models.BooleanField(
        default=False,
        help_text="Used for Aptitude / Knowledge based assessments."
    )

    remarks = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scoring_rules"
        verbose_name = "Scoring Rule"
        verbose_name_plural = "Scoring Rules"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "question",
                    "option"
                ],
                name="unique_question_option_score"
            )
        ]

        indexes = [
            models.Index(fields=["question"]),
            models.Index(fields=["option"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        option = self.option.option_code if self.option else "No Option"
        return f"{self.question.question_code} | {option} "
        
class InterpretationRule(models.Model):
    """
    Converts calculated scores into
    human-readable interpretations.
    """

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        editable=False,
        unique=True,
        db_index=True
    )
    
    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.CASCADE,
        related_name="interpretation_rules"
    )
    
    subsection = models.ForeignKey(
        SubSection,
        on_delete=models.CASCADE,
        related_name="interpretation_rules"
    )

    min_score = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    rating = models.CharField(
        max_length=100,
        help_text="Example: Excellent, Good, Average"
    )

    title = models.CharField(
        max_length=100,
        help_text="Example: Outstanding, Strong, Moderate"
    )

    performance_analysis = models.TextField(null=True, blank=True)
    
    action_plan = models.TextField(null=True, blank=True)

    display_color = models.CharField(
        max_length=50,
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
        db_table = "interpretation_rules"

        verbose_name = "Interpretation Rule"
        verbose_name_plural = "Interpretation Rules"

        ordering = [
            "display_color"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "subsection",
                    "display_color"
                ],
                name="unique_interpretation_order_per_subsection"
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["subsection"]),
            models.Index(fields=["min_score"]),
            models.Index(fields=["max_score"]),
            models.Index(fields=["display_color"]),
        ]

    def __str__(self):
        return (
            f"{self.subsection.name} | "
            f"{self.rating} "
            f"({self.min_score}-{self.max_score})"
        )
        
class RecommendationRule(models.Model):
    """
    Stores recommendations based on
    Dimension and Rating.
    """

    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        editable=False,
        unique=True,
        db_index=True
    )
    
    assessment_version = models.ForeignKey(
        AssessmentVersion,
        on_delete=models.CASCADE,
        related_name="recommendation_rules"
    )

    rating = models.CharField(
        max_length=100,
        help_text="Example: Excellent, Good, Average"
    )

    recommendation_title = models.CharField(
        max_length=255
    )

    recommendation_text = models.TextField(null=True, blank=True)

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.HIGH,
        blank=True,
        null=True
    )
    
    display_order = models.PositiveIntegerField(
        default=1,
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
        db_table = "recommendation_rules"

        verbose_name = "Recommendation Rule"
        verbose_name_plural = "Recommendation Rules"

        ordering = [
            "priority"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment_version",
                    "rating",
                    "priority"
                ],
                name="unique_recommendation_per_rating"
            )
        ]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return (
            f"{self.assessment_version.version_number} - "
            f"{self.rating}"
        )
        
       
        
        

    
