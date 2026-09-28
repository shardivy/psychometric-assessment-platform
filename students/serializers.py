from datetime import timedelta

from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from assessments.models import Grade
from accounts.models import EmailVerificationOTP, Role, UserRole
from accounts.utils import generate_otp, send_email_verification_otp
from organizations.models import Package, RegistrationLink
from students.models import Order, Student, StudentRegistration

User = get_user_model()


# ============================================================
# STUDENT REGISTRATION SERIALIZER
# ============================================================

class StudentRegistrationSerializer(serializers.Serializer):

    # ========================================================
    # REGISTRATION LINK
    # ========================================================

    registration_token = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )

    # ========================================================
    # DIRECT REGISTRATION PACKAGE
    # ========================================================

    package_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True
    )

    # ========================================================
    # USER DETAILS
    # ========================================================

    email = serializers.EmailField()

    mobile = serializers.CharField(
        max_length=20
    )

    first_name = serializers.CharField(
        max_length=100
    )

    last_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    password = serializers.CharField(
        write_only=True
    )
    
    confirm_password = serializers.CharField(
        write_only=True
    )

    # ========================================================
    # STUDENT DETAILS
    # ========================================================

    gender = serializers.ChoiceField(
        choices=Student.Gender.choices,
        required=False,
        allow_null=True
    )

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True
    )

    blood_group = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    parent_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    parent_mobile = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    emergency_contact = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # ========================================================
    # REGISTRATION DETAILS
    # ========================================================

    grade_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    class_name = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    section = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    academic_year = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    registration_type = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self, attrs):

        email = attrs["email"].lower().strip()
        mobile = attrs["mobile"].strip()

        attrs["email"] = email
        attrs["mobile"] = mobile
        
        # ====================================================
        # CHECK PASSWORD CONFIRMATION
        # ====================================================

        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:

            raise serializers.ValidationError({
                "confirm_password": (
                    "Password and confirm password do not match."
                )
            })

        # ====================================================
        # CHECK EMAIL ALREADY EXISTS
        # ====================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": (
                    "No registration request found for this email. "
                    "Please verify your email first using the OTP."
                )
            })

        # ====================================================
        # CHECK EMAIL VERIFIED
        # ====================================================

        if not user.is_email_verified:

            raise serializers.ValidationError({
                "email": (
                    "Email is not verified. "
                    "Please verify the OTP first."
                )
            })

        attrs["_verified_user"] = user

        # ====================================================
        # CHECK MOBILE ALREADY USED BY ANOTHER USER
        # ====================================================

        existing_mobile_user = (
            User.objects
            .filter(mobile=mobile)
            .exclude(id=user.id)
            .first()
        )

        if existing_mobile_user:

            raise serializers.ValidationError({
                "mobile": (
                    "This mobile number is already registered. "
                    "Please use another mobile number."
                )
            })

        # ====================================================
        # CHECK IF THIS USER ALREADY HAS STUDENT PROFILE
        # ====================================================

        if Student.objects.filter(user=user).exists():

            raise serializers.ValidationError({
                "email": (
                    "A student is already registered "
                    "with this email."
                )
            })

        # ====================================================
        # REGISTRATION TOKEN
        # ====================================================

        registration_token = attrs.get(
            "registration_token"
        )

        package_id = attrs.get(
            "package_id"
        )

        # ====================================================
        # ORGANIZATION REGISTRATION
        # ====================================================

        if registration_token:

            try:

                registration_link = (
                    RegistrationLink.objects
                    .select_related("organization")
                    .get(
                        public_slug=registration_token
                    )
                )

            except RegistrationLink.DoesNotExist:

                raise serializers.ValidationError({
                    "registration_token":
                        "Invalid registration token."
                })

            if not registration_link.is_valid():

                raise serializers.ValidationError({
                    "registration_token": (
                        "Registration link is expired, "
                        "inactive, revoked, or invalid."
                    )
                })

            attrs["_registration_source"] = "ORGANIZATION"

            attrs["_registration_link"] = (
                registration_link
            )

            attrs["_organization"] = (
                registration_link.organization
            )

            return attrs

        # ====================================================
        # DIRECT REGISTRATION
        # ====================================================

        if not package_id:

            raise serializers.ValidationError({
                "package_id": (
                    "Package ID is required "
                    "for direct registration."
                )
            })

        # ====================================================
        # GET PACKAGE
        # ====================================================

        try:

            package = Package.objects.get(
                id=package_id
            )

        except Package.DoesNotExist:

            raise serializers.ValidationError({
                "package_id": (
                    f"Package with id {package_id} "
                    "does not exist."
                )
            })

        # ====================================================
        # CHECK PACKAGE STATUS
        # ====================================================

        if package.status != "ACTIVE":

            raise serializers.ValidationError({
                "package_id": (
                    f"Package with id {package_id} "
                    "is not active."
                )
            })

        attrs["_registration_source"] = "DIRECT"

        attrs["_package"] = package

        return attrs


    # ========================================================
    # CREATE
    # ========================================================

    def create(self, validated_data):

        # ====================================================
        # INTERNAL DATA
        # ====================================================

        registration_source = validated_data.pop(
            "_registration_source"
        )

        registration_link = validated_data.pop(
            "_registration_link",
            None
        )

        organization = validated_data.pop(
            "_organization",
            None
        )

        package = validated_data.pop(
            "_package",
            None
        )

        user = validated_data.pop(
            "_verified_user"
        )

        # ====================================================
        # REMOVE NON-STUDENT FIELDS
        # ====================================================

        validated_data.pop(
            "registration_token",
            None
        )

        validated_data.pop(
            "package_id",
            None
        )

        password = validated_data.pop(
            "password"
        )
        
        validated_data.pop(
            "confirm_password"
        )

        grade_id = validated_data.pop(
            "grade_id",
            None
        )

        # ====================================================
        # GET GRADE
        # ====================================================

        grade = None

        if grade_id:

            try:

                grade = Grade.objects.get(
                    id=grade_id
                )

            except Grade.DoesNotExist:

                raise serializers.ValidationError({
                    "grade_id": (
                        f"Grade with id {grade_id} "
                        "does not exist."
                    )
                })

        # ====================================================
        # USER DETAILS
        # ====================================================

        email = validated_data["email"]
        mobile = validated_data["mobile"]

        first_name = validated_data["first_name"]
        last_name = validated_data.get("last_name")

        # ====================================================
        # DATABASE TRANSACTION
        # ====================================================

        with transaction.atomic():

            # =================================================
            # UPDATE USER
            # =================================================

            user.email = email
            user.mobile = mobile
            user.first_name = first_name
            user.last_name = last_name

            user.set_password(password)

            # IMPORTANT:
            # Do NOT set is_email_verified=False here.
            # It was already verified through OTP.

            user.is_email_verified = True

            user.save()

            # =================================================
            # CHECK EXISTING STUDENT
            # =================================================

            existing_student = (
                Student.objects
                .filter(user=user)
                .first()
            )

            if existing_student:

                raise serializers.ValidationError({
                    "email": (
                        "A student is already registered "
                        "with this email."
                    )
                })

            # =================================================
            # CREATE STUDENT CODE
            # =================================================

            student_code = (
                self.generate_student_code()
            )

            # =================================================
            # CREATE STUDENT
            # =================================================

            student = Student.objects.create(

                user=user,

                student_code=student_code,

                first_name=first_name,

                last_name=last_name,

                gender=validated_data.get(
                    "gender"
                ),

                date_of_birth=validated_data.get(
                    "date_of_birth"
                ),

                blood_group=validated_data.get(
                    "blood_group"
                ),

                parent_name=validated_data.get(
                    "parent_name"
                ),

                parent_mobile=validated_data.get(
                    "parent_mobile"
                ),

                emergency_contact=validated_data.get(
                    "emergency_contact"
                )
            )

            # =================================================
            # CREATE STUDENT USER ROLE
            # =================================================

            try:

                student_role = Role.objects.get(
                    name="STUDENT"
                )

            except Role.DoesNotExist:

                raise serializers.ValidationError({
                    "role": (
                        "STUDENT role does not exist. "
                        "Please create the STUDENT role first."
                    )
                })

            # =================================================
            # CREATE USER ROLE
            # =================================================

            UserRole.objects.get_or_create(

                user=user,

                role=student_role,

                defaults={
                    "assigned_by": None,
                    "is_active": True
                }
            )

            # =================================================
            # REGISTRATION NUMBER
            # =================================================

            registration_number = (
                self.generate_registration_number()
            )

            # =================================================
            # CREATE STUDENT REGISTRATION
            # =================================================

            registration = (
                StudentRegistration.objects.create(

                    student=student,

                    organization=organization,

                    registration_link=registration_link,

                    registration_number=(
                        registration_number
                    ),

                    grade=grade,

                    class_name=validated_data.get(
                        "class_name"
                    ),

                    section=validated_data.get(
                        "section"
                    ),

                    academic_year=validated_data.get(
                        "academic_year"
                    ),

                    registration_type=(
                        "ORGANIZATION"
                        if registration_source ==
                        "ORGANIZATION"
                        else "DIRECT"
                    ),

                    registration_status=(
                        StudentRegistration
                        .RegistrationStatus
                        .REGISTERED
                    )
                )
            )

            # =================================================
            # ORDER
            # =================================================

            order = None

            # IMPORTANT:
            # Organization registration does NOT create order.

            if registration_source == "DIRECT":

                quantity = 1

                unit_price = package.package_price

                total_amount = (
                    unit_price * quantity
                )

                order = Order.objects.create(

                    student=student,

                    package=package,

                    quantity=quantity,

                    unit_price=unit_price,

                    total_amount=total_amount,

                    status=Order.Status.PENDING
                )

            # =================================================
            # UPDATE REGISTRATION LINK COUNT
            # =================================================

            if registration_link:

                registration_link.registration_count += 1

                registration_link.save(
                    update_fields=[
                        "registration_count",
                        "updated_at"
                    ]
                )
                

            # =================================================
            # GENERATE JWT TOKENS
            # =================================================

            refresh = RefreshToken.for_user(user)

            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # =================================================
            # RETURN
            # =================================================

            return {
                "student": student,

                "registration": registration,

                "order": order,

                "registration_source":
                    registration_source,
                    
                "access_token": access_token,
                "refresh_token": refresh_token
            }

    # ========================================================
    # GENERATE STUDENT CODE
    # ========================================================

    def generate_student_code(self):

        last_student = (
            Student.objects
            .order_by("-id")
            .first()
        )

        next_number = (
            last_student.id + 1
            if last_student
            else 1
        )

        return f"STU-{next_number:06d}"

    # ========================================================
    # GENERATE REGISTRATION NUMBER
    # ========================================================

    def generate_registration_number(self):

        last_registration = (
            StudentRegistration.objects
            .order_by("-id")
            .first()
        )

        next_number = (
            last_registration.id + 1
            if last_registration
            else 1
        )

        return f"REG-{next_number:06d}"           


         