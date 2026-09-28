from django.contrib import admin

from evaluation.models import EvaluationResult, StudentSubsectionEvaluation, StudentSubsectionInterpretation

# ==========================================================
# Evaluation Result Admin
# ==========================================================

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_attempt",
        "student_registration",
        "assessment_version",
        "percentage",
        "overall_rating",
        "evaluation_status",
        "evaluated_at",
    )

    list_filter = (
        "evaluation_status",
        "assessment_version",
        "overall_rating",
    )

    search_fields = (
        "student_registration__registration_number",
        "assessment_attempt__id",
        "assessment_version__version_number",
    )

    autocomplete_fields = (
        "assessment_attempt",
        "assessment_version",
        "student_registration",
        "evaluated_by",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-evaluated_at",
    )

    fieldsets = (
        (
            "Evaluation",
            {
                "fields": (
                    "public_id",
                    "assessment_attempt",
                    "assessment_version",
                    "student_registration",
                )
            },
        ),
        (
            "Question Summary",
            {
                "fields": (
                    "total_questions",
                    "answered_questions",
                    "skipped_questions",
                    "correct_answers",
                    "incorrect_answers",
                )
            },
        ),
        (
            "Marks",
            {
                "fields": (
                    "obtained_marks",
                    "total_marks",
                    "percentage",
                    "overall_percentile",
                )
            },
        ),
        (
            "Overall Result",
            {
                "fields": (
                    "overall_rating",
                    "overall_level",
                    "evaluation_summary_json",
                )
            },
        ),
        (
            "Evaluation Details",
            {
                "fields": (
                    "evaluation_engine_version",
                    "evaluation_status",
                    "evaluated_by",
                    "evaluated_at",
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

@admin.register(StudentSubsectionEvaluation)
class StudentSubsectionEvaluationAdmin(admin.ModelAdmin):

    # ==========================================================
    # LIST DISPLAY
    # ==========================================================

    list_display = (
        "id",
        "student_registration",
        "assessment_attempt",
        "assessment_version",
        "section",
        "subsection",
        "calculation_formula",
        "formula_case_number",
        "total_questions",
        "answered_questions",
        "correct_answers",
        "incorrect_answers",
        "evaluation_score",
        "evaluation_status",
        "evaluated_at",
    )

    # ==========================================================
    # FILTERS
    # ==========================================================

    list_filter = (
        "evaluation_status",
        "assessment_version",
        "section",
        "subsection",
        "calculation_formula",
        "grade",
        "board",
        "evaluated_at",
        "created_at",
    )

    # ==========================================================
    # SEARCH
    # ==========================================================

    search_fields = (
        "public_id",
        "student_registration__registration_number",
        "student_registration__student__first_name",
        "student_registration__student__last_name",
        "student_registration__student__email",
        "assessment_attempt__id",
        "assessment_version__version_number",
        "section__name",
        "subsection__name",
        "calculation_formula__case_name",
    )

    # ==========================================================
    # DEFAULT ORDERING
    # ==========================================================

    ordering = (
        "-evaluated_at",
        "-created_at",
    )

    # ==========================================================
    # READONLY FIELDS
    # ==========================================================

    readonly_fields = (
        "id",
        "public_id",

        "assessment_attempt",
        "assessment_version",
        "student_registration",

        "section",
        "subsection",
        "grade",
        "board",

        "calculation_formula",
        "formula_case_number",
        "formula_expression",

        "total_questions",
        "answered_questions",
        "skipped_questions",
        "correct_answers",
        "incorrect_answers",

        "raw_score",
        "min_score",
        "max_score",
        "evaluation_score",

        "formula_input_json",

        "evaluation_status",
        "evaluation_engine_version",
        "evaluated_at",

        "created_at",
        "updated_at",
    )

    # ==========================================================
    # FIELDSETS
    # ==========================================================

    fieldsets = (

        (
            "Student & Assessment",
            {
                "fields": (
                    "id",
                    "public_id",
                    "assessment_attempt",
                    "assessment_version",
                    "student_registration",
                )
            }
        ),

        (
            "Blueprint",
            {
                "fields": (
                    "section",
                    "subsection",
                    "grade",
                    "board",
                )
            }
        ),

        (
            "Calculation Formula",
            {
                "fields": (
                    "calculation_formula",
                    "formula_case_number",
                    "formula_expression",
                    "formula_input_json",
                )
            }
        ),

        (
            "Question Statistics",
            {
                "fields": (
                    "total_questions",
                    "answered_questions",
                    "skipped_questions",
                    "correct_answers",
                    "incorrect_answers",
                )
            }
        ),

        (
            "Score",
            {
                "fields": (
                    "raw_score",
                    "min_score",
                    "max_score",
                    "evaluation_score",
                )
            }
        ),

        (
            "Evaluation",
            {
                "fields": (
                    "evaluation_status",
                    "evaluation_engine_version",
                    "evaluated_at",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )

    # ==========================================================
    # READ ONLY ADMIN
    # ==========================================================

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(StudentSubsectionInterpretation)
class StudentSubsectionInterpretationAdmin(admin.ModelAdmin):

    # ==========================================================
    # LIST DISPLAY
    # ==========================================================

    list_display = (
        "id",
        "student_subsection_evaluation",
        "interpretation_rule",
        "created_at",
        "updated_at",
    )

    # ==========================================================
    # FILTERS
    # ==========================================================

    list_filter = (
        "created_at",
        "updated_at",
        "interpretation_rule__status",
        "interpretation_rule__assessment_version",
    )

    # ==========================================================
    # SEARCH
    # ==========================================================

    search_fields = (
        "public_id",

        # Student / Registration
        "student_subsection_evaluation__student_registration__registration_number",

        # Assessment Attempt
        "student_subsection_evaluation__assessment_attempt__id",

        # Subsection
        "student_subsection_evaluation__subsection__name",

        # Interpretation
        "interpretation_rule__rating",
        "interpretation_rule__title",
    )

    # ==========================================================
    # ORDERING
    # ==========================================================

    ordering = (
        "-created_at",
    )

    # ==========================================================
    # READ ONLY FIELDS
    # ==========================================================

    readonly_fields = (
        "id",
        "public_id",
        "student_subsection_evaluation",
        "interpretation_rule",
        "created_at",
        "updated_at",
    )

    # ==========================================================
    # FIELDSETS
    # ==========================================================

    fieldsets = (

        (
            "Student Evaluation",
            {
                "fields": (
                    "id",
                    "public_id",
                    "student_subsection_evaluation",
                )
            }
        ),

        (
            "Interpretation",
            {
                "fields": (
                    "interpretation_rule",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )

    # ==========================================================
    # DISABLE MANUAL CREATE / UPDATE / DELETE
    # ==========================================================

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
