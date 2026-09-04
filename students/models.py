import uuid

from django.db import models

from organizations.models import Campaign, Organization, RegistrationChannel, RegistrationLink

class Student(models.Model):
    """
    Master Student Profile

    This table stores only the student's master information.
    It is independent of organizations and campaigns.
    """

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        BLOCKED = "BLOCKED", "Blocked"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    student_code = models.CharField(
        max_length=30,
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )
    
    blood_group = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )
    
    profile_photo = models.URLField(
        blank=True,
        null=True,
        help_text="S3/CDN Profile Photo URL"
    )

    parent_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    parent_mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True   
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "students"

        verbose_name = "Student"
        verbose_name_plural = "Students"

        ordering = ["first_name", "last_name"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["student_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name} ({self.student_code})"
        return f"{self.first_name} ({self.student_code})" 
    
class StudentRegistration(models.Model):
    """
    Represents one registration event.

    A student can register multiple times in different
    organizations/campaigns.
    """

    class RegistrationStatus(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        ASSESSMENT_ASSIGNED = "ASSESSMENT_ASSIGNED", "Assessment Assigned"
        STARTED = "STARTED", "Started"
        COMPLETED = "COMPLETED", "Completed"
        REPORT_GENERATED = "REPORT_GENERATED", "Report Generated"
        COUNSELLING_PENDING = "COUNSELLING_PENDING", "Counselling Pending"
        COUNSELLING_COMPLETED = "COUNSELLING_COMPLETED", "Counselling Completed"

    # Primary Key
    id = models.BigAutoField(primary_key=True)

    # Public UUID
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="student_registrations"
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="student_registrations"
    )
    
    registration_channel = models.ForeignKey(
        RegistrationChannel,    
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_registrations_channel"
    )

    registration_link = models.ForeignKey(
        RegistrationLink,
        on_delete=models.CASCADE,
        related_name="student_registrations"
    )

    registration_number = models.CharField(
        max_length=50,
        unique=True
    )

    admission_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    roll_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    
    grade = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    class_name = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    section = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    academic_year = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    assigned_counsellor = models.ForeignKey(
        "accounts.OrganizationMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_counsellor"
    )

    registration_status = models.CharField(
        max_length=30,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.REGISTERED
    )

    registered_at = models.DateTimeField(
        auto_now_add=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "student_registrations"

        verbose_name = "Student Registration"
        verbose_name_plural = "Student Registrations"

        ordering = ["-registered_at"]

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["student"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["campaign"]),
            models.Index(fields=["registration_channel"]),
            models.Index(fields=["registration_link"]),
            models.Index(fields=["registration_number"]),
            models.Index(fields=["registration_status"]),
            models.Index(fields=["academic_year"]),
            models.Index(fields=["registered_at"]),
        ]

    def __str__(self):
        return f"{self.registration_number} - {self.student}"


