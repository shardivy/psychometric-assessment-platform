from django.contrib import admin

from assessments.models import Assessment, AssessmentBlueprintItem, AssessmentVersion, Grade, InterpretationRule, Question, QuestionGradeMapping, QuestionOption, RecommendationRule, ScoringRule, Section, SubSection, Tags

# ==========================================================
# Assessment Admin
# ==========================================================

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_code",
        "name",
        "assessment_type",
        "default_language",
        "status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "assessment_type",
        "status",
        "default_language",
    )

    search_fields = (
        "assessment_code",
        "name",
        "short_name",
        "description",
    )

    autocomplete_fields = (
        "created_by",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "name",
        "-created_at",
    )

    fieldsets = (
        (
            "Assessment Information",
            {
                "fields": (
                    "public_id",
                    "assessment_code",
                    "name",
                    "short_name",
                    "assessment_type",
                    "description",
                )
            },
        ),
        (
            "Display",
            {
                "fields": (
                    "default_language",
                    "icon",
                    "thumbnail",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "created_by",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Assessment Version Admin
# ==========================================================

@admin.register(AssessmentVersion)
class AssessmentVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment",
        "version_number",
        "version_name",
        "effective_from",
        "effective_to",
        "duration_minutes",
        "total_questions",
        "status",
    )

    list_filter = (
        "status",
        "assessment",
        "allow_resume",
        "allow_review",
        "randomize_sections",
        "show_result_immediately",
    )

    search_fields = (
        "assessment__name",
        "version_number",
        "version_name",
    )

    autocomplete_fields = (
        "assessment",
        "report_template",
        "published_by",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "published_at",
    )

    ordering = (
        # "-effective_from",
        # "version_number",
        "-created_at",
    )

    fieldsets = (
        (
            "Version Information",
            {
                "fields": (
                    "public_id",
                    "assessment",
                    "report_template",
                    "version_number",
                    "version_name",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "release_date",
                    "effective_from",
                    "effective_to",
                )
            },
        ),
        (
            "Assessment Statistics",
            {
                "fields": (
                    "duration_minutes",
                    "total_sections",
                    "total_subsections",
                    "total_questions",
                    "total_marks",
                )
            },
        ),
        (
            "Assessment Settings",
            {
                "fields": (
                    "allow_resume",
                    "allow_review",
                    "randomize_sections",
                    "show_result_immediately",
                )
            },
        ),
        (
            "Instructions",
            {
                "fields": (
                    "instructions",
                )
            },
        ),
        (
            "Publishing",
            {
                "fields": (
                    "status",
                    "published_by",
                    "published_at",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

# ==========================================================
# Grade Admin
# ==========================================================
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "grade_code",
        "grade_name",
        "education_level",
        "display_order",
        "status",
        "created_at",
    )

    list_filter = (
        "education_level",
        "status",
    )

    search_fields = (
        "grade_code",
        "grade_name",
    )

    ordering = (
        "display_order",
        "grade_name",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    list_per_page = 25

    list_select_related = ()

    fieldsets = (
        (
            "Grade Information",
            {
                "fields": (
                    "grade_code",
                    "grade_name",
                    "education_level",
                    "display_order",
                    "status",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "public_id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    
# ==========================================================
# Tags Admin
# ==========================================================
@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    
    list_display = (
        "id",
        "tag_name",
        "created_at",
    )
    
    list_filter = (
        "tag_name",
    )
    
    search_fields = (
        "tag_name",
    )
    
    ordering = (
        "-created_at",
    )

# ==========================================================
# Question Grade Mapping Admin
# ==========================================================
@admin.register(QuestionGradeMapping)
class QuestionGradeMappingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "question",
        "grade",
        "tag",
        "created_at",
    )

    list_filter = (
        "grade",
    )

    search_fields = (
        "question__question_code",
        "question__question_text",
        "grade__grade_name",
        "grade__grade_code",
    )

    autocomplete_fields = (
        "question",
        "grade",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "grade",
        # "question",
        "-created_at",
    )

    list_select_related = (
        "question",
        "grade",
    )

    list_per_page = 25

    fieldsets = (
        (
            "Mapping Information",
            {
                "fields": (
                    "question",
                    "grade",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "public_id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

# ==========================================================
# Section Admin
# ==========================================================

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "section_code",
        "name",
        "display_order",
        "is_mandatory",
        "status",
    )

    list_filter = (
        "status",
        "is_mandatory",
    )

    search_fields = (
        "section_code",
        "name",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "display_order",
        "-created_at",
    )

    fieldsets = (
        (
            "Section Information",
            {
                "fields": (
                    "public_id",
                    "section_code",
                    "name",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "instructions",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "display_order",
                    "is_mandatory",
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# SubSection Admin
# ==========================================================

@admin.register(SubSection)
class SubSectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subsection_code",
        "name",
        "display_order",
        "time_limit_minutes",
        "question_limit",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "subsection_code",
        "name",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "section",
        "display_order",
    )

    fieldsets = (
        (
            "Sub Section Information",
            {
                "fields": (
                    "public_id",
                    "subsection_code",
                    "name",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "instructions",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "display_order",
                    "time_limit_minutes",
                    "question_limit",
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    
# ==========================================================
# Question Option Inline
# ==========================================================

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1

    fields = (
        "option_code",
        "option_text",
        "option_value",
        "display_order",
        "is_correct",
        "status",
    )

    ordering = (
        "-id",
    )


# ==========================================================
# Question Admin
# ==========================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question_code",
        "question_type",
        "difficulty_level",
        "language",
        "default_marks",
        "question_status",
        "is_active",
        "created_by",
    )

    list_filter = (
        "question_type",
        "difficulty_level",
        "media_type",
        "language",
        "is_active",
    )

    search_fields = (
        "question_code",
        "question_text",
        "question_status",
    )

    autocomplete_fields = (
        "created_by",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-id",
    )

    inlines = [
        QuestionOptionInline,
    ]

    fieldsets = (
        (
            "Question",
            {
                "fields": (
                    "public_id",
                    "question_code",
                    "question_type",
                    "difficulty_level",
                )
            },
        ),
        (
            "Question Content",
            {
                "fields": (
                    "question_text",
                    "explanation",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "media_type",
                    "media_url",
                    "media_file",
                )
            },
        ),
        (
            "Marks",
            {
                "fields": (
                    "default_marks",
                    "negative_marks",
                    "expected_time_seconds",
                )
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "language",
                    "is_mandatory",
                    "is_active",
                )
            },
        ),
        (
            "Created By",
            {
                "fields": (
                    "created_by",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Question Option Admin
# ==========================================================

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "option_code",
        "display_order",
        "is_correct",
        "status",
    )

    list_filter = (
        "status",
        "is_correct",
    )

    search_fields = (
        "question__question_code",
        "question__question_text",
        "option_code",
        "option_text",
    )

    autocomplete_fields = (
        "question",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "question",
        # "display_order",
        "-created_at",
    )

    fieldsets = (
        (
            "Question Option",
            {
                "fields": (
                    "public_id",
                    "question",
                    "option_code",
                    "option_text",
                    "option_image",
                    "option_value",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "display_order",
                    "is_correct",
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    
# ==========================================================
# Assessment Blueprint Item Admin
# ==========================================================

@admin.register(AssessmentBlueprintItem)
class AssessmentBlueprintItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_version",
        "section",
        "subsection",
        "grade",
        "board",
        "question",
        "sequence_no",
        "status",
    )

    list_filter = (
        "assessment_version",
        "section",
        "subsection",
        "grade",
        "board",
        "status",
    )

    search_fields = (
        "assessment_version__version_number",
        "question__question_code",
        "question__question_text",
        "section__name",
        "subsection__name",
    )

    autocomplete_fields = (
        "assessment_version",
        "section",
        "subsection",
        "question",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        # "assessment_version",
        # "section",
        # "subsection",
        # "sequence_no",
        "-id",
    )

    fieldsets = (
        (
            "Blueprint",
            {
                "fields": (
                    "public_id",
                    "assessment_version",
                    "section",
                    "subsection",
                    "question",
                )
            },
        ),
        (
            "Marks",
            {
                "fields": (
                    "sequence_no",
                    "marks_override",
                    "negative_marks_override",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Scoring Rule Admin
# ==========================================================

@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "option",
        "score",
        "weight_percentage",
        "is_correct",
    )

    list_filter = (
        "is_correct",
    )

    search_fields = (
        "question__question_code",
        "question__question_text",
        "option__option_code",
        "option__option_text",
    )

    autocomplete_fields = (
        "question",
        "option"
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "question",
    )

    fieldsets = (
        (
            "Rule",
            {
                "fields": (
                    "public_id",
                    "question",
                    "option",
                )
            },
        ),
        (
            "Scoring",
            {
                "fields": (
                    "score",
                    "weight_percentage",
                    "is_correct",
                    "remarks",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

# ==========================================================
# Interpretation Rule Admin
# ==========================================================

@admin.register(InterpretationRule)
class InterpretationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_version",
        "subsection",
        "rating",
        "title",
        "min_score",
        "max_score",
        "display_color",
    )

    list_filter = (
        "assessment_version",
        "subsection",
    )

    search_fields = (
        "assessment_version__version_number",
        "subsection__name",
        "rating",
        "title",
    )

    autocomplete_fields = (
        "assessment_version",
        "subsection",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "subsection",
        "min_score",
    )

    fieldsets = (
        (
            "Interpretation",
            {
                "fields": (
                    "public_id",
                    "assessment_version",
                    "subsection",
                    "rating",
                    "title",
                    "interpretation",
                )
            },
        ),
        (
            "Score Range",
            {
                "fields": (
                    "min_score",
                    "max_score",
                    "display_color",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Recommendation Rule Admin
# ==========================================================

@admin.register(RecommendationRule)
class RecommendationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_version",
        "rating",
        "recommendation_title",
        "priority",
        "display_order",
    )

    list_filter = (
        "assessment_version",
        "priority",
    )

    search_fields = (
        "assessment_version__version_number",
        "rating",
        "recommendation_title",
        "recommendation_text",
    )

    autocomplete_fields = (
        "assessment_version",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "assessment_version",
        "display_order",
    )

    fieldsets = (
        (
            "Recommendation",
            {
                "fields": (
                    "public_id",
                    "assessment_version",
                    "rating",
                    "recommendation_title",
                    "recommendation_text",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "priority",
                    "display_order",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )