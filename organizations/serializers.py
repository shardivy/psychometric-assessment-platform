import re

import secrets
import hashlib
from django.db import transaction
from rest_framework import serializers
from django.conf import settings

from assessments.models import AssessmentBlueprintItem, AssessmentVersion
from organizations.models import Organization, OrganizationPackage, Package, RegistrationLink


# class AssessmentVersionGradeSerializer(serializers.ModelSerializer):

#     grade_id = serializers.IntegerField(
#         source="grade.id",
#         read_only=True
#     )

#     grade_name = serializers.CharField(
#         source="grade.grade_name",
#         read_only=True
#     )

#     board = serializers.CharField(
#         read_only=True
#     )

#     class Meta:
#         model = AssessmentBlueprintItem

#         fields = [
#             "grade_id",
#             "grade_name",
#             "board",
#         ]

class PackageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Package
        fields = [
            "id",
            "public_id",
            "assessment_version",
            "grade",
            "package_name",
            "package_features1",
            "package_features2",
            "package_features3",
            "package_features4",
            "package_features5",
            "package_price",
            "package_description",
            "status",
            "package_deliverable1",
            "package_deliverable2",
            "package_deliverable3",
            "package_deliverable4",
            "package_deliverable5",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "public_id",
        ]

class PackageListSerializer(serializers.ModelSerializer):

    assessment_version_number = serializers.CharField(
        source="assessment_version.version_number",
        read_only=True
    )

    assessment_version_name = serializers.CharField(
        source="assessment_version.version_name",
        read_only=True
    )
    
    grade_id = serializers.CharField(
        source="grade.id",
        read_only=True
    )
    
    grade_name = serializers.CharField(
        source="grade.grade_name",
        read_only=True
    )

    class Meta:
        model = Package
        fields = [
            "id",
            "public_id",
            "assessment_version",
            "assessment_version_number",
            "assessment_version_name",
            "grade_id",
            "grade_name",
            "package_name",
            "package_features1",
            "package_features2",
            "package_features3",
            "package_features4",
            "package_features5",
            "package_price",
            "package_description",
            "status",
            "package_deliverable1",
            "package_deliverable2",
            "package_deliverable3",
            "package_deliverable4",
            "package_deliverable5",
        ]
        
class PublishedAssessmentVersionSerializer(serializers.ModelSerializer):

    assessment_name = serializers.CharField(
        source="assessment.name",
        read_only=True
    )

    class Meta:
        model = AssessmentVersion
        fields = [
            "id",
            "public_id",
            "assessment",
            "assessment_name",
            "version_number",
            "version_name",
            "release_date",
            "effective_from",
            "effective_to",
            "duration_minutes",
            "total_sections",
            "total_subsections",
            "total_questions",
            "total_marks",
            "allow_resume",
            "allow_review",
            "randomize_sections",
            "show_result_immediately",
            "instructions",
            "status",
            "published_by",
            "published_at",
            "created_at",
            "updated_at",
        ]
        
#================================ Organization Serializers =================================

class OrganizationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization

        fields = [
            "id",
            "public_id",
            "organization_code",
            "organization_type",
            "name",
            "short_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "logo_url",
            "timezone",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "public_id",
            "organization_code",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Organization name cannot be empty."
            )

        return value

    def validate_email(self, value):
        if value:
            return value.strip().lower()

        return value

    def validate_phone(self, value):
        if value:
            value = value.strip()

            if not re.match(r"^[0-9+\-\s()]{7,20}$", value):
                raise serializers.ValidationError(
                    "Enter a valid phone number."
                )

        return value

    def validate_pincode(self, value):
        if value:
            value = value.strip()

            if not re.match(r"^[0-9]{6}$", value):
                raise serializers.ValidationError(
                    "Pincode must contain exactly 6 digits."
                )

        return value
    
class OrganizationListSerializer(serializers.ModelSerializer):

    registration_link = serializers.SerializerMethodField()

    class Meta:
        model = Organization

        fields = [
            "id",
            "public_id",
            "organization_code",
            "organization_type",
            "name",
            "short_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "logo_url",
            "timezone",
            "status",
            "registration_link",
            "created_at",
            "updated_at",
        ]

    def get_registration_link(self, obj):

        # ==========================================
        # ONLY ACTIVE ORGANIZATION
        # ==========================================

        if obj.status != Organization.Status.ACTIVE:
            return None

        # ==========================================
        # GET ACTIVE REGISTRATION LINK
        # ==========================================

        registration_link = (
            obj.registration_links
            .filter(
                status=RegistrationLink.Status.ACTIVE
            )
            .order_by("-id")
            .first()
        )

        if not registration_link:
            return None

        # ==========================================
        # FRONTEND REGISTRATION URL
        # ==========================================

        return (
            f"{settings.FRONTEND_URL}/"
            f"?token={registration_link.public_slug}"
        )   
        
        
class OrganizationPackageInputSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
    negotiated_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0
    )
    currency = serializers.CharField(
        max_length=3,
        required=False,
        default="INR"
    )
    seat_limit = serializers.IntegerField(
        min_value=1
    )
    valid_from = serializers.DateField()
    valid_until = serializers.DateField(
        required=False,
        allow_null=True
    )
    contract_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    def validate_package_id(self, value):
        try:
            package = Package.objects.get(
                id=value
            )
        except Package.DoesNotExist:
            raise serializers.ValidationError(
                f"Package with id {value} does not exist."
            )

        if package.status != Package.Status.ACTIVE:
            raise serializers.ValidationError(
                f"Package with id {value} is not active."
            )

        return value

    def validate(self, attrs):

        if (
            attrs.get("valid_until")
            and attrs["valid_until"] < attrs["valid_from"]
        ):
            raise serializers.ValidationError({
                "valid_until":
                    "valid_until must be greater than or equal to valid_from."
            })

        return attrs


class OrganizationCreateSerializer(serializers.ModelSerializer):

    packages = OrganizationPackageInputSerializer(
        many=True,
        required=False
    )

    is_draft = serializers.BooleanField(
        default=True,
        write_only=True
    )

    organization_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100
    )

    class Meta:
        model = Organization

        fields = [
            "organization_code",
            "organization_type",
            "name",
            "short_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "logo_url",
            "timezone",
            "packages",
            "is_draft",
        ]

    # def generate_organization_code(self, name):

    #     # ==========================================
    #     # CREATE NAME PART
    #     # ==========================================

    #     name_part = re.sub(
    #         r"[^A-Za-z0-9]+",
    #         "-",
    #         name.strip().upper()
    #     ).strip("-")

    #     name_part = name_part[:40]

    #     # ==========================================
    #     # GET LAST ORGANIZATION CODE
    #     # ==========================================

    #     last_organization = (
    #         Organization.objects
    #         .filter(
    #             organization_code__startswith="ORG-"
    #         )
    #         .order_by("-id")
    #         .first()
    #     )

    #     if last_organization:
    #         try:
    #             last_number = int(
    #                 last_organization.organization_code.split("-")[-1]
    #             )
    #         except (ValueError, IndexError):
    #             last_number = 0
    #     else:
    #         last_number = 0

    #     next_number = last_number + 1

    #     # ==========================================
    #     # FINAL ORGANIZATION CODE
    #     # ==========================================

    #     return f"ORG-{name_part}-{next_number:03d}"
    
    def validate(self, attrs):

        packages = attrs.get("packages", [])

        is_draft = attrs.get("is_draft", True)

        # ==========================================
        # DRAFT ORGANIZATION
        # Packages can be empty
        # ==========================================

        if is_draft and not packages:
            return attrs

        # ==========================================
        # ACTIVE ORGANIZATION
        # At least one package is required
        # ==========================================

        if not is_draft and not packages:
            raise serializers.ValidationError({
                "packages": (
                    "At least one package is required "
                    "when is_draft is false."
                )
            })

        # ==========================================
        # CHECK DUPLICATE PACKAGES
        # ==========================================

        package_ids = [
            package["package_id"]
            for package in packages
        ]

        if len(package_ids) != len(set(package_ids)):
            raise serializers.ValidationError({
                "packages":
                    "The same package cannot be assigned more than once."
            })

        return attrs
    
    def create_registration_link(self, organization):

        # ==========================================
        # GENERATE RANDOM TOKEN
        # ==========================================

        public_slug = secrets.token_urlsafe(32)

        # ==========================================
        # CREATE TOKEN HASH
        # ==========================================

        token_hash = hashlib.sha256(
            public_slug.encode()
        ).hexdigest()

        # ==========================================
        # GET REQUEST USER
        # ==========================================

        request = self.context.get("request")

        user = (
            request.user
            if request and request.user.is_authenticated
            else None
        )

        # ==========================================
        # CREATE REGISTRATION LINK
        # ==========================================

        registration_link = RegistrationLink.objects.create(
            organization=organization,
            token_hash=token_hash,
            public_slug=public_slug,
            link_name=f"{organization.name} Registration",
            status=RegistrationLink.Status.ACTIVE,
            registration_count=0,
            created_by=user
        )

        return registration_link


    def create(self, validated_data):

        packages_data = validated_data.pop(
            "packages",
            []
        )

        is_draft = validated_data.pop(
            "is_draft",
            True
        )

        request = self.context.get("request")

        user = (
            request.user
            if request and request.user.is_authenticated
            else None
        )

        organization_status = (
            Organization.Status.DRAFT
            if is_draft
            else Organization.Status.ACTIVE
        )
        registration_link = None

        with transaction.atomic():

            # # ==========================================
            # # AUTO GENERATE ORGANIZATION CODE
            # # ==========================================

            # organization_code = self.generate_organization_code(
            #     validated_data["name"]
            # )

            # ==========================================
            # CREATE ORGANIZATION
            # ==========================================

            organization = Organization.objects.create(
                **validated_data,
                # organization_code=organization_code,
                status=organization_status,
                created_by=user
            )

            # ==========================================
            # CREATE ORGANIZATION PACKAGES
            # ==========================================

            organization_packages = []

            if packages_data:

                package_ids = [
                    item["package_id"]
                    for item in packages_data
                ]

                packages = {
                    package.id: package
                    for package in Package.objects.filter(
                        id__in=package_ids,
                        status=Package.Status.ACTIVE
                    )
                }

                missing_package_ids = (
                    set(package_ids) - set(packages.keys())
                )

                if missing_package_ids:
                    raise serializers.ValidationError({
                        "packages": (
                            "The following package IDs are invalid "
                            "or inactive: "
                            f"{sorted(missing_package_ids)}"
                        )
                    })

                for package_data in packages_data:

                    package = packages[
                        package_data["package_id"]
                    ]

                    organization_packages.append(
                        OrganizationPackage(
                            organization=organization,
                            package=package,
                            contract_code=package_data.get(
                                "contract_code"
                            ),
                            negotiated_price=package_data[
                                "negotiated_price"
                            ],
                            currency=package_data.get(
                                "currency",
                                "INR"
                            ),
                            seat_limit=package_data[
                                "seat_limit"
                            ],
                            used_seats=0,
                            valid_from=package_data[
                                "valid_from"
                            ],
                            valid_until=package_data.get(
                                "valid_until"
                            ),
                            status=(
                                OrganizationPackage.Status.PENDING
                                if is_draft
                                else OrganizationPackage.Status.ACTIVE
                            ),
                            notes=package_data.get(
                                "notes"
                            ),
                            assigned_by=user
                        )
                    )

                OrganizationPackage.objects.bulk_create(
                    organization_packages
                )
                
            # ==========================================
            # CREATE REGISTRATION LINK
            # ONLY WHEN ORGANIZATION IS ACTIVATED
            # ==========================================

            if not is_draft:

                self.registration_link = (
                    self.create_registration_link(
                        organization
                    )
                )

            return organization
        
class OrganizationDraftGetSerializer(serializers.ModelSerializer):

    packages = serializers.SerializerMethodField()

    class Meta:
        model = Organization

        fields = [
            "id",
            "public_id",
            "organization_code",
            "organization_type",
            "name",
            "short_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "logo_url",
            "timezone",
            "status",
            "packages",
        ]

    def get_packages(self, obj):

        organization_packages = (
            OrganizationPackage.objects
            .filter(organization=obj)
            .select_related("package")
        )

        data = []

        for organization_package in organization_packages:

            data.append({
                "id": organization_package.id,
                "public_id": str(
                    organization_package.public_id
                ),
                "package_id": organization_package.package.id,
                "package_name": organization_package.package.package_name,
                "contract_code": organization_package.contract_code,
                "negotiated_price": str(
                    organization_package.negotiated_price
                ),
                "currency": organization_package.currency,
                "seat_limit": organization_package.seat_limit,
                "used_seats": organization_package.used_seats,
                "available_seats": (
                    organization_package.seat_limit
                    - organization_package.used_seats
                ),
                "valid_from": organization_package.valid_from,
                "valid_until": organization_package.valid_until,
                "status": organization_package.status,
                "notes": organization_package.notes,
            })

        return data
    
class OrganizationDraftUpdateSerializer(serializers.ModelSerializer):

    packages = OrganizationPackageInputSerializer(
        many=True,
        required=False
    )

    is_draft = serializers.BooleanField(
        required=False,
        default=True,
        write_only=True
    )

    class Meta:
        model = Organization

        fields = [
            "organization_type",
            "name",
            "short_name",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "state",
            "country",
            "pincode",
            "logo_url",
            "timezone",
            "packages",
            "is_draft",
        ]

    def validate(self, attrs):

        organization = self.instance

        # ==========================================
        # ONLY DRAFT ORGANIZATION CAN USE THIS FLOW
        # ==========================================

        if organization.status != Organization.Status.DRAFT:
            raise serializers.ValidationError({
                "organization": (
                    "Only draft organizations can be updated "
                    "through this API."
                )
            })

        is_draft = attrs.get(
            "is_draft",
            True
        )

        packages = attrs.get(
            "packages",
            []
        )

        # ==========================================
        # IF ACTIVATING ORGANIZATION
        # PACKAGE IS REQUIRED
        # ==========================================

        if not is_draft and not packages:

            raise serializers.ValidationError({
                "packages": (
                    "At least one package is required "
                    "when is_draft is false."
                )
            })

        # ==========================================
        # CHECK DUPLICATE PACKAGES
        # ==========================================

        package_ids = [
            package["package_id"]
            for package in packages
        ]

        if len(package_ids) != len(set(package_ids)):

            raise serializers.ValidationError({
                "packages":
                    "The same package cannot be assigned more than once."
            })

        return attrs
    
    def create_registration_link(self, organization):

        # ==========================================
        # GENERATE RANDOM TOKEN
        # ==========================================

        public_slug = secrets.token_urlsafe(32)

        # ==========================================
        # CREATE TOKEN HASH
        # ==========================================

        token_hash = hashlib.sha256(
            public_slug.encode()
        ).hexdigest()

        # ==========================================
        # GET REQUEST USER
        # ==========================================

        request = self.context.get("request")

        user = (
            request.user
            if request and request.user.is_authenticated
            else None
        )

        # ==========================================
        # CREATE REGISTRATION LINK
        # ==========================================

        registration_link = RegistrationLink.objects.create(
            organization=organization,
            token_hash=token_hash,
            public_slug=public_slug,
            link_name=f"{organization.name} Registration",
            status=RegistrationLink.Status.ACTIVE,
            registration_count=0,
            created_by=user
        )

        return registration_link

    def update(self, instance, validated_data):

        packages_data = validated_data.pop(
            "packages",
            None
        )

        is_draft = validated_data.pop(
            "is_draft",
            True
        )

        # ==========================================
        # REGISTRATION LINK
        # ==========================================

        self.registration_link = None

        with transaction.atomic():

            # ==========================================
            # UPDATE ORGANIZATION DETAILS
            # ==========================================

            for field, value in validated_data.items():

                setattr(
                    instance,
                    field,
                    value
                )

            # ==========================================
            # UPDATE ORGANIZATION STATUS
            # ==========================================

            if is_draft:

                instance.status = (
                    Organization.Status.DRAFT
                )

            else:

                instance.status = (
                    Organization.Status.ACTIVE
                )

            instance.save()

            # ==========================================
            # UPDATE PACKAGES
            # ==========================================

            if packages_data is not None:

                # Remove old packages
                OrganizationPackage.objects.filter(
                    organization=instance
                ).delete()

                organization_packages = []

                for package_data in packages_data:

                    package = Package.objects.get(
                        id=package_data["package_id"]
                    )

                    organization_packages.append(
                        OrganizationPackage(
                            organization=instance,
                            package=package,

                            contract_code=package_data.get(
                                "contract_code"
                            ),

                            negotiated_price=package_data[
                                "negotiated_price"
                            ],

                            currency=package_data.get(
                                "currency",
                                "INR"
                            ),

                            seat_limit=package_data[
                                "seat_limit"
                            ],

                            used_seats=0,

                            valid_from=package_data[
                                "valid_from"
                            ],

                            valid_until=package_data.get(
                                "valid_until"
                            ),

                            # ==================================
                            # PACKAGE STATUS
                            # ==================================

                            status=(
                                OrganizationPackage.Status.PENDING
                                if is_draft
                                else OrganizationPackage.Status.ACTIVE
                            ),

                            notes=package_data.get(
                                "notes"
                            ),
                        )
                    )

                OrganizationPackage.objects.bulk_create(
                    organization_packages
                )

            # ==========================================
            # CREATE REGISTRATION LINK
            # ONLY WHEN ORGANIZATION IS ACTIVATED
            # ==========================================

            if not is_draft:

                self.registration_link = (
                    self.create_registration_link(
                        instance
                    )
                )

            return instance