from django.contrib import admin

from students.models import Student, StudentRegistration

# ==========================================================
# Student Registration Inline
# ==========================================================

class StudentRegistrationInline(admin.TabularInline):
    model = StudentRegistration
    extra = 0

    fields = (
        "organization",
        "campaign",
        "registration_number",
        "grade",
        "class_name",
        "section",
        "registration_status",
        "registered_at",
    )

    readonly_fields = (
        "registered_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-registered_at",
    )


# ==========================================================
# Student Admin
# ==========================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_code",
        "first_name",
        "last_name",
        "user",
        "gender",
        "parent_mobile",
        "status",
        "created_at",
    )

    list_filter = (
        "gender",
        "status",
    )

    search_fields = (
        "student_code",
        "first_name",
        "last_name",
        "user__email",
        "parent_name",
        "parent_mobile",
    )

    autocomplete_fields = (
        "user",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "first_name",
        "last_name",
    )

    inlines = [
        StudentRegistrationInline,
    ]

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "public_id",
                    "user",
                    "student_code",
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Personal Details",
            {
                "fields": (
                    "gender",
                    "date_of_birth",
                    "blood_group",
                    "profile_photo",
                )
            },
        ),
        (
            "Parent Information",
            {
                "fields": (
                    "parent_name",
                    "parent_mobile",
                    "emergency_contact",
                )
            },
        ),
        (
            "Status",
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
# Student Registration Admin
# ==========================================================

@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "registration_number",
        "student",
        "organization",
        "campaign",
        "grade",
        "class_name",
        "registration_status",
        "registered_at",
    )

    list_filter = (
        "registration_status",
        "organization",
        "campaign",
        "academic_year",
        "grade",
    )

    search_fields = (
        "registration_number",
        "student__student_code",
        "student__first_name",
        "student__last_name",
        "organization__name",
        "campaign__name",
        "roll_number",
        "admission_number",
    )

    autocomplete_fields = (
        "student",
        "organization",
        "campaign",
        "registration_channel",
        "registration_link",
        "assigned_counsellor",
    )

    readonly_fields = (
        "public_id",
        "registered_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-registered_at",
    )

    fieldsets = (
        (
            "Registration Information",
            {
                "fields": (
                    "public_id",
                    "student",
                    "organization",
                    "campaign",
                )
            },
        ),
        (
            "Registration Details",
            {
                "fields": (
                    "registration_channel",
                    "registration_link",
                    "registration_number",
                    "registration_status",
                    "registered_at",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "admission_number",
                    "roll_number",
                    "grade",
                    "class_name",
                    "section",
                    "academic_year",
                )
            },
        ),
        (
            "Counsellor",
            {
                "fields": (
                    "assigned_counsellor",
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