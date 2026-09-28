import uuid

from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        email,
        password=None,
        first_name="",
        last_name="",
        **extra_fields,
    ):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        password,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Master User Model
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        BLOCKED = "BLOCKED", "Blocked"
        DELETED = "DELETED", "Deleted"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    email = models.EmailField(
        unique=True,
        max_length=255,
    )

    mobile = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    profile_photo = models.URLField(
        blank=True,
        null=True,
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    is_mobile_verified = models.BooleanField(
        default=False,
    )

    last_login_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    password_changed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Django Required Fields

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"

        ordering = [
            "first_name",
            "last_name",
        ]

        verbose_name = "User"
        verbose_name_plural = "Users"

        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["mobile"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()
    
class EmailVerificationOTP(models.Model):

    id = models.BigAutoField(
        primary_key=True
    )

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_otps"
    )

    otp = models.CharField(
        max_length=6
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(
        default=False
    )

    attempts = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "email_verification_otps"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["otp"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.otp}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

class PasswordResetOTP(models.Model):

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = models.BigAutoField(
        primary_key=True
    )

    # ==================================================
    # PUBLIC ID
    # ==================================================

    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    # ==================================================
    # USER
    # ==================================================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_otps"
    )

    # ==================================================
    # OTP
    # ==================================================

    otp = models.CharField(
        max_length=6
    )

    # ==================================================
    # EXPIRY
    # ==================================================

    expires_at = models.DateTimeField()

    # ==================================================
    # STATUS
    # ==================================================

    is_verified = models.BooleanField(
        default=False
    )

    is_used = models.BooleanField(
        default=False
    )

    # ==================================================
    # CREATED / UPDATED
    # ==================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "password_reset_otps"

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=["user"]
            ),
            models.Index(
                fields=["otp"]
            ),
            models.Index(
                fields=["expires_at"]
            ),
        ]

    def is_expired(self):

        return timezone.now() > self.expires_at

    def __str__(self):

        return (
            f"{self.user.email} - "
            f"{self.otp}"
        )
    
class Role(models.Model):
    """
    Master Role model.
    Defines the different roles available in the platform.
    """
    
    class RoleName(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN", "Organization Admin"
        COUNSELLOR = "COUNSELLOR", "Counsellor"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent"
        VIEWER = "VIEWER", "Viewer"
        SUPPORT = "SUPPORT", "Support Executive"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # ---------------------------------
    # Primary Key
    # ---------------------------------
    id = models.BigAutoField(primary_key=True)

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique role code"
    )

    name = models.CharField(
        max_length=100,
        choices=RoleName.choices,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_system_role = models.BooleanField(
        default=True,
        help_text="True if this role is created by the system."
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
        db_table = "roles"

        verbose_name = "Role"
        verbose_name_plural = "Roles"

        ordering = ["name"]

        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_system_role"]),
        ]

    def __str__(self):
        return self.name
    
class Permission(models.Model):
    """
    Master Permission Model
    Stores all permissions available in the platform.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # ---------------------------------
    # Primary Key
    # ---------------------------------
    id = models.BigAutoField(primary_key=True)

    module = models.CharField(
        max_length=100,
        help_text="Module name (Assessment, Student, Report, etc.)"
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique permission code"
    )

    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
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
        db_table = "permissions"

        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

        ordering = ["module", "name"]

        indexes = [
            models.Index(fields=["module"]),
            models.Index(fields=["code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.module} - {self.name}"
    
class RolePermission(models.Model):
    """
    Maps Roles to Permissions.
    One Role -> Many Permissions
    One Permission -> Many Roles
    """

    # -----------------------------
    # Primary Key
    # -----------------------------
    id = models.BigAutoField(primary_key=True)

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions"
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "role_permissions"

        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"

        ordering = [
            "role",
            "permission"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission"
            )
        ]

        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["permission"]),
        ]

    def __str__(self):
        return f"{self.role.name} -> {self.permission.code}"
    
class UserRole(models.Model):
    """
    Maps Users to Roles.
    A user can have one or more roles.
    """

    # ---------------------------------
    # Primary Key
    # ---------------------------------
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles"
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles"
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_roles",
        null=True,
        blank=True
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "user_roles"

        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

        ordering = [
            "user",
            "role"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role"
            )
        ]

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"
    
