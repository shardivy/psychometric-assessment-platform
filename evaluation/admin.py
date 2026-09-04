from django.contrib import admin

from evaluation.models import EvaluationResult

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


