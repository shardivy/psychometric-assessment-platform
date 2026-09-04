import uuid

from django.db import models

# ==========================================================
# Base Model
# ==========================================================

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ==========================================================
# Choices
# ==========================================================

class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
    EXPORT = "EXPORT", "Export"
    IMPORT = "IMPORT", "Import"


class ActivityType(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    DASHBOARD = "DASHBOARD", "Dashboard"
    ASSESSMENT = "ASSESSMENT", "Assessment"
    REPORT = "REPORT", "Report"
    CAMPAIGN = "CAMPAIGN", "Campaign"
    STUDENT = "STUDENT", "Student"
    ORGANIZATION = "ORGANIZATION", "Organization"


# ==========================================================
# Audit Log
# ==========================================================

class AuditLog(BaseModel):
    """
    Stores all create/update/delete actions.
    """

    id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )

    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices
    )

    entity_name = models.CharField(
        max_length=100
    )

    entity_id = models.CharField(
        max_length=100
    )

    old_value = models.JSONField(
        null=True,
        blank=True
    )

    new_value = models.JSONField(
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "audit_logs"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["entity_name"]),
            models.Index(fields=["entity_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.entity_name}"

# ==========================================================
# Activity Log
# ==========================================================

class ActivityLog(BaseModel):
    """
    Stores user activities.
    """

    id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs"
    )

    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    reference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    device = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    browser = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        db_table = "activity_logs"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["activity_type"]),
            models.Index(fields=["reference_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.activity_type}"