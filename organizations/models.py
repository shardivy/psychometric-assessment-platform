import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


# ==========================================================
# Base Model
# ==========================================================

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
# ==========================================================
# Package
# ==========================================================

class Package(BaseModel):
    
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        DEPRECATED = "DEPRECATED", "Deprecated"
    
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )
    assessment_version = models.ForeignKey(
        "assessments.AssessmentVersion",
        on_delete=models.CASCADE,
        related_name="packages",
        null=True,
        blank=True
    )
    grade = models.ForeignKey(
        "assessments.Grade",
        on_delete=models.CASCADE,
        related_name="packages",
        null=True,
        blank=True
    )
    package_name = models.CharField(max_length=200)
    package_features1 = models.TextField(blank=True, null=True)
    package_features2 = models.TextField(blank=True, null=True)
    package_features3 = models.TextField(blank=True, null=True)
    package_features4 = models.TextField(blank=True, null=True)
    package_features5 = models.TextField(blank=True, null=True)
    package_price = models.IntegerField()
    package_description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    package_deliverable1 = models.TextField(blank=True, null=True)
    package_deliverable2 = models.TextField(blank=True, null=True)
    package_deliverable3 = models.TextField(blank=True, null=True)
    package_deliverable4 = models.TextField(blank=True, null=True)
    package_deliverable5 = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = "packages"
        ordering = ["package_name"]
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["assessment_version"]),
            models.Index(fields=["package_name"]),
            models.Index(fields=["status"]),
        ]
        
    def __str__(self):
        return f"{self.package_name} ({self.assessment_version.version_number})"
    

# ==========================================================
# Organization
# ==========================================================

class Organization(BaseModel):

    class OrganizationType(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        COLLEGE = "COLLEGE", "College"
        COACHING_INSTITUTE = "COACHING_INSTITUTE", "Coaching Institute"
        COUNSELLOR = "COUNSELLOR", "Independent Counsellor"
        ENTERPRISE = "ENTERPRISE", "Enterprise"
        NGO = "NGO", "NGO"
        FRANCHISE = "FRANCHISE", "Franchise"
        OTHER =  "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft" 
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"
        ARCHIVED = "ARCHIVED", "Archived"

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
        unique=True,
        blank=True,
        null=True
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
    
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="created_organizations"
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
    
# ============================================================
# ORGANIZATION MEMBER
# ============================================================
    
class OrganizationMember(models.Model):

    class MemberType(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        COUNSELLOR = "COUNSELLOR", "Counsellor"
        TEACHER = "TEACHER", "Teacher"
        COORDINATOR = "COORDINATOR", "Coordinator"
        STAFF = "STAFF", "Staff"

    class Status(models.TextChoices):
        INVITED = "INVITED", "Invited"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        REMOVED = "REMOVED", "Removed"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships"
    )

    member_type = models.CharField(
        max_length=40,
        choices=MemberType.choices
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED
    )

    joined_at = models.DateTimeField(
        null=True,
        blank=True
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invitations"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "organization_members"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_user"
            )
        ]
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["user"]),
            models.Index(fields=["member_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.user}"
    
    
class OrganizationPackage(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        SUSPENDED = "SUSPENDED", "Suspended"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.BigAutoField(
        primary_key=True
    )

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="organization_packages"
    )

    package = models.ForeignKey(
        "organizations.Package",
        on_delete=models.PROTECT,
        related_name="organization_packages"
    )

    contract_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    negotiated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        null=True,
        blank=True
    )

    currency = models.CharField(
        max_length=3,
        default="INR",
        blank=True,
        null=True
    )

    seat_limit = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ],
        null=True,
        blank=True
    )

    used_seats = models.PositiveIntegerField(
        default=0
    )

    valid_from = models.DateField()

    valid_until = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_organization_packages"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "organization_packages"
        ordering = ["-created_at"]
        
        constraints = [
        models.UniqueConstraint(
            fields=["organization", "package"],
            name="unique_organization_package"
        )
    ]

    indexes = [
        models.Index(fields=["organization"]),
        models.Index(fields=["package"]),
        models.Index(fields=["status"]),
        models.Index(fields=["valid_from"]),
        models.Index(fields=["valid_until"]),
    ]

    def __str__(self):
        return f"{self.organization.name} - {self.package.package_name}"

    @property
    def available_seats(self):
        return self.seat_limit - self.used_seats
    
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

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="registration_links"
    )

    token_hash = models.CharField(
        max_length=255
    )

    public_slug = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    link_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    max_registrations = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    registration_count = models.PositiveIntegerField(
        default=0
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
        ordering = ["-created_at"]
        
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["public_slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return self.public_slug

    def is_valid(self):
        if self.status != self.Status.ACTIVE:
            return False

        if (
            self.expires_at
            and timezone.now() >= self.expires_at
        ):
            return False

        if (
            self.max_registrations is not None
            and self.registration_count >= self.max_registrations
        ):
            return False

        if self.organization.status != Organization.Status.ACTIVE:
            return False

        return True   
