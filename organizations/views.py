from django.shortcuts import render

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError, transaction

from assessments.models import AssessmentBlueprintItem, AssessmentVersion
from organizations.utils import generate_organization_code
from organizations.models import Organization, Package
from organizations.serializers import OrganizationCreateSerializer, OrganizationDraftGetSerializer, OrganizationDraftUpdateSerializer, OrganizationListSerializer, PackageCreateSerializer, PackageListSerializer, PublishedAssessmentVersionSerializer


#=================================================
# PACKAGE API VIEW
#=================================================
class PackageCreateAPIView(APIView):
    """
    Create a new Package for an Assessment Version.

    POST
    /api/v1/packages/
    """

    @transaction.atomic
    def post(self, request):

        # ==================================================
        # STEP 1: GET ASSESSMENT VERSION
        # ==================================================

        assessment_version_id = request.data.get("assessment_version")

        if not assessment_version_id:
            return Response(
                {
                    "success": False,
                    "message": "assessment_version is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # STEP 2: CHECK ASSESSMENT VERSION
        # ==================================================

        try:
            assessment_version = AssessmentVersion.objects.get(
                id=assessment_version_id
            )

        except AssessmentVersion.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Assessment version not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==================================================
        # STEP 3: SERIALIZE DATA
        # ==================================================

        serializer = PackageCreateSerializer(
            data=request.data
        )

        # ==================================================
        # STEP 4: VALIDATE
        # ==================================================

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # STEP 5: CREATE PACKAGE
        # ==================================================

        package = serializer.save(
            assessment_version=assessment_version
        )

        # ==================================================
        # STEP 6: RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Package created successfully.",
                "data": PackageCreateSerializer(package).data
            },
            status=status.HTTP_201_CREATED
        )
        
class PackageUpdateAPIView(APIView):
    """
    Update an existing Package.

    PUT
    /api/v1/packages/<package_id>/
    """

    @transaction.atomic
    def put(self, request, package_id):

        # ==================================================
        # STEP 1: GET PACKAGE
        # ==================================================

        try:
            package = Package.objects.select_for_update().get(
                id=package_id
            )

        except Package.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Package not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==================================================
        # STEP 2: SERIALIZE DATA
        # ==================================================

        serializer = PackageCreateSerializer(
            package,
            data=request.data,
            partial=False
        )

        # ==================================================
        # STEP 3: VALIDATE
        # ==================================================

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # STEP 4: UPDATE PACKAGE
        # ==================================================

        package = serializer.save()

        # ==================================================
        # STEP 5: RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Package updated successfully.",
                "data": PackageCreateSerializer(package).data
            },
            status=status.HTTP_200_OK
        )
        
class PackageListAPIView(APIView):
    """
    Get all Packages.

    GET
    /api/v1/packages/
    """

    def get(self, request):

        # ==================================================
        # GET ALL PACKAGES
        # ==================================================

        packages = (
            Package.objects
            .select_related("assessment_version")
            .all()
            .order_by("package_name")
        )

        # ==================================================
        # SERIALIZE DATA
        # ==================================================

        serializer = PackageListSerializer(
            packages,
            many=True
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Packages fetched successfully.",
                "count": packages.count(),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
class PublishedAssessmentVersionListAPIView(APIView):
    """
    Fetch all published assessment versions.

    GET
    /api/v1/assessment-versions/published/
    """

    def get(self, request):

        # ==================================================
        # GET PUBLISHED VERSIONS ONLY
        # ==================================================

        versions = (
            AssessmentVersion.objects
            .select_related("assessment", "published_by", "report_template")
            .filter(
                status=AssessmentVersion.Status.PUBLISHED
            )
            .order_by(
                "-effective_from",
                "version_number"
            )
        )

        # ==================================================
        # SERIALIZE
        # ==================================================

        serializer = PublishedAssessmentVersionSerializer(
            versions,
            many=True
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Published assessment versions fetched successfully.",
                "count": versions.count(),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
        
#================================ Organization API VIEW =================================

class OrganizationCreateAPIView(APIView):
    """
    Create Organization.

    POST
    /api/v1/organizations/
    """

    @transaction.atomic
    def post(self, request):

        # ==================================================
        # STEP 1: VALIDATE REQUEST
        # ==================================================

        serializer = OrganizationCreateSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            # ==================================================
            # STEP 2: GENERATE ORGANIZATION CODE
            # ==================================================

            year = timezone.now().year

            last_organization = (
                Organization.objects
                .filter(
                    organization_code__startswith=f"ORG-{year}-"
                )
                .order_by("-id")
                .first()
            )

            if last_organization:
                try:
                    last_number = int(
                        last_organization.organization_code.split("-")[-1]
                    )
                except (ValueError, IndexError):
                    last_number = 0
            else:
                last_number = 0

            organization_code = (
                f"ORG-{year}-{last_number + 1:06d}"
            )

            # ==================================================
            # STEP 3: CREATE ORGANIZATION
            # ==================================================

            organization = serializer.save(
                organization_code=organization_code
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Organization could not be created. "
                        "Please try again."
                    )
                },
                status=status.HTTP_409_CONFLICT
            )

        # ==================================================
        # STEP 4: GENERATE URL DIRECTLY
        # ==================================================

        organization_url = (
            request.build_absolute_uri(
                f"/api/v1/organizations/{organization.public_id}/"
            )
        )

        # ==================================================
        # STEP 5: RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Organization created successfully.",
                "data": {
                    "id": organization.id,
                    "public_id": organization.public_id,
                    "organization_code": organization.organization_code,
                    "organization_type": organization.organization_type,
                    "name": organization.name,
                    "organization_url": organization_url,
                    "status": organization.status,
                }
            },
            status=status.HTTP_201_CREATED
        )
        
class OrganizationUpdateAPIView(APIView):
    """
    Update Organization using ID.

    PUT
    /api/v1/organizations/<organization_id>/
    """

    @transaction.atomic
    def put(self, request, organization_id):

        # ==================================================
        # STEP 1: GET ORGANIZATION BY ID
        # ==================================================

        try:
            organization = (
                Organization.objects
                .select_for_update()
                .get(id=organization_id)
            )

        except Organization.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Organization not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==================================================
        # STEP 2: VALIDATE REQUEST
        # ==================================================

        serializer = OrganizationCreateSerializer(
            organization,
            data=request.data,
            partial=False
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # STEP 3: UPDATE ORGANIZATION
        # ==================================================

        organization = serializer.save()

        # ==================================================
        # STEP 4: GENERATE ORGANIZATION URL
        # ==================================================

        organization_url = request.build_absolute_uri(
            f"/api/v1/organizations/{organization.public_id}/"
        )

        # ==================================================
        # STEP 5: RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Organization updated successfully.",
                "data": {
                    "id": organization.id,
                    "public_id": organization.public_id,
                    "organization_code": organization.organization_code,
                    "organization_type": organization.organization_type,
                    "name": organization.name,
                    "short_name": organization.short_name,
                    "email": organization.email,
                    "phone": organization.phone,
                    "website": organization.website,
                    "address": organization.address,
                    "city": organization.city,
                    "state": organization.state,
                    "country": organization.country,
                    "pincode": organization.pincode,
                    "logo_url": organization.logo_url,
                    "timezone": organization.timezone,
                    "status": organization.status,
                    "organization_url": organization_url,
                    "created_at": organization.created_at,
                    "updated_at": organization.updated_at,
                }
            },
            status=status.HTTP_200_OK
        )

class OrganizationListAPIView(APIView):
    """
    Fetch all Organizations.

    GET
    /api/v1/organizations/
    """

    def get(self, request):

        # ==================================================
        # STEP 1: FETCH ALL ORGANIZATIONS
        # ==================================================

        organizations = (
            Organization.objects
            .all()
            .order_by("name")
        )

        # ==================================================
        # STEP 2: SERIALIZE DATA
        # ==================================================

        serializer = OrganizationListSerializer(
            organizations,
            many=True
        )

        # ==================================================
        # STEP 3: RESPONSE
        # ==================================================

        return Response(
            {
                "success": True,
                "message": "Organizations fetched successfully.",
                "count": organizations.count(),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
class PublicOrganizationCreateAPIView(APIView):

    # permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = OrganizationCreateSerializer(
            data=request.data,
            context={
                "request": request
            }
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            organization = serializer.save()

            registration_link = (
                serializer.registration_link
                if hasattr(serializer, "registration_link")
                else None
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Organization created successfully."
                    ),
                    "data": {
                        "id": organization.id,

                        "public_id": str(
                            organization.public_id
                        ),

                        "organization_code":
                            organization.organization_code,

                        "name":
                            organization.name,

                        "status":
                            organization.status,

                        # "registration_link": (
                        #     request.build_absolute_uri(
                        #         f"/api/v1/stu/students/register/"
                        #         f"{registration_link.public_slug}/"
                        #     )
                        #     if registration_link
                        #     else None
                        # )
                        "registration_link": (
                            f"{settings.FRONTEND_URL}/"
                            f"?token={registration_link.public_slug}"
                            if registration_link
                            else None
                        )
                    }
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to create organization "
                        "because of a database constraint."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "An unexpected error occurred "
                        "while creating the organization."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )      
   
class OrganizationDraftDetailAPIView(APIView):

    def get(self, request, organization_id):

        try:

            organization = (
                Organization.objects
                .prefetch_related(
                    "organization_packages__package"
                )
                .get(
                    id=organization_id
                )
            )

        except Organization.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Organization not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==========================================
        # CHECK DRAFT STATUS
        # ==========================================

        if organization.status != Organization.Status.DRAFT:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Only draft organizations can be fetched."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrganizationDraftGetSerializer(
            organization
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Draft organization details fetched successfully."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
class OrganizationDraftUpdateAPIView(APIView):

    def put(self, request, organization_id):

        try:

            organization = Organization.objects.get(
                id=organization_id
            )

        except Organization.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Organization not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==========================================
        # ONLY DRAFT ORGANIZATION CAN BE UPDATED
        # ==========================================

        if organization.status != Organization.Status.DRAFT:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Only draft organizations can be "
                        "updated through this API."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrganizationDraftUpdateSerializer(
            organization,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            organization = serializer.save()
            
            registration_link = (
                serializer.registration_link
            )

            # ==========================================
            # RESPONSE MESSAGE
            # ==========================================

            if organization.status == Organization.Status.ACTIVE:

                message = (
                    "Organization updated and activated successfully."
                )

            else:

                message = (
                    "Draft organization updated successfully."
                )

            return Response(
                {
                    "success": True,
                    "message": message,
                    "data": {
                        "id": organization.id,

                        "public_id": str(
                            organization.public_id
                        ),

                        "organization_code":
                            organization.organization_code,

                        "name":
                            organization.name,

                        "status":
                            organization.status,

                        "registration_link": (
                            f"{settings.FRONTEND_URL}/"
                            f"?token={registration_link.public_slug}"
                            if registration_link
                            else None
                        )
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "An unexpected error occurred "
                        "while updating the organization."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )