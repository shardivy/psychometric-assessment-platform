from django.contrib import admin

from audit.models import ActivityLog, AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "entity_name",
        "entity_id",
        "ip_address",
        "created_at",
    )

    list_filter = (
        "action",
        "entity_name",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__full_name",
        "entity_name",
        "entity_id",
    )

    readonly_fields = (
        "id",
        "user",
        "action",
        "entity_name",
        "entity_id",
        "old_value",
        "new_value",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "activity_type",
        "title",
        "reference_id",
        "ip_address",
        "device",
        "browser",
        "created_at",
    )

    list_filter = (
        "activity_type",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__full_name",
        "title",
        "description",
        "reference_id",
    )

    readonly_fields = (
        "id",
        "user",
        "activity_type",
        "title",
        "description",
        "reference_id",
        "ip_address",
        "device",
        "browser",
        "metadata",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25
