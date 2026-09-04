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
# Organization
# ==========================================================

class Organization(BaseModel):

    class OrganizationType(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        COLLEGE = "COLLEGE", "College"
        COACHING = "COACHING", "Coaching Institute"
        COUNSELLOR = "COUNSELLOR", "Independent Counsellor"
        ENTERPRISE = "ENTERPRISE", "Enterprise"
        NGO = "NGO", "NGO"
        FRANCHISE = "FRANCHISE", "Franchise"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    # Auto Increment Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    organization_code = models.CharField(
        max_length=20,
        unique=True
    )

    organization_type = models.CharField(
        max_length=20,
        choices=OrganizationType.choices
    )

    name = models.CharField(
        max_length=255
    )

    short_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    logo_url = models.URLField(
        blank=True,
        null=True
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kolkata"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        db_table = "organizations"
        ordering = ["name"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["organization_code"]),
            models.Index(fields=["organization_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization_code})"
    
# ==========================================================
# Campaign
# ==========================================================   

class Campaign(BaseModel):
    """
    Represents an assessment campaign for an organization.

    Examples:
    - Career Assessment 2026
    - Grade 10 Assessment
    - Summer Career Program
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="campaigns"
    )

    campaign_code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    # Temporary (Replace with FK after Assessment model is created)
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.PROTECT,
        related_name="campaigns"
    )

    start_date = models.DateField()

    end_date = models.DateField()

    max_attempts = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_campaigns"
    )

    class Meta:
        db_table = "campaigns"

        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["campaign_code"]),
            models.Index(fields=["assessment"]),
            models.Index(fields=["status"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.campaign_code})"
    
class RegistrationChannel(models.Model):
    """
    Represents how students enter a campaign.
    Example:
    - Class 10-A
    - Website
    - QR Code
    - Counsellor
    """

    class ChannelType(models.TextChoices):
        CLASS = "CLASS", "Class"
        SECTION = "SECTION", "Section"
        WEBSITE = "WEBSITE", "Website"
        QR_CODE = "QR_CODE", "QR Code"
        COUNSELLOR = "COUNSELLOR", "Counsellor"
        SEMINAR = "SEMINAR", "Seminar"
        EXTERNAL_PARTNER = "EXTERNAL_PARTNER", "External Partner"
        BULK_IMPORT = "BULK_IMPORT", "Bulk Import"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # ----------------------------------------------------
    # Primary Key
    # ----------------------------------------------------
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="registration_channels",
    )

    channel_code = models.CharField(
        max_length=30,
        unique=True,
    )

    channel_name = models.CharField(
        max_length=100,
    )

    channel_type = models.CharField(
        max_length=30,
        choices=ChannelType.choices,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    display_order = models.PositiveIntegerField(
        blank=True,
        null=True,
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
        db_table = "registration_channels"

        verbose_name = "Registration Channel"
        verbose_name_plural = "Registration Channels"

        ordering = ["display_order", "channel_name"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["campaign"]),
            models.Index(fields=["channel_code"]),
            models.Index(fields=["channel_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.channel_name} ({self.campaign.name})"
    
class RegistrationLink(models.Model):
    """
    Registration entry point for students.

    Every student enters the platform through a Registration Link.

    Example:
    https://assessment.truemindpath.com/r/e4WzEwV2
    """

    class RegistrationChannel(models.TextChoices):
        CLASS_6 = "CLASS_6", "Class 6"
        CLASS_7 = "CLASS_7", "Class 7"
        CLASS_8 = "CLASS_8", "Class 8"
        CLASS_9 = "CLASS_9", "Class 9"
        CLASS_10 = "CLASS_10", "Class 10"
        CLASS_11 = "CLASS_11", "Class 11"
        CLASS_12 = "CLASS_12", "Class 12"
        COLLEGE = "COLLEGE", "College"
        WEBSITE = "WEBSITE", "Website"
        QR_CODE = "QR_CODE", "QR Code"
        COUNSELLOR = "COUNSELLOR", "Counsellor"
        BULK_IMPORT = "BULK_IMPORT", "Bulk Import"
        DIRECT_LINK = "DIRECT_LINK", "Direct Link"

    class RegistrationSource(models.TextChoices):
        URL = "URL", "URL"
        QR_CODE = "QR_CODE", "QR Code"
        MANUAL = "MANUAL", "Manual"
        API = "API", "API"
        EXCEL_IMPORT = "EXCEL_IMPORT", "Excel Import"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="registration_links"
    )

    link_code = models.CharField(
        max_length=100,
        unique=True
    )

    registration_channel = models.CharField(
        max_length=30,
        choices=RegistrationChannel.choices
    )

    registration_source = models.CharField(
        max_length=30,
        choices=RegistrationSource.choices
    )

    display_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Temporary
    assessment_version = models.ForeignKey(
        "assessments.AssessmentVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    max_registrations = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    registrations_count = models.PositiveIntegerField(
        default=0
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    allow_duplicate_email = models.BooleanField(
        default=False
    )

    allow_duplicate_mobile = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_registration_links"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "registration_links"

        verbose_name = "Registration Link"
        verbose_name_plural = "Registration Links"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["campaign"]),
            models.Index(fields=["link_code"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.display_name or self.link_code}" 
    
