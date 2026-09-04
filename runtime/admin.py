from django.contrib import admin

from runtime.models import AssessmentAssignment, AssessmentAttempt, StudentResponse

# ==========================================================
# Student Response Inline
# ==========================================================

class StudentResponseInline(admin.TabularInline):
    model = StudentResponse
    extra = 0

    fields = (
        "assessment_blueprint_item",
        "question",
        "is_skipped",
        "is_marked_for_review",
        "answered_at",
        "time_spent_seconds",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "assessment_blueprint_item",
    )


# ==========================================================
# Assessment Assignment Admin
# ==========================================================

@admin.register(AssessmentAssignment)
class AssessmentAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_registration",
        "assessment_version",
        "allowed_attempts",
        "attempts_used",
        "assignment_status",
        "assigned_by",
        "assigned_at",
    )

    list_filter = (
        "assignment_status",
        "assessment_version",
    )

    search_fields = (
        "student_registration__registration_number",
        "assessment_version__version_number",
    )

    autocomplete_fields = (
        "student_registration",
        "assessment_version",
        "assigned_by",
    )

    readonly_fields = (
        "public_id",
        "assigned_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-assigned_at",
    )

    fieldsets = (
        (
            "Assignment Information",
            {
                "fields": (
                    "public_id",
                    "student_registration",
                    "assessment_version",
                )
            },
        ),
        (
            "Assignment Settings",
            {
                "fields": (
                    "allowed_attempts",
                    "attempts_used",
                    "due_date",
                    "assignment_status",
                )
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "assigned_by",
                    "remarks",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "assigned_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Assessment Attempt Admin
# ==========================================================

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_assignment",
        "attempt_number",
        "attempt_status",
        "started_at",
        "submitted_at",
        "auto_submitted",
        "total_time_taken_seconds",
    )

    list_filter = (
        "attempt_status",
        "auto_submitted",
    )

    search_fields = (
        "assessment_assignment__student_registration__registration_number",
        "assessment_assignment__assessment_version__version_number",
    )

    autocomplete_fields = (
        "assessment_assignment",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-started_at",
    )

    inlines = [
        StudentResponseInline,
    ]

    fieldsets = (
        (
            "Attempt Information",
            {
                "fields": (
                    "public_id",
                    "assessment_assignment",
                    "attempt_number",
                    "attempt_status",
                )
            },
        ),
        (
            "Timeline",
            {
                "fields": (
                    "started_at",
                    "last_activity_at",
                    "submitted_at",
                    "total_time_taken_seconds",
                )
            },
        ),
        (
            "Device Information",
            {
                "fields": (
                    "ip_address",
                    "device_type",
                    "browser",
                )
            },
        ),
        (
            "Assessment Settings",
            {
                "fields": (
                    "auto_submitted",
                    "assessment_snapshot_json",
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
# Student Response Admin
# ==========================================================

@admin.register(StudentResponse)
class StudentResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assessment_attempt",
        "question",
        "is_skipped",
        "is_marked_for_review",
        "answered_at",
        "time_spent_seconds",
    )

    list_filter = (
        "is_skipped",
        "is_marked_for_review",
    )

    search_fields = (
        "question__question_code",
        "question__question_text",
        "assessment_attempt__assessment_assignment__student_registration__registration_number",
    )

    autocomplete_fields = (
        "assessment_attempt",
        "assessment_blueprint_item",
        "question",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "assessment_attempt",
        "assessment_blueprint_item",
    )

    fieldsets = (
        (
            "Response Information",
            {
                "fields": (
                    "public_id",
                    "assessment_attempt",
                    "assessment_blueprint_item",
                    "question",
                )
            },
        ),
        (
            "Student Response",
            {
                "fields": (
                    "selected_response_json",
                    "is_skipped",
                    "is_marked_for_review",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "answered_at",
                    "time_spent_seconds",
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