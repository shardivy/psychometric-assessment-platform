from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import EmailVerificationOTP, PasswordResetOTP, UserRole
from accounts.utils import generate_otp, send_email_verification_otp
from students.models import Student

User = get_user_model()

# ============================================================
# SEND EMAIL OTP SERIALIZER
# ============================================================

class SendStudentEmailOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):

        return value.lower().strip()

    def create(self, validated_data):

        email = validated_data["email"]

        # ====================================================
        # GET OR CREATE USER
        # ====================================================

        user = User.objects.filter(
            email=email
        ).first()

        if not user:

            user = User.objects.create(
                email=email,
                first_name="",
                is_email_verified=False,
            )

        # ====================================================
        # IF ALREADY VERIFIED
        # ====================================================

        if user.is_email_verified:

            return {
                "user": user,
                "already_verified": True,
            }

        # ====================================================
        # GENERATE OTP
        # ====================================================

        otp = generate_otp()

        # ====================================================
        # DELETE OLD OTP
        # ====================================================

        EmailVerificationOTP.objects.filter(
            user=user,
            is_verified=False
        ).delete()

        # ====================================================
        # CREATE NEW OTP
        # ====================================================

        EmailVerificationOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(
                minutes=10
            )
        )

        # ====================================================
        # SEND OTP EMAIL
        # ====================================================

        send_email_verification_otp(
            email=user.email,
            otp=otp
        )

        return {
            "user": user,
            "already_verified": False,
        }


# ============================================================
# VERIFY EMAIL OTP SERIALIZER
# ============================================================

class VerifyStudentEmailOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(
        max_length=6,
        min_length=6
    )

    def validate(self, attrs):

        email = attrs["email"].lower().strip()
        otp = attrs["otp"]

        # ====================================================
        # GET USER
        # ====================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "No registration request found "
                    "for this email."
                )
            })

        # ====================================================
        # ALREADY VERIFIED
        # ====================================================

        if user.is_email_verified:

            attrs["_user"] = user

            return attrs

        # ====================================================
        # GET LATEST OTP
        # ====================================================

        verification_otp = (
            EmailVerificationOTP.objects
            .filter(
                user=user,
                is_verified=False
            )
            .order_by("-created_at")
            .first()
        )

        if not verification_otp:

            raise serializers.ValidationError({
                "otp": (
                    "OTP not found. "
                    "Please request a new OTP."
                )
            })

        # ====================================================
        # CHECK EXPIRY
        # ====================================================

        if timezone.now() >= verification_otp.expires_at:

            raise serializers.ValidationError({
                "otp": (
                    "OTP has expired. "
                    "Please request a new OTP."
                )
            })

        # ====================================================
        # CHECK OTP
        # ====================================================

        if verification_otp.otp != otp:

            # Optional: increase failed attempt count
            verification_otp.attempts += 1
            verification_otp.save(
                update_fields=[
                    "attempts",
                    "updated_at"
                ]
            )

            raise serializers.ValidationError({
                "otp": "Invalid OTP."
            })

        attrs["_user"] = user
        attrs["_verification_otp"] = verification_otp

        return attrs

    def create(self, validated_data):

        user = validated_data["_user"]

        verification_otp = validated_data.get(
            "_verification_otp"
        )

        # ====================================================
        # MARK EMAIL AS VERIFIED
        # ====================================================

        user.is_email_verified = True

        user.save(
            update_fields=[
                "is_email_verified",
                "updated_at",
            ]
        )

        # ====================================================
        # MARK OTP AS VERIFIED
        # ====================================================

        if verification_otp:

            verification_otp.is_verified = True

            verification_otp.save(
                update_fields=[
                    "is_verified",
                    "updated_at",
                ]
            )

        return user
    
class StudentLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):

        email = attrs["email"].lower().strip()
        password = attrs["password"]

        # ==================================================
        # GET USER
        # ==================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": "Invalid email or password."
            })

        # ==================================================
        # CHECK PASSWORD
        # ==================================================

        if not user.check_password(password):

            raise serializers.ValidationError({
                "password": "Invalid email or password."
            })

        # ==================================================
        # CHECK EMAIL VERIFIED
        # ==================================================

        if not user.is_email_verified:

            raise serializers.ValidationError({
                "email": (
                    "Email is not verified. "
                    "Please verify your email first."
                )
            })

        # ==================================================
        # CHECK STUDENT ROLE
        # ==================================================

        student_role = (
            UserRole.objects
            .select_related("role")
            .filter(
                user=user,
                role__name="STUDENT",
                is_active=True
            )
            .first()
        )

        if not student_role:

            raise serializers.ValidationError({
                "email": (
                    "This account is not registered "
                    "as a student."
                )
            })

        # ==================================================
        # GET STUDENT
        # ==================================================

        try:

            student = Student.objects.get(
                user=user
            )

        except Student.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "Student profile not found "
                    "for this account."
                )
            })

        # ==================================================
        # GENERATE JWT
        # ==================================================

        refresh = RefreshToken.for_user(user)

        attrs["user"] = user
        attrs["student"] = student
        attrs["role"] = student_role.role
        attrs["access_token"] = str(
            refresh.access_token
        )
        attrs["refresh_token"] = str(
            refresh
        )

        return attrs
    
class StudentForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate(self, attrs):

        email = attrs["email"].lower().strip()

        attrs["email"] = email

        # ==================================================
        # GET USER
        # ==================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "No account found with this email."
                )
            })

        # ==================================================
        # CHECK STUDENT
        # ==================================================

        if not Student.objects.filter(
            user=user
        ).exists():

            raise serializers.ValidationError({
                "email": (
                    "This email is not registered "
                    "with a student account."
                )
            })

        # ==================================================
        # CHECK STUDENT ROLE
        # ==================================================

        student_role_exists = (
            UserRole.objects
            .filter(
                user=user,
                role__name="STUDENT",
                is_active=True
            )
            .exists()
        )

        if not student_role_exists:

            raise serializers.ValidationError({
                "email": (
                    "This account is not registered "
                    "as a student."
                )
            })

        attrs["user"] = user

        return attrs
    
class VerifyPasswordResetOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(
        max_length=6,
        min_length=6
    )

    def validate(self, attrs):

        email = attrs["email"].lower().strip()

        otp = attrs["otp"].strip()

        # ==================================================
        # GET USER
        # ==================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "Invalid email or OTP."
                )
            })

        # ==================================================
        # GET LATEST OTP
        # ==================================================

        password_reset_otp = (
            PasswordResetOTP.objects
            .filter(
                user=user,
                otp=otp,
                is_used=False
            )
            .order_by("-created_at")
            .first()
        )

        if not password_reset_otp:

            raise serializers.ValidationError({
                "otp": "Invalid OTP."
            })

        # ==================================================
        # CHECK EXPIRY
        # ==================================================

        if password_reset_otp.is_expired():

            raise serializers.ValidationError({
                "otp": (
                    "OTP has expired. "
                    "Please request a new OTP."
                )
            })

        # ==================================================
        # MARK VERIFIED
        # ==================================================

        password_reset_otp.is_verified = True

        password_reset_otp.save(
            update_fields=[
                "is_verified",
                "updated_at"
            ]
        )

        attrs["user"] = user

        attrs[
            "password_reset_otp"
        ] = password_reset_otp

        return attrs

class StudentResetPasswordSerializer(serializers.Serializer):

    # ==================================================
    # EMAIL
    # ==================================================

    email = serializers.EmailField()

    # ==================================================
    # PASSWORD
    # ==================================================

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    # ==================================================
    # CONFIRM PASSWORD
    # ==================================================

    confirm_password = serializers.CharField(
        write_only=True
    )

    # ==================================================
    # VALIDATION
    # ==================================================

    def validate(self, attrs):

        email = attrs["email"].lower().strip()

        password = attrs["password"]

        confirm_password = attrs[
            "confirm_password"
        ]

        # ==================================================
        # CHECK PASSWORD MATCH
        # ==================================================

        if password != confirm_password:

            raise serializers.ValidationError({
                "confirm_password": (
                    "Password and confirm password "
                    "do not match."
                )
            })

        # ==================================================
        # GET USER
        # ==================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "No account found with this email."
                )
            })

        # ==================================================
        # CHECK STUDENT
        # ==================================================

        if not Student.objects.filter(
            user=user
        ).exists():

            raise serializers.ValidationError({
                "email": (
                    "This email is not registered "
                    "with a student account."
                )
            })

        # ==================================================
        # CHECK STUDENT ROLE
        # ==================================================

        student_role_exists = (
            UserRole.objects
            .filter(
                user=user,
                role__name="STUDENT",
                is_active=True
            )
            .exists()
        )

        if not student_role_exists:

            raise serializers.ValidationError({
                "email": (
                    "This account is not registered "
                    "as a student."
                )
            })

        # ==================================================
        # GET VERIFIED OTP
        # ==================================================

        password_reset_otp = (
            PasswordResetOTP.objects
            .filter(
                user=user,
                is_verified=True,
                is_used=False
            )
            .order_by("-created_at")
            .first()
        )

        if not password_reset_otp:

            raise serializers.ValidationError({
                "email": (
                    "Please verify the OTP first "
                    "before resetting your password."
                )
            })

        # ==================================================
        # CHECK OTP EXPIRY
        # ==================================================

        if password_reset_otp.is_expired():

            raise serializers.ValidationError({
                "email": (
                    "OTP verification has expired. "
                    "Please request a new OTP."
                )
            })

        # ==================================================
        # STORE INTERNAL DATA
        # ==================================================

        attrs["_user"] = user

        attrs[
            "_password_reset_otp"
        ] = password_reset_otp

        return attrs

