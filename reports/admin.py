from django.contrib import admin

from reports.models import ReportFile, ReportInstance, ReportTemplate

# ==========================================================
# Report File Inline
# ==========================================================

class ReportFileInline(admin.TabularInline):
    model = ReportFile
    extra = 0

    fields = (
        "file_type",
        "file_name",
        "storage_provider",
        "file_size_kb",
        "download_count",
        "generated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-generated_at",
    )


# ==========================================================
# Report Template Admin
# ==========================================================

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "template_code",
        "name",
        "report_type",
        "version",
        "language",
        "is_default",
        "status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "report_type",
        "status",
        "language",
        "is_default",
    )

    search_fields = (
        "template_code",
        "name",
        "version",
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
        "name",
    )

    fieldsets = (
        (
            "Template Information",
            {
                "fields": (
                    "public_id",
                    "template_code",
                    "name",
                    "report_type",
                    "version",
                    "description",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "template_config_json",
                    "language",
                    "is_default",
                    "status",
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
# Report Instance Admin
# ==========================================================

@admin.register(ReportInstance)
class ReportInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_registration",
        "report_title",
        "report_version",
        "report_template",
        "status",
        "generated_at",
    )

    list_filter = (
        "status",
        "report_template",
    )

    search_fields = (
        "report_title",
        "report_version",
        "student_registration__registration_number",
    )

    autocomplete_fields = (
        "report_template",
        "evaluation_result",
        "student_registration",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-generated_at",
    )

    inlines = [
        ReportFileInline,
    ]

    fieldsets = (
        (
            "Report Information",
            {
                "fields": (
                    "public_id",
                    "report_template",
                    "evaluation_result",
                    "student_registration",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "report_title",
                    "report_version",
                    "report_json",
                    "report_metadata_json",
                )
            },
        ),
        (
            "Generation",
            {
                "fields": (
                    "generated_by",
                    "generated_at",
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
# Report File Admin
# ==========================================================

@admin.register(ReportFile)
class ReportFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "report_instance",
        "file_name",
        "file_type",
        "storage_provider",
        "file_size_kb",
        "download_count",
        "generated_at",
    )

    list_filter = (
        "file_type",
        "storage_provider",
    )

    search_fields = (
        "file_name",
        "report_instance__report_title",
        "report_instance__student_registration__registration_number",
    )

    autocomplete_fields = (
        "report_instance",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-generated_at",
    )

    fieldsets = (
        (
            "File Information",
            {
                "fields": (
                    "public_id",
                    "report_instance",
                    "file_type",
                    "file_name",
                    "file_path",
                )
            },
        ),
        (
            "Storage",
            {
                "fields": (
                    "storage_provider",
                    "file_size_kb",
                    "download_count",
                    "generated_at",
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
