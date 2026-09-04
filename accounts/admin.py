from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import OrganizationMember, Permission, Role, RolePermission, User, UserRole

# ==========================================================
# User Admin
# ==========================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "mobile",
        "status",
        "is_active",
        "is_staff",
        "is_email_verified",
        "created_at",
    )

    list_filter = (
        "status",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "is_mobile_verified",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
        "mobile",
        "public_id",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "last_login",
        "last_login_at",
        "password_changed_at",
    )

    fieldsets = (
        ("Login Information", {
            "fields": (
                "email",
                "password",
            )
        }),
        ("Personal Information", {
            "fields": (
                "first_name",
                "last_name",
                "mobile",
                "profile_photo",
            )
        }),
        ("Verification", {
            "fields": (
                "is_email_verified",
                "is_mobile_verified",
            )
        }),
        ("Status", {
            "fields": (
                "status",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Permissions", {
            "fields": (
                "groups",
                "user_permissions",
            )
        }),
        ("Audit", {
            "fields": (
                "public_id",
                "last_login",
                "last_login_at",
                "password_changed_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "mobile",
                    "password1",
                    "password2",
                    "status",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


# ==========================================================
# Role Admin
# ==========================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "status",
        "is_system_role",
        "created_at",
    )

    list_filter = (
        "status",
        "is_system_role",
    )

    search_fields = (
        "code",
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("name",)


# ==========================================================
# Permission Admin
# ==========================================================

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "module",
        "code",
        "name",
        "status",
        "created_at",
    )

    list_filter = (
        "module",
        "status",
    )

    search_fields = (
        "module",
        "code",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "module",
        "name",
    )


# ==========================================================
# Role Permission Admin
# ==========================================================

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role",
        "permission",
        "created_at",
    )

    list_filter = (
        "role",
        "permission__module",
    )

    search_fields = (
        "role__name",
        "permission__name",
        "permission__code",
    )

    autocomplete_fields = (
        "role",
        "permission",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ==========================================================
# User Role Admin
# ==========================================================

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "role",
        "assigned_by",
        "is_active",
        "assigned_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "role__name",
    )

    autocomplete_fields = (
        "user",
        "role",
        "assigned_by",
    )

    readonly_fields = (
        "assigned_at",
        "created_at",
        "updated_at",
    )


# ==========================================================
# Organization Member Admin
# ==========================================================

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "user",
        "employee_code",
        "designation",
        "status",
        "is_primary",
    )

    list_filter = (
        "organization",
        "status",
        "is_primary",
    )

    search_fields = (
        "organization__name",
        "user__email",
        "user__first_name",
        "user__last_name",
        "employee_code",
        "designation",
    )

    autocomplete_fields = (
        "organization",
        "user",
        "reporting_to",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "organization",
        "user",
    )