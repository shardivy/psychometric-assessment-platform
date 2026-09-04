from decimal import Decimal
import re

from django.db import IntegrityError, transaction
from django.db.models import Q, Count, Prefetch, Sum
from django.shortcuts import render

from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView, api_settings
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from assessments.models import Assessment, AssessmentBlueprintItem, AssessmentVersion, Grade, Question, QuestionGradeMapping, QuestionOption, Section, SubSection, Tags
from assessments.serializers import AssessmentBlueprintListSerializer, AssessmentBuilderSerializer, AssessmentSerializer, AssessmentVersionBlueprintSerializer, AssessmentVersionListSerializer, AssessmentVersionSerializer, GradeSerializer, QuestionCreateUpdateSerializer, QuestionLibrarySerializer, QuestionListSerializer, QuestionRetrieveSerializer, SectionSerializer, SubSectionSerializer, TagsSerializer
from audit.models import ActivityLog, ActivityType, AuditAction, AuditLog
from assessments.pagination import DefaultPagination
from assessments.utils import generate_assessment_code
from reports.models import ReportTemplate

# ========================== Assessment API =========================

class AssessmentAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    # -------------------------------------------------------
    # GET
    # List Assessment / Single Assessment
    # -------------------------------------------------------
    def get(self, request, id=None):

        # ----------------------------------
        # Single Assessment
        # ----------------------------------
        if id:

            try:
                assessment = (
                    Assessment.objects
                    .select_related("created_by")
                    .get(id=id)
                )

            except Assessment.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Assessment not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = AssessmentSerializer(assessment, context={"request": request})

            return Response(
                {
                    "success": True,
                    "message": "Assessment fetched successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # ----------------------------------
        # Assessment List
        # ----------------------------------

        assessments = (
            Assessment.objects
            .select_related("created_by")
            # .all()
            .filter(status__in=["ACTIVE"])
            .order_by("-created_at")
        )

        search = request.query_params.get("search")
        assessment_type = request.query_params.get("assessment_type")
        status_filter = request.query_params.get("status")

        if search:
            assessments = assessments.filter(
                Q(name__icontains=search) |
                Q(short_name__icontains=search) |
                Q(assessment_code__icontains=search)
            )

        if assessment_type:
            assessments = assessments.filter(
                assessment_type=assessment_type
            )

        if status_filter:
            assessments = assessments.filter(
                status=status_filter
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            assessments,
            request
        )

        serializer = AssessmentSerializer(
            page,
            many=True,
            context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)

    # -------------------------------------------------------
    # POST
    # Create Assessment
    # -------------------------------------------------------
    def post(self, request):

        serializer = AssessmentSerializer(
            data=request.data,
            context={"request": request}
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

            serializer.save(
                # created_by=request.user,
                status="ACTIVE"
            )

            return Response(
                {
                    "success": True,
                    "message": "Assessment created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": "Assessment code already exists."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # -------------------------------------------------------
    # PUT
    # Update Assessment
    # -------------------------------------------------------
    def put(self, request, id):

        try:

            assessment = Assessment.objects.get(id=id)

        except Assessment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Assessment not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssessmentSerializer(
            assessment,
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

        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Assessment updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # -------------------------------------------------------
    # DELETE
    # Archive Assessment
    # -------------------------------------------------------
    def delete(self, request, id):

        try:

            assessment = Assessment.objects.get(id=id)

        except Assessment.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Assessment not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        assessment.status = "ARCHIVED"
        assessment.save()

        return Response(
            {
                "success": True,
                "message": "Assessment archived successfully."
            },
            status=status.HTTP_200_OK
        )


# =========================== Assessment Version API ===================

class AssessmentVersionAPIView(APIView):
    
    # permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    
    # -------------------------------------------------------
    # POST
    # Create Assessment Version
    # -------------------------------------------------------
    def post(self, request):

        serializer = AssessmentVersionSerializer(
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

            assessment = serializer.validated_data.get("assessment")
            report_template = serializer.validated_data.get("report_template")

            # -----------------------------------------
            # Validate Assessment
            # -----------------------------------------

            if not Assessment.objects.filter(
                id=assessment.id
            ).exists():

                return Response(
                    {
                        "success": False,
                        "message": "Assessment not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # -----------------------------------------
            # Validate Report Template
            # -----------------------------------------

            if not ReportTemplate.objects.filter(
                id=report_template.id
            ).exists():

                return Response(
                    {
                        "success": False,
                        "message": "Report Template not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            status_value = serializer.validated_data.get(
                "status",
                AssessmentVersion.Status.DRAFT
            )

            published_at = None
            published_by = None

            # -----------------------------------------
            # Publish Logic
            # -----------------------------------------

            if status_value == AssessmentVersion.Status.PUBLISHED:

                AssessmentVersion.objects.filter(
                    assessment=assessment,
                    status=AssessmentVersion.Status.PUBLISHED
                ).update(
                    status=AssessmentVersion.Status.DEPRECATED
                )

                published_at = timezone.now()

                published_by = request.user
                # published_by = None

            assessment_version = serializer.save(
                status=status_value,
                published_at=published_at,
                # published_by=published_by
            )

            return Response(
                {
                    "success": True,
                    "message": "Assessment Version created successfully.",
                    "data": AssessmentVersionSerializer(
                        assessment_version
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": "Version number already exists for this Assessment."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    # -------------------------------------------------------
    # GET
    # List Assessment Versions / Single Assessment Version
    # -------------------------------------------------------
    def get(self, request, id=None):

        # ----------------------------------
        # Single Assessment Version
        # ----------------------------------

        if id:

            try:

                assessment_version = (
                    AssessmentVersion.objects
                    .select_related(
                        "assessment",
                        "report_template",
                        "published_by",
                    )
                    .get(id=id)
                )

            except AssessmentVersion.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Assessment Version not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = AssessmentVersionSerializer(
                assessment_version
            )

            return Response(
                {
                    "success": True,
                    "message": "Assessment Version fetched successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # ----------------------------------
        # Assessment Version List
        # ----------------------------------

        assessment_versions = (

            AssessmentVersion.objects

            .select_related(
                "assessment",
                "report_template"
            )

            .only(

                "id",

                "public_id",

                "assessment",

                "assessment__name",

                "report_template",

                "report_template__name",

                "version_number",

                "version_name",

                "duration_minutes",

                "total_questions",

                "status",

                "effective_from",

                "effective_to",

                "created_at",

            )

            .order_by("-created_at")

        )

        # ----------------------------------
        # Filters
        # ----------------------------------

        search = request.query_params.get("search")

        assessment = request.query_params.get("assessment")

        report_template = request.query_params.get("report_template")

        status_filter = request.query_params.get("status")

        effective_from = request.query_params.get("effective_from")

        effective_to = request.query_params.get("effective_to")

        if search:

            assessment_versions = assessment_versions.filter(

                Q(version_number__icontains=search) |

                Q(version_name__icontains=search) |

                Q(assessment__name__icontains=search)

            )

        if assessment:

            assessment_versions = assessment_versions.filter(
                assessment_id=assessment
            )

        if report_template:

            assessment_versions = assessment_versions.filter(
                report_template_id=report_template
            )

        if status_filter:

            assessment_versions = assessment_versions.filter(
                status=status_filter
            )

        if effective_from:

            assessment_versions = assessment_versions.filter(
                effective_from__gte=effective_from
            )

        if effective_to:

            assessment_versions = assessment_versions.filter(
                effective_to__lte=effective_to
            )

        # ----------------------------------
        # Pagination
        # ----------------------------------

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            assessment_versions,
            request
        )

        serializer = AssessmentVersionListSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )
        
    # -------------------------------------------------------
    # PUT
    # Update Assessment Version
    # -------------------------------------------------------
    def put(self, request, id):

        try:

            assessment_version = AssessmentVersion.objects.get(id=id)

        except AssessmentVersion.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Assessment Version not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------------------------------------------
        # Published Version Cannot Be Edited
        # ---------------------------------------------------

        if assessment_version.status == AssessmentVersion.Status.PUBLISHED:

            return Response(
                {
                    "success": False,
                    "message": "Published Assessment Version cannot be modified."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AssessmentVersionSerializer(
            assessment_version,
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

            status_value = serializer.validated_data.get(
                "status",
                assessment_version.status
            )

            assessment = serializer.validated_data.get(
                "assessment",
                assessment_version.assessment
            )

            published_at = assessment_version.published_at
            published_by = assessment_version.published_by

            # ---------------------------------------------------
            # Publish Logic
            # ---------------------------------------------------

            if status_value == AssessmentVersion.Status.PUBLISHED:

                AssessmentVersion.objects.filter(
                    assessment=assessment,
                    status=AssessmentVersion.Status.PUBLISHED
                ).exclude(
                    id=assessment_version.id
                ).update(
                    status=AssessmentVersion.Status.DEPRECATED
                )

                published_at = timezone.now()

                # published_by = request.user
                published_by = None

            serializer.save(
                status=status_value,
                published_at=published_at,
                published_by=published_by
            )

            return Response(
                {
                    "success": True,
                    "message": "Assessment Version updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    # -------------------------------------------------------
    # DELETE
    # Archive Assessment Version
    # -------------------------------------------------------
    def delete(self, request, id):

        try:

            assessment_version = AssessmentVersion.objects.get(id=id)

        except AssessmentVersion.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Assessment Version not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Don't archive published version

        if assessment_version.status == AssessmentVersion.Status.PUBLISHED:

            return Response(
                {
                    "success": False,
                    "message": "Published Assessment Version cannot be archived."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        assessment_version.status = AssessmentVersion.Status.ARCHIVED

        assessment_version.save(
            update_fields=["status"]
        )

        return Response(
            {
                "success": True,
                "message": "Assessment Version archived successfully."
            },
            status=status.HTTP_200_OK
        )


# ============================ Grade API ======================
class GradeAPIView(APIView):
    """
    Grade CRUD API

    POST    -> Create Grade
    GET     -> List / Detail
    PUT     -> Update Grade
    DELETE  -> Archive Grade
    """

    # permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    # ---------------------------------------------------------
    # Base Queryset
    # ---------------------------------------------------------

    def get_queryset(self):

        return (
            Grade.objects
            .only(
                "id",
                "public_id",
                "grade_code",
                "grade_name",
                "education_level",
                "display_order",
                "status",
                "created_at",
                "updated_at",
            )
            .order_by("display_order", "grade_name")
        )

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    @transaction.atomic
    def post(self, request):

        serializer = GradeSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Grade created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get(self, request, id=None):

        queryset = self.get_queryset()

        if id:

            try:

                grade = queryset.get(id=id)

            except Grade.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Grade not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = GradeSerializer(grade)

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                }
            )

        search = request.query_params.get("search")

        education_level = request.query_params.get(
            "education_level"
        )

        status_filter = request.query_params.get(
            "status"
        )

        if search:

            queryset = queryset.filter(
                Q(grade_name__icontains=search)
                |
                Q(grade_code__icontains=search)
            )

        if education_level:

            queryset = queryset.filter(
                education_level=education_level
            )

        if status_filter:

            queryset = queryset.filter(
                status=status_filter
            )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = GradeSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "Grade list fetched successfully.",
                "data": serializer.data,
            }
        )

    # ---------------------------------------------------------
    # PUT
    # ---------------------------------------------------------

    @transaction.atomic
    def put(self, request, id):

        try:

            grade = Grade.objects.get(id=id)

        except Grade.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Grade not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GradeSerializer(
            grade,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Grade updated successfully.",
                    "data": serializer.data,
                }
            )

        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # DELETE (Archive)
    # ---------------------------------------------------------

    @transaction.atomic
    def delete(self, request, id):

        try:

            grade = Grade.objects.get(id=id)

        except Grade.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Grade not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        grade.status = Grade.Status.INACTIVE
        grade.save(update_fields=["status"])

        return Response(
            {
                "success": True,
                "message": "Grade archived successfully."
            }
        )  
        
# ======================= Tags API =======================
class TagsAPIView(APIView):

    """
    POST   -> Create Tag
    GET    -> List Tags / Detail Tag
    PUT    -> Update Tag
    """

    pagination_class = DefaultPagination

    # =================================================
    # GET QUERYSET
    # =================================================

    def get_queryset(self):

        return (
            Tags.objects
            .all()
            .order_by("tag_name")
        )

    # =================================================
    # POST
    # =================================================

    def post(self, request):

        serializer = TagsSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        tag = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Tag created successfully.",
                "data": TagsSerializer(tag).data,
            },
            status=status.HTTP_201_CREATED,
        )

    # =================================================
    # GET
    # =================================================

    def get(self, request, id=None):

        queryset = self.get_queryset()

        # -----------------------------------------
        # Detail
        # -----------------------------------------

        if id:

            tag = queryset.filter(
                id=id
            ).first()

            if not tag:

                return Response(
                    {
                        "success": False,
                        "message": "Tag not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = TagsSerializer(tag)

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        # -----------------------------------------
        # Search
        # -----------------------------------------

        search = request.query_params.get(
            "search"
        )

        if search:

            queryset = queryset.filter(
                tag_name__icontains=search
            )

        # -----------------------------------------
        # Pagination
        # -----------------------------------------

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = TagsSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "Tags fetched successfully.",
                "data": serializer.data,
            }
        )

    # =================================================
    # PUT
    # =================================================

    @transaction.atomic
    def put(self, request, id):

        # -----------------------------------------
        # Get Tag
        # -----------------------------------------

        tag = (
            Tags.objects
            .select_for_update()
            .filter(id=id)
            .first()
        )

        if not tag:

            return Response(
                {
                    "success": False,
                    "message": "Tag not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------------
        # Validate
        # -----------------------------------------

        serializer = TagsSerializer(
            tag,
            data=request.data,
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------
        # Update
        # -----------------------------------------

        tag = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Tag updated successfully.",
                "data": TagsSerializer(tag).data,
            },
            status=status.HTTP_200_OK,
        )
    

# ======================== Section API =======================
class SectionAPIView(APIView):

    # permission_classes = [IsAuthenticated]

    pagination_class = DefaultPagination

    # ---------------------------------------------------------
    # Base Queryset
    # ---------------------------------------------------------

    def get_queryset(self):

        return (
            Section.objects
            .only(
                "id",
                "public_id",
                "section_code",
                "name",
                "description",
                "instructions",
                "display_order",
                "is_mandatory",
                "status",
                "created_at",
                "updated_at",
            )
            .order_by(
                "display_order",
                "name"
            )
        )

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    @transaction.atomic
    def post(self, request):

        serializer = SectionSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Section created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # List / Detail
    # ---------------------------------------------------------

    def get(self, request, id=None):

        queryset = self.get_queryset()

        if id:

            try:

                section = queryset.get(id=id)

            except Section.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Section not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = SectionSerializer(section)

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                }
            )

        search = request.query_params.get(
            "search"
        )

        status_filter = request.query_params.get(
            "status"
        )

        if search:

            queryset = queryset.filter(
                Q(name__icontains=search)
                |
                Q(section_code__icontains=search)
            )

        if status_filter:

            queryset = queryset.filter(
                status=status_filter
            )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = SectionSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    @transaction.atomic
    def put(self, request, id):

        try:

            instance = Section.objects.get(id=id)

        except Section.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Section not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SectionSerializer(
            instance,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Section updated successfully.",
                    "data": serializer.data,
                }
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # Archive
    # ---------------------------------------------------------

    @transaction.atomic
    def delete(self, request, id):

        try:

            section = Section.objects.get(id=id)

        except Section.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Section not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        section.status = Section.Status.INACTIVE
        section.save(
            update_fields=["status"]
        )

        return Response(
            {
                "success": True,
                "message": "Section archived successfully.",
            }
        )        


# ================= Sub-Section API ==========================
class SubSectionAPIView(APIView):

    # permission_classes = [IsAuthenticated]

    pagination_class = DefaultPagination

    # ---------------------------------------------------------
    # Base Queryset
    # ---------------------------------------------------------

    def get_queryset(self):

        return (
            SubSection.objects
            .only(
                "id",
                "public_id",
                "subsection_code",
                "name",
                "description",
                "instructions",
                "display_order",
                "time_limit_minutes",
                "question_limit",
                "randomize_questions",
                "status",
                "created_at",
                "updated_at",
            )
            .order_by(
                "display_order",
                "name",
            )
        )

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    @transaction.atomic
    def post(self, request):

        serializer = SubSectionSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Sub section created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # List / Detail
    # ---------------------------------------------------------

    def get(self, request, id=None):

        queryset = self.get_queryset()

        if id:

            try:
                subsection = queryset.get(id=id)

            except SubSection.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Sub section not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = SubSectionSerializer(
                subsection
            )

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                }
            )

        search = request.query_params.get("search")

        status_filter = request.query_params.get("status")

        if search:

            queryset = queryset.filter(
                Q(name__icontains=search)
                |
                Q(subsection_code__icontains=search)
            )

        if status_filter:

            queryset = queryset.filter(
                status=status_filter
            )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = SubSectionSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    @transaction.atomic
    def put(self, request, id):

        try:

            subsection = SubSection.objects.get(
                id=id
            )

        except SubSection.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Sub section not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubSectionSerializer(
            subsection,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Sub section updated successfully.",
                    "data": serializer.data,
                }
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ---------------------------------------------------------
    # Archive
    # ---------------------------------------------------------

    @transaction.atomic
    def delete(self, request, id):

        try:

            subsection = SubSection.objects.get(
                id=id
            )

        except SubSection.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Sub section not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        subsection.status = SubSection.Status.INACTIVE

        subsection.save(
            update_fields=["status"]
        )

        return Response(
            {
                "success": True,
                "message": "Sub section archived successfully.",
            }
        )  

# ========================== Assessment Builder API ==========================

class GenerateAssessmentVersionAPIView(APIView):
    """
    Generate the next version number for an assessment.

    Example:
        V1
        V2
        V3
        V4
    """

    def get(self, request, assessment_id):

        try:
            # -----------------------------------------
            # Get Assessment
            # -----------------------------------------

            assessment = (
                Assessment.objects
                .only(
                    "id",
                    "name",
                    "assessment_code"
                )
                .filter(
                    id=assessment_id
                )
                .first()
            )

            if not assessment:

                return Response(
                    {
                        "success": False,
                        "message": "Assessment not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # -----------------------------------------
            # Get existing version numbers
            # -----------------------------------------

            existing_versions = (
                AssessmentVersion.objects
                .filter(
                    assessment_id=assessment.id
                )
                .values_list(
                    "version_number",
                    flat=True
                )
            )

            max_version = 0

            # -----------------------------------------
            # Find highest V number
            # -----------------------------------------

            for version_number in existing_versions:

                if not version_number:
                    continue

                match = re.fullmatch(
                    r"V(\d+)",
                    version_number.strip().upper()
                )

                if match:

                    version = int(
                        match.group(1)
                    )

                    max_version = max(
                        max_version,
                        version
                    )

            # -----------------------------------------
            # Generate next version
            # -----------------------------------------

            next_version = (
                f"V{max_version + 1}"
            )

            # -----------------------------------------
            # Response
            # -----------------------------------------

            return Response(
                {
                    "success": True,
                    "message": (
                        "Next version number "
                        "generated successfully."
                    ),
                    "data": {
                        "assessment_id":
                            assessment.id,

                        "assessment_name":
                            assessment.name,

                        "assessment_code":
                            assessment.assessment_code,

                        "version_number":
                            next_version
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to generate "
                        "version number."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssessmentBuilderAPIView(APIView):
    """
    Assessment Builder API

    Supports:
    1. Create new assessment
    2. Reuse existing assessment
    3. Create version
    4. Reuse existing draft version
    5. Add blueprint questions
    6. Save partial draft
    7. Publish existing draft
    8. Re-submit same draft without duplicate errors
    """

    @transaction.atomic
    def post(self, request):

        serializer = AssessmentBuilderSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        try:

            # ==================================================
            # GET INPUT
            # ==================================================

            assessment_data = data.get("assessment", {})

            assessment_id = assessment_data.get("id")

            version_id = data.get("version_id")
            version_data = data.get("version")

            blueprint_data = data.get(
                "blueprint_items",
                []
            )

            is_draft = data.get(
                "is_draft",
                True
            )
            
            # ==================================================
            # PUBLISHING VALIDATION
            # ==================================================

            if not is_draft:

                # ----------------------------------------------
                # Blueprint items are required
                # ----------------------------------------------

                if not blueprint_data:

                    raise ValidationError({
                        "blueprint_items": (
                            "Blueprint items are required "
                            "when publishing the assessment."
                        )
                    })

                # ----------------------------------------------
                # Complete hierarchy is required
                # Grade -> Section -> SubSection -> Questions
                # ----------------------------------------------

                for blueprint_item in blueprint_data:

                    # ------------------------------------------
                    # Grade
                    # ------------------------------------------

                    if not blueprint_item.get("grade_id"):

                        raise ValidationError({
                            "grade_id": (
                                "Grade ID is required "
                                "when publishing."
                            )
                        })

                    # ------------------------------------------
                    # Sections
                    # ------------------------------------------

                    if not blueprint_item.get("sections"):

                        raise ValidationError({
                            "sections": (
                                "Sections are required "
                                "when publishing."
                            )
                        })

                    for section_data in blueprint_item["sections"]:

                        # --------------------------------------
                        # SubSections
                        # --------------------------------------

                        if not section_data.get("subsections"):

                            raise ValidationError({
                                "subsections": (
                                    "SubSections are required "
                                    "when publishing."
                                )
                            })

                        for subsection_data in section_data[
                            "subsections"
                        ]:

                            # ----------------------------------
                            # Questions
                            # ----------------------------------

                            if not subsection_data.get(
                                "question_ids"
                            ):

                                raise ValidationError({
                                    "question_ids": (
                                        "Question IDs are required "
                                        "when publishing."
                                    )
                                })

            # ==================================================
            # STEP 1: GET / CREATE ASSESSMENT
            # ==================================================

            assessment = None
            assessment_created = False

            # --------------------------------------------------
            # CASE 1: Existing assessment selected
            # --------------------------------------------------

            if assessment_id:

                assessment = (
                    Assessment.objects
                    .select_for_update()
                    .filter(id=assessment_id)
                    .first()
                )

                if not assessment:
                    raise ValidationError({
                        "assessment": {
                            "id": "Assessment not found."
                        }
                    })

            # --------------------------------------------------
            # CASE 2: New assessment
            # --------------------------------------------------

            else:

                if not assessment_data.get("name"):
                    raise ValidationError({
                        "assessment": {
                            "name": "This field is required."
                        }
                    })

                if not assessment_data.get("assessment_type"):
                    raise ValidationError({
                        "assessment": {
                            "assessment_type":
                                "This field is required."
                        }
                    })

                # ----------------------------------------------
                # Reuse existing draft with same name
                # ----------------------------------------------

                assessment = (
                    Assessment.objects
                    .select_for_update()
                    .filter(
                        name=assessment_data["name"],
                        status=Assessment.Status.DRAFT
                    )
                    .order_by("-id")
                    .first()
                )

                # ----------------------------------------------
                # Create new assessment
                # ----------------------------------------------

                if not assessment:

                    assessment = Assessment.objects.create(

                        assessment_code=
                            generate_assessment_code(),

                        name=
                            assessment_data["name"],

                        short_name=
                            assessment_data.get("short_name"),

                        assessment_type=
                            assessment_data["assessment_type"],

                        description=
                            assessment_data.get("description"),

                        default_language=
                            assessment_data.get(
                                "default_language",
                                "en"
                            ),

                        status=
                            Assessment.Status.DRAFT,

                        created_by=(
                            request.user
                            if request.user.is_authenticated
                            else None
                        ),
                    )

                    assessment_created = True

                # ----------------------------------------------
                # Update existing draft
                # ----------------------------------------------

                else:

                    update_fields = []

                    if "short_name" in assessment_data:
                        assessment.short_name = (
                            assessment_data.get("short_name")
                        )
                        update_fields.append("short_name")

                    if "assessment_type" in assessment_data:
                        assessment.assessment_type = (
                            assessment_data["assessment_type"]
                        )
                        update_fields.append("assessment_type")

                    if "description" in assessment_data:
                        assessment.description = (
                            assessment_data.get("description")
                        )
                        update_fields.append("description")

                    if "default_language" in assessment_data:
                        assessment.default_language = (
                            assessment_data.get(
                                "default_language"
                            )
                        )
                        update_fields.append("default_language")

                    if update_fields:

                        update_fields.append("updated_at")

                        assessment.save(
                            update_fields=update_fields
                        )

            # ==================================================
            # STEP 2: GET / CREATE VERSION
            # ==================================================

            version = None
            version_created = False

            # --------------------------------------------------
            # CASE 1: Existing version_id supplied
            # --------------------------------------------------

            if version_id:

                version = (
                    AssessmentVersion.objects
                    .select_for_update()
                    .filter(
                        id=version_id,
                        assessment=assessment
                    )
                    .first()
                )

                if not version:
                    raise ValidationError({
                        "version_id":
                            "Version not found for this assessment."
                    })

                # Published version cannot be modified
                if (
                    version.status ==
                    AssessmentVersion.Status.PUBLISHED
                    and is_draft
                ):
                    raise ValidationError({
                        "version_id":
                            "Published version cannot be modified."
                    })

            # --------------------------------------------------
            # CASE 2: Version data supplied
            # --------------------------------------------------

            elif version_data:

                version_number = version_data.get(
                    "version_number"
                )

                if not version_number:
                    raise ValidationError({
                        "version_number":
                            "Version number is required."
                    })

                # --------------------------------------------------
                # IMPORTANT:
                # First search existing version.
                # --------------------------------------------------

                version = (
                    AssessmentVersion.objects
                    .select_for_update()
                    .filter(
                        assessment=assessment,
                        version_number=version_number
                    )
                    .first()
                )

                # --------------------------------------------------
                # Existing draft version
                # --------------------------------------------------

                if version:

                    # Published version
                    if (
                        version.status ==
                        AssessmentVersion.Status.PUBLISHED
                    ):

                        if is_draft:
                            raise ValidationError({
                                "version_number":
                                    (
                                        "This version is already "
                                        "published and cannot be "
                                        "modified."
                                    )
                            })

                    else:

                        # --------------------------------------------------
                        # Reuse existing draft version
                        # --------------------------------------------------

                        update_fields = []

                        if "version_name" in version_data:
                            version.version_name = (
                                version_data.get(
                                    "version_name"
                                )
                            )
                            update_fields.append(
                                "version_name"
                            )

                        if "release_date" in version_data:
                            version.release_date = (
                                version_data.get(
                                    "release_date"
                                )
                            )
                            update_fields.append(
                                "release_date"
                            )

                        if "effective_from" in version_data:
                            version.effective_from = (
                                version_data[
                                    "effective_from"
                                ]
                            )
                            update_fields.append(
                                "effective_from"
                            )

                        if "effective_to" in version_data:
                            version.effective_to = (
                                version_data.get(
                                    "effective_to"
                                )
                            )
                            update_fields.append(
                                "effective_to"
                            )

                        if "duration_minutes" in version_data:
                            version.duration_minutes = (
                                version_data.get(
                                    "duration_minutes"
                                )
                            )
                            update_fields.append(
                                "duration_minutes"
                            )

                        if "allow_resume" in version_data:
                            version.allow_resume = (
                                version_data.get(
                                    "allow_resume"
                                )
                            )
                            update_fields.append(
                                "allow_resume"
                            )

                        if "allow_review" in version_data:
                            version.allow_review = (
                                version_data.get(
                                    "allow_review"
                                )
                            )
                            update_fields.append(
                                "allow_review"
                            )

                        if "randomize_sections" in version_data:
                            version.randomize_sections = (
                                version_data.get(
                                    "randomize_sections"
                                )
                            )
                            update_fields.append(
                                "randomize_sections"
                            )

                        if "show_result_immediately" in version_data:
                            version.show_result_immediately = (
                                version_data.get(
                                    "show_result_immediately"
                                )
                            )
                            update_fields.append(
                                "show_result_immediately"
                            )

                        if "instructions" in version_data:
                            version.instructions = (
                                version_data.get(
                                    "instructions"
                                )
                            )
                            update_fields.append(
                                "instructions"
                            )

                        if update_fields:
                            update_fields.append("updated_at")

                            version.save(
                                update_fields=update_fields
                            )

                # --------------------------------------------------
                # Create new version
                # --------------------------------------------------

                else:

                    version = (
                        AssessmentVersion.objects.create(

                            assessment=assessment,

                            report_template_id=
                                version_data[
                                    "report_template_id"
                                ],

                            version_number=
                                version_number,

                            version_name=
                                version_data.get(
                                    "version_name"
                                ),

                            release_date=
                                version_data.get(
                                    "release_date"
                                ),

                            effective_from=
                                version_data[
                                    "effective_from"
                                ],

                            effective_to=
                                version_data.get(
                                    "effective_to"
                                ),

                            duration_minutes=
                                version_data.get(
                                    "duration_minutes"
                                ),

                            allow_resume=
                                version_data.get(
                                    "allow_resume",
                                    False
                                ),

                            allow_review=
                                version_data.get(
                                    "allow_review",
                                    True
                                ),

                            randomize_sections=
                                version_data.get(
                                    "randomize_sections",
                                    False
                                ),

                            show_result_immediately=
                                version_data.get(
                                    "show_result_immediately",
                                    False
                                ),

                            instructions=
                                version_data.get(
                                    "instructions"
                                ),

                            status=
                                AssessmentVersion.Status.DRAFT
                        )
                    )

                    version_created = True

            # --------------------------------------------------
            # CASE 3:
            # Assessment exists but version was not supplied
            # --------------------------------------------------

            elif not version_id and not version_data:

                version = (
                    AssessmentVersion.objects
                    .select_for_update()
                    .filter(
                        assessment=assessment,
                        version_number="V1",
                        status=AssessmentVersion.Status.DRAFT
                    )
                    .first()
                )

                if not version:

                    version = (
                        AssessmentVersion.objects.create(

                            assessment=assessment,

                            version_number="V1",

                            version_name="",

                            effective_from=
                                timezone.now().date(),

                            status=
                                AssessmentVersion.Status.DRAFT
                        )
                    )

                    version_created = True

            # ==================================================
            # STEP 3: BLUEPRINT
            # ==================================================

            blueprint = AssessmentBlueprintItem.objects.none()

            # --------------------------------------------------
            # CASE 1:
            # No blueprint data
            #
            # Allowed for draft.
            # Nothing will be created.
            # --------------------------------------------------

            if not blueprint_data:

                if not version:
                    raise ValidationError({
                        "blueprint_items": (
                            "Assessment version is required."
                        )
                    })

                # --------------------------------------------------
                # Do NOT create empty blueprint automatically.
                #
                # If frontend sends:
                #
                # "blueprint_items": []
                #
                # simply keep blueprint as None.
                # --------------------------------------------------

                blueprint = (
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version
                    )
                    .order_by("id")
                    # .first()
                )
                
                # Create blueprint automatically
                # when assessment + version are created
                if not blueprint:

                    blueprint = AssessmentBlueprintItem.objects.create(
                        assessment_version=version,
                        grade=None,
                        section=None,
                        subsection=None,
                        question=None,
                        board=AssessmentBlueprintItem.Board.ALL,
                        sequence_no=1,
                        marks_override=None,
                        negative_marks_override=None,
                        status=AssessmentBlueprintItem.Status.DRAFT,
                    )


            # --------------------------------------------------
            # CASE 2:
            # Blueprint data supplied
            # --------------------------------------------------

            else:

                if not version:
                    raise ValidationError({
                        "blueprint_items": (
                            "Create or select a version "
                            "before adding blueprint items."
                        )
                    })

                # ==================================================
                # COLLECT IDS
                # ==================================================

                grade_ids = set()
                section_ids = set()
                subsection_ids = set()
                question_ids = set()

                for blueprint_item in blueprint_data:

                    # ----------------------------------------------
                    # Grade
                    # ----------------------------------------------

                    grade_id = blueprint_item.get("grade_id")

                    if grade_id:
                        grade_ids.add(grade_id)

                    # ----------------------------------------------
                    # Sections
                    # ----------------------------------------------

                    for section_data in blueprint_item.get(
                        "sections",
                        []
                    ):

                        section_id = section_data.get(
                            "section_id"
                        )

                        if section_id:
                            section_ids.add(section_id)

                        # ------------------------------------------
                        # SubSections
                        # ------------------------------------------

                        for subsection_data in section_data.get(
                            "subsections",
                            []
                        ):

                            subsection_id = subsection_data.get(
                                "subsection_id"
                            )

                            if subsection_id:
                                subsection_ids.add(
                                    subsection_id
                                )

                            # --------------------------------------
                            # Questions
                            # --------------------------------------

                            question_ids.update(
                                subsection_data.get(
                                    "question_ids",
                                    []
                                )
                            )

                # ==================================================
                # BULK FETCH MASTER DATA
                # ==================================================

                grades = {
                    obj.id: obj
                    for obj in Grade.objects.filter(
                        id__in=grade_ids
                    )
                }

                sections = {
                    obj.id: obj
                    for obj in Section.objects.filter(
                        id__in=section_ids
                    )
                }

                subsections = {
                    obj.id: obj
                    for obj in SubSection.objects.filter(
                        id__in=subsection_ids
                    )
                }

                questions = {
                    obj.id: obj
                    for obj in Question.objects.filter(
                        id__in=question_ids
                    )
                }
                
                question_grade_mappings = set(
                    QuestionGradeMapping.objects.filter(
                        question_id__in=question_ids,
                        grade_id__in=grade_ids,
                    ).values_list(
                        "question_id",
                        "grade_id",
                    )
                )

                # ==================================================
                # VALIDATE GRADE / SECTION / SUBSECTION / QUESTION
                # ==================================================

                for blueprint_item in blueprint_data:

                    # ----------------------------------------------
                    # GRADE
                    # ----------------------------------------------

                    grade_id = blueprint_item.get("grade_id")

                    if not grade_id:
                        raise ValidationError({
                            "grade_id": (
                                "Grade ID is required."
                            )
                        })

                    grade = grades.get(grade_id)

                    if not grade:
                        raise ValidationError({
                            "grade_id": (
                                f"Grade {grade_id} not found."
                            )
                        })

                    # ----------------------------------------------
                    # SECTIONS
                    # ----------------------------------------------

                    for section_data in blueprint_item.get(
                        "sections",
                        []
                    ):

                        section_id = section_data.get(
                            "section_id"
                        )

                        if not section_id:
                            raise ValidationError({
                                "section_id": (
                                    "Section ID is required."
                                )
                            })

                        section = sections.get(section_id)

                        if not section:
                            raise ValidationError({
                                "section_id": (
                                    f"Section {section_id} not found."
                                )
                            })

                        # ==================================================
                        # IMPORTANT:
                        # VALIDATE SECTION -> SUBSECTION RELATIONSHIP
                        # ==================================================

                        for subsection_data in section_data.get(
                            "subsections",
                            []
                        ):

                            subsection_id = (
                                subsection_data.get(
                                    "subsection_id"
                                )
                            )

                            if not subsection_id:
                                raise ValidationError({
                                    "subsection_id": (
                                        "SubSection ID is required."
                                    )
                                })

                            subsection = subsections.get(
                                subsection_id
                            )

                            if not subsection:
                                raise ValidationError({
                                    "subsection_id": (
                                        f"SubSection "
                                        f"{subsection_id} not found."
                                    )
                                })

                            # ==================================================
                            # QUESTION VALIDATION
                            # ==================================================

                            for question_id in subsection_data.get(
                                "question_ids",
                                []
                            ):

                                question = questions.get(question_id)

                                if not question:

                                    raise ValidationError({
                                        "question_id": (
                                            f"Question {question_id} not found."
                                        )
                                    })

                                # ==================================================
                                # QUESTION -> GRADE MAPPING
                                # ==================================================

                                if (
                                    question_id,
                                    grade_id
                                ) not in question_grade_mappings:

                                    raise ValidationError({
                                        "question_id": (
                                            f"Question {question_id} is not "
                                            f"mapped to Grade {grade_id}."
                                        )
                                    })

                # ==================================================
                # DUPLICATE QUESTION-GRADE INSIDE REQUEST
                # ==================================================

                request_question_grade_mappings = set()

                for blueprint_item in blueprint_data:

                    grade_id = blueprint_item.get("grade_id")

                    for section_data in blueprint_item.get(
                        "sections",
                        []
                    ):

                        for subsection_data in section_data.get(
                            "subsections",
                            []
                        ):

                            for question_id in subsection_data.get(
                                "question_ids",
                                []
                            ):

                                key = (
                                    question_id,
                                    grade_id,
                                )

                                if key in request_question_grade_mappings:

                                    raise ValidationError({
                                        "question_ids": (
                                            f"Question {question_id} is "
                                            f"already assigned to Grade "
                                            f"{grade_id} in this request."
                                        )
                                    })

                                request_question_grade_mappings.add(
                                    key
                                )

                # ==================================================
                # EXISTING BLUEPRINT QUESTION-GRADE MAPPINGS
                # ==================================================

                existing_question_grade_mappings = set(
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version,
                        question__isnull=False,
                        grade__isnull=False,
                    )
                    .values_list(
                        "question_id",
                        "grade_id",
                    )
                )

                # ==================================================
                # CREATE BLUEPRINT RECORDS
                #
                # Supports:
                #
                # 1. Grade only
                # 2. Grade + Section
                # 3. Grade + Section + SubSection
                # 4. Grade + Section + SubSection + Question
                # ==================================================

                blueprint_objects = []

                for blueprint_item in blueprint_data:

                    # ----------------------------------------------
                    # GRADE
                    # ----------------------------------------------

                    grade = grades[
                        blueprint_item["grade_id"]
                    ]

                    sequence_no = blueprint_item.get(
                        "sequence_start",
                        1
                    )

                    # ----------------------------------------------
                    # GET SECTIONS
                    # ----------------------------------------------

                    sections_data = blueprint_item.get(
                        "sections",
                        []
                    )

                    # ==================================================
                    # CASE 1:
                    # ONLY GRADE
                    #
                    # Example:
                    #
                    # {
                    #     "grade_id": 25,
                    #     "board": "ALL",
                    #     "sections": []
                    # }
                    #
                    # {
                    #     "grade_id": 29,
                    #     "board": "ALL",
                    #     "sections": []
                    # }
                    #
                    # Each grade must create its own blueprint record.
                    # ==================================================

                    if not sections_data:

                        grade_exists = (
                            AssessmentBlueprintItem.objects
                            .filter(
                                assessment_version=version,
                                grade_id=grade.id,
                                section__isnull=True,
                                subsection__isnull=True,
                                question__isnull=True,
                            )
                            .exists()
                        )

                        if not grade_exists:

                            blueprint_objects.append(
                                AssessmentBlueprintItem(
                                    assessment_version=version,
                                    grade=grade,
                                    section=None,
                                    subsection=None,
                                    question=None,

                                    board=blueprint_item.get(
                                        "board",
                                        AssessmentBlueprintItem.Board.ALL
                                    ),

                                    sequence_no=sequence_no,

                                    marks_override=blueprint_item.get(
                                        "marks_override"
                                    ),

                                    negative_marks_override=blueprint_item.get(
                                        "negative_marks_override"
                                    ),

                                    status=(
                                        AssessmentBlueprintItem.Status.DRAFT
                                    ),
                                )
                            )

                        sequence_no += 1

                        continue
                    
                    # ==================================================
                    # SECTIONS
                    # ==================================================

                    for section_data in sections_data:

                        section = sections[
                            section_data["section_id"]
                        ]

                        subsections_data = section_data.get(
                            "subsections",
                            []
                        )

                        # ==================================================
                        # CASE 2:
                        # GRADE + SECTION
                        #
                        # Example:
                        #
                        # {
                        #     "grade_id": 8,
                        #     "sections": [
                        #         {
                        #             "section_id": 1
                        #         }
                        #     ]
                        # }
                        # ==================================================

                        if not subsections_data:

                            section_exists = (
                                AssessmentBlueprintItem.objects
                                .filter(
                                    assessment_version=version,
                                    grade=grade,
                                    section=section,
                                    subsection__isnull=True,
                                    question__isnull=True,
                                )
                                .exists()
                            )

                            if not section_exists:

                                blueprint_objects.append(
                                    AssessmentBlueprintItem(

                                        assessment_version=version,

                                        grade=grade,

                                        section=section,

                                        subsection=None,

                                        question=None,

                                        board=blueprint_item.get(
                                            "board",
                                            AssessmentBlueprintItem.Board.ALL
                                        ),

                                        sequence_no=sequence_no,

                                        marks_override=(
                                            blueprint_item.get(
                                                "marks_override"
                                            )
                                        ),

                                        negative_marks_override=(
                                            blueprint_item.get(
                                                "negative_marks_override"
                                            )
                                        ),

                                        status=(
                                            AssessmentBlueprintItem
                                            .Status.DRAFT
                                        ),
                                    )
                                )

                            continue

                        # ==================================================
                        # SUBSECTIONS
                        # ==================================================

                        for subsection_data in subsections_data:

                            subsection = subsections[
                                subsection_data[
                                    "subsection_id"
                                ]
                            ]

                            question_list = (
                                subsection_data.get(
                                    "question_ids",
                                    []
                                )
                            )

                            # ==================================================
                            # CASE 3:
                            # GRADE + SECTION + SUBSECTION
                            #
                            # Example:
                            #
                            # {
                            #     "grade_id": 8,
                            #     "sections": [
                            #         {
                            #             "section_id": 1,
                            #             "subsections": [
                            #                 {
                            #                     "subsection_id": 3
                            #                 }
                            #             ]
                            #         }
                            #     ]
                            # }
                            # ==================================================

                            if not question_list:

                                subsection_exists = (
                                    AssessmentBlueprintItem.objects
                                    .filter(
                                        assessment_version=version,
                                        grade=grade,
                                        section=section,
                                        subsection=subsection,
                                        question__isnull=True,
                                    )
                                    .exists()
                                )

                                if not subsection_exists:

                                    blueprint_objects.append(
                                        AssessmentBlueprintItem(

                                            assessment_version=version,

                                            grade=grade,

                                            section=section,

                                            subsection=subsection,

                                            question=None,

                                            board=blueprint_item.get(
                                                "board",
                                                AssessmentBlueprintItem.Board.ALL
                                            ),

                                            sequence_no=sequence_no,

                                            marks_override=(
                                                blueprint_item.get(
                                                    "marks_override"
                                                )
                                            ),

                                            negative_marks_override=(
                                                blueprint_item.get(
                                                    "negative_marks_override"
                                                )
                                            ),

                                            status=(
                                                AssessmentBlueprintItem
                                                .Status.DRAFT
                                            ),
                                        )
                                    )

                                continue

                            # ==================================================
                            # CASE 4:
                            # COMPLETE
                            #
                            # GRADE + SECTION + SUBSECTION + QUESTIONS
                            # ==================================================

                            for question_id in question_list:

                                # ==================================================
                                # QUESTION -> GRADE MAPPING
                                # ==================================================

                                question_grade_key = (
                                    question_id,
                                    grade.id,
                                )

                                # ==================================================
                                # DON'T CREATE DUPLICATE QUESTION FOR SAME GRADE
                                # ==================================================

                                if question_grade_key in existing_question_grade_mappings:
                                    continue

                                # ==================================================
                                # CREATE BLUEPRINT QUESTION
                                # ==================================================

                                blueprint_objects.append(
                                    AssessmentBlueprintItem(

                                        assessment_version=version,

                                        grade=grade,

                                        section=section,

                                        subsection=subsection,

                                        question=questions[question_id],

                                        board=blueprint_item.get(
                                            "board",
                                            AssessmentBlueprintItem.Board.ALL
                                        ),

                                        sequence_no=sequence_no,

                                        marks_override=(
                                            blueprint_item.get(
                                                "marks_override"
                                            )
                                        ),

                                        negative_marks_override=(
                                            blueprint_item.get(
                                                "negative_marks_override"
                                            )
                                        ),

                                        status=(
                                            AssessmentBlueprintItem
                                            .Status.ACTIVE
                                        ),
                                    )
                                )

                                # Add immediately so the same question-grade
                                # cannot be added twice in the same request.
                                existing_question_grade_mappings.add(
                                    question_grade_key
                                )

                                sequence_no += 1

                # ==================================================
                # BULK INSERT
                # ==================================================

                if blueprint_objects:

                    AssessmentBlueprintItem.objects.bulk_create(
                        blueprint_objects,
                        batch_size=500
                    )

                # ==================================================
                # GET FIRST BLUEPRINT FOR RESPONSE
                # ==================================================

                blueprint = (
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version
                    )
                    .order_by("id")
                    # .first()
                )
                
            # ==================================================
            # GET BLUEPRINT FOR RESPONSE
            # ==================================================

            blueprint = (
                AssessmentBlueprintItem.objects
                .filter(
                    assessment_version=version
                )
                .order_by("id")
            )

            # ==================================================
            # STEP 4: UPDATE VERSION COUNTS
            # ==================================================

            if version:

                # --------------------------------------------------
                # ALL BLUEPRINT ITEMS
                # --------------------------------------------------

                blueprint_qs = (
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version
                    )
                )

                # --------------------------------------------------
                # TOTAL SECTIONS
                #
                # Count sections even when questions are not present.
                # --------------------------------------------------

                version.total_sections = (
                    blueprint_qs
                    .filter(
                        section__isnull=False
                    )
                    .values(
                        "section_id"
                    )
                    .distinct()
                    .count()
                )

                # --------------------------------------------------
                # TOTAL SUBSECTIONS
                #
                # Count subsections even when questions are not present.
                # --------------------------------------------------

                version.total_subsections = (
                    blueprint_qs
                    .filter(
                        subsection__isnull=False
                    )
                    .values(
                        "subsection_id"
                    )
                    .distinct()
                    .count()
                )

                # --------------------------------------------------
                # TOTAL QUESTIONS
                # --------------------------------------------------

                version.total_questions = (
                    blueprint_qs
                    .filter(
                        question__isnull=False
                    )
                    .count()
                )

                # --------------------------------------------------
                # TOTAL MARKS
                #
                # Only question-level records should contribute marks.
                # --------------------------------------------------

                version.total_marks = (
                    blueprint_qs
                    .filter(
                        question__isnull=False
                    )
                    .aggregate(
                        total=Sum(
                            "marks_override"
                        )
                    )["total"]
                    or Decimal("0")
                )

                version.save(
                    update_fields=[
                        "total_sections",
                        "total_subsections",
                        "total_questions",
                        "total_marks",
                        "updated_at",
                    ]
                )

            # ==================================================
            # STEP 5: PUBLISH
            # ==================================================

            if not is_draft:

                if not version:
                    raise ValidationError({
                        "version_id":
                            (
                                "Version is required "
                                "for publishing."
                            )
                    })

                blueprint_exists = (
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version,
                        question__isnull=False
                    )
                    .exists()
                )

                if not blueprint_exists:
                    raise ValidationError({
                        "blueprint_items":
                            (
                                "Cannot publish assessment "
                                "without blueprint items."
                            )
                    })

                version.status = (
                    AssessmentVersion.Status.PUBLISHED
                )

                version.published_by = (
                    request.user
                    if request.user.is_authenticated
                    else None
                )

                version.published_at = timezone.now()

                version.save(
                    update_fields=[
                        "status",
                        "published_by",
                        "published_at",
                        "updated_at",
                    ]
                )

                assessment.status = (
                    Assessment.Status.ACTIVE
                )

                assessment.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            # ==================================================
            # RESPONSE
            # ==================================================

            return Response(
                {
                    "success": True,

                    "message": (
                        "Assessment draft saved successfully."
                        if is_draft
                        else
                        "Assessment published successfully."
                    ),

                    "data": {

                        "assessment": {
                            "id": assessment.id,

                            "public_id":
                                str(
                                    assessment.public_id
                                ),

                            "assessment_code":
                                assessment.assessment_code,

                            "name":
                                assessment.name,

                            "status":
                                assessment.status,
                        },

                        "assessment_version": (
                            {
                                "id": version.id,

                                "public_id":
                                    str(
                                        version.public_id
                                    ),

                                "version_number":
                                    version.version_number,

                                "status":
                                    version.status,

                                "total_sections":
                                    version.total_sections,

                                "total_subsections":
                                    version.total_subsections,

                                "total_questions":
                                    version.total_questions,

                                "total_marks":
                                    version.total_marks,
                            }
                            if version
                            else None
                        ),

                        "blueprint": [
                            {
                                "id": item.id,
                                "public_id": str(item.public_id),
                                "assessment_version_id": item.assessment_version_id,
                                "status": item.status,
                                "section_id": item.section_id,
                                "subsection_id": item.subsection_id,
                                "grade_id": item.grade_id,
                                "question_id": item.question_id,
                                "board": item.board,
                                "sequence_no": item.sequence_no,
                            }
                            for item in blueprint
                        ]
                    }
                },

                status=(
                    status.HTTP_200_OK
                    if assessment_id or version_id
                    else status.HTTP_201_CREATED
                )
            )

        except ValidationError:
            raise

        except IntegrityError as exc:

            return Response(
                {
                    "success": False,

                    "message":
                        (
                            "Assessment could not be saved "
                            "because of a database constraint."
                        ),

                    "error": str(exc),
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,

                    "message":
                        (
                            "Something went wrong while "
                            "saving the assessment."
                        ),

                    "error": str(exc),
                },

                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssessmentBlueprintDraftDetailAPIView(APIView):
    """
    GET:
    Fetch complete assessment draft using AssessmentBlueprintItem ID.

    URL:
        GET /api/assessment-builder/draft/<blueprint_id>/
    """

    def get(self, request, blueprint_id):

        try:
            # ==================================================
            # STEP 1: FETCH ONE BLUEPRINT ITEM
            # ==================================================

            blueprint_item = (
                AssessmentBlueprintItem.objects
                .select_related(
                    "assessment_version",
                    "assessment_version__assessment",
                    "section",
                    "subsection",
                    "grade",
                    "question",
                )
                .filter(
                    id=blueprint_id
                )
                .first()
            )

            if not blueprint_item:
                return Response(
                    {
                        "success": False,
                        "message": "Blueprint item not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # ==================================================
            # STEP 2: GET VERSION
            # ==================================================

            version = blueprint_item.assessment_version
            assessment = version.assessment

            # ==================================================
            # STEP 3: FETCH ALL BLUEPRINT ITEMS
            # FOR SAME ASSESSMENT VERSION
            # ==================================================

            blueprint_items = (
                AssessmentBlueprintItem.objects
                .select_related(
                    "section",
                    "subsection",
                    "grade",
                    "question",
                )
                .filter(
                    assessment_version=version
                )
                .order_by(
                    "section_id",
                    "subsection_id",
                    "sequence_no",
                    "id",
                )
            )

            # ==================================================
            # STEP 3A: PAGINATION
            # ==================================================

            paginator = DefaultPagination()

            page = paginator.paginate_queryset(
                blueprint_items,
                request
            )

            # ==================================================
            # STEP 4: BUILD BLUEPRINT RESPONSE
            # ==================================================

            blueprint_data = []

            for item in page:

                blueprint_data.append(
                    {
                        "blueprint_id": item.id,
                        "blueprint_public_id": (
                            str(item.public_id)
                            if item.public_id
                            else None
                        ),

                        "grade": {
                            "id": (
                                item.grade.id
                                if item.grade
                                else None
                            ),
                            "grade_code": (
                                item.grade.grade_code
                                if item.grade
                                else None
                            ),
                            "grade_name": (
                                item.grade.grade_name
                                if item.grade
                                else None
                            ),
                        },

                        "section": {
                            "id": (
                                item.section.id
                                if item.section
                                else None
                            ),
                            "section_code": (
                                item.section.section_code
                                if item.section
                                else None
                            ),
                            "name": (
                                item.section.name
                                if item.section
                                else None
                            ),
                        },

                        "subsection": {
                            "id": (
                                item.subsection.id
                                if item.subsection
                                else None
                            ),
                            "name": (
                                item.subsection.name
                                if item.subsection
                                else None
                            ),
                        },

                        "board": item.board,

                        "question": {
                            "id": (
                                item.question.id
                                if item.question
                                else None
                            ),
                            "question_code": (
                                item.question.question_code
                                if item.question
                                else None
                            ),
                        },

                        "sequence_no": item.sequence_no,

                        "marks_override": (
                            item.marks_override
                        ),

                        "negative_marks_override": (
                            item.negative_marks_override
                        ),

                        "status": item.status,
                    }
                )

            # ==================================================
            # STEP 5: RESPONSE
            # ==================================================

            return paginator.get_paginated_response(
                {
                    "success": True,
                    "message": (
                        "Assessment draft fetched successfully."
                    ),

                    "data": {

                        # --------------------------------------
                        # Assessment
                        # --------------------------------------

                        "assessment": {
                            "id": assessment.id,
                            "public_id": str(
                                assessment.public_id
                            ),
                            "assessment_code": (
                                assessment.assessment_code
                            ),
                            "name": assessment.name,
                            "short_name": assessment.short_name,
                            "assessment_type": (
                                assessment.assessment_type
                            ),
                            "description": (
                                assessment.description
                            ),
                            "default_language": (
                                assessment.default_language
                            ),
                            "status": assessment.status,
                        },

                        # --------------------------------------
                        # Version
                        # --------------------------------------

                        "assessment_version": {
                            "id": version.id,
                            "public_id": str(
                                version.public_id
                            ),
                            "version_number": (
                                version.version_number
                            ),
                            "version_name": (
                                version.version_name
                            ),
                            "report_template_id": (
                                version.report_template_id
                            ),
                            "release_date": (
                                version.release_date
                            ),
                            "effective_from": (
                                version.effective_from
                            ),
                            "effective_to": (
                                version.effective_to
                            ),
                            "duration_minutes": (
                                version.duration_minutes
                            ),
                            "allow_resume": (
                                version.allow_resume
                            ),
                            "allow_review": (
                                version.allow_review
                            ),
                            "randomize_sections": (
                                version.randomize_sections
                            ),
                            "show_result_immediately": (
                                version.show_result_immediately
                            ),
                            "instructions": (
                                version.instructions
                            ),
                            "status": version.status,

                            "total_sections": (
                                version.total_sections
                            ),
                            "total_subsections": (
                                version.total_subsections
                            ),
                            "total_questions": (
                                version.total_questions
                            ),
                            "total_marks": (
                                version.total_marks
                            ),
                        },

                        # --------------------------------------
                        # Blueprint Items
                        # --------------------------------------

                        "blueprint_items": blueprint_data,
                    }
                }
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Something went wrong while "
                        "fetching assessment draft."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
# class AssessmentBlueprintItemUpdateAPIView(APIView):

#     """
#     Update complete Assessment Blueprint for a Version.

#     PUT /api/assessment-builder/blueprint/<version_id>/
#     """

#     @transaction.atomic
#     def put(self, request, blueprint_id):

#         try:

#             # ==================================================
#             # STEP 1: GET BLUEPRINT + VERSION
#             # ==================================================

#             blueprint = (
#                 AssessmentBlueprintItem.objects
#                 .filter(id=blueprint_id)
#                 .values("id", "assessment_version_id")
#                 .first()
#             )

#             if not blueprint:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": "Assessment blueprint item not found."
#                     },
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             # --------------------------------------------------
#             # Lock the AssessmentVersion separately
#             # --------------------------------------------------

#             version = (
#                 AssessmentVersion.objects
#                 .select_for_update()
#                 .filter(
#                     id=blueprint["assessment_version_id"]
#                 )
#                 .first()
#             )

#             if not version:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": "Assessment version not found."
#                     },
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             # ==================================================
#             # STEP 2: CHECK VERSION STATUS
#             # ==================================================

#             if (
#                 version.status
#                 == AssessmentVersion.Status.PUBLISHED
#             ):

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             "Published assessment version "
#                             "cannot be modified."
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 3: GET INPUT
#             # ==================================================

#             grades_data = request.data.get(
#                 "blueprint_items",
#                 []
#             )
#             is_draft = request.data.get(
#                 "is_draft",
#                 True
#             )

#             if not grades_data:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": "blueprint_items is required."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
                
            
#             # ==================================================
#             # STEP 3A: PUBLISHING VALIDATION
#             # ==================================================

#             if not is_draft:

#                 # ----------------------------------------------
#                 # Validate complete blueprint hierarchy
#                 # ----------------------------------------------

#                 for grade_data in grades_data:

#                     # ------------------------------------------
#                     # Sections are required for publishing
#                     # ------------------------------------------

#                     if not grade_data.get("sections"):

#                         return Response(
#                             {
#                                 "success": False,
#                                 "message": (
#                                     "Sections are required "
#                                     "when publishing."
#                                 )
#                             },
#                             status=status.HTTP_400_BAD_REQUEST
#                         )

#                     # ------------------------------------------
#                     # Validate Sections
#                     # ------------------------------------------

#                     for section_data in grade_data["sections"]:

#                         # --------------------------------------
#                         # SubSections are required
#                         # --------------------------------------

#                         if not section_data.get("subsections"):

#                             return Response(
#                                 {
#                                     "success": False,
#                                     "message": (
#                                         "SubSections are required "
#                                         "when publishing."
#                                     )
#                                 },
#                                 status=status.HTTP_400_BAD_REQUEST
#                             )

#                         # --------------------------------------
#                         # Validate SubSections
#                         # --------------------------------------

#                         for subsection_data in section_data[
#                             "subsections"
#                         ]:

#                             # ----------------------------------
#                             # Questions are required
#                             # ----------------------------------

#                             if not subsection_data.get(
#                                 "question_ids"
#                             ):

#                                 return Response(
#                                     {
#                                         "success": False,
#                                         "message": (
#                                             "Question IDs are required "
#                                             "when publishing."
#                                         )
#                                     },
#                                     status=status.HTTP_400_BAD_REQUEST
#                                 )

#             # ==================================================
#             # STEP 4: COLLECT IDS
#             # ==================================================

#             grade_ids = set()
#             section_ids = set()
#             subsection_ids = set()
#             question_ids = set()

#             for grade_data in grades_data:

#                 # ----------------------------------------------
#                 # Grade
#                 # ----------------------------------------------

#                 grade_id = grade_data.get("grade_id")

#                 if grade_id:
#                     grade_ids.add(grade_id)

#                 # ----------------------------------------------
#                 # Sections
#                 # ----------------------------------------------

#                 for section_data in grade_data.get(
#                     "sections", []
#                 ):

#                     section_id = section_data.get(
#                         "section_id"
#                     )

#                     if section_id:
#                         section_ids.add(section_id)

#                     # ------------------------------------------
#                     # SubSections
#                     # ------------------------------------------

#                     for subsection_data in section_data.get(
#                         "subsections", []
#                     ):

#                         subsection_id = subsection_data.get(
#                             "subsection_id"
#                         )

#                         if subsection_id:
#                             subsection_ids.add(
#                                 subsection_id
#                             )

#                         # --------------------------------------
#                         # Questions
#                         # --------------------------------------

#                         question_ids.update(
#                             subsection_data.get(
#                                 "question_ids",
#                                 []
#                             )
#                         )

#             # ==================================================
#             # STEP 5: FETCH MASTER DATA
#             # ==================================================

#             grades = {
#                 obj.id: obj
#                 for obj in Grade.objects.filter(
#                     id__in=grade_ids
#                 )
#             }

#             sections = {
#                 obj.id: obj
#                 for obj in Section.objects.filter(
#                     id__in=section_ids
#                 )
#             }

#             subsections = {
#                 obj.id: obj
#                 for obj in SubSection.objects.filter(
#                     id__in=subsection_ids
#                 )
#             }

#             questions = {
#                 obj.id: obj
#                 for obj in Question.objects.filter(
#                     id__in=question_ids
#                 )
#             }

#             # ==================================================
#             # STEP 6: VALIDATE GRADES
#             # ==================================================

#             missing_grades = (
#                 grade_ids - set(grades.keys())
#             )

#             if missing_grades:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             f"Invalid Grade IDs: "
#                             f"{sorted(missing_grades)}"
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 7: VALIDATE SECTIONS
#             # ==================================================

#             missing_sections = (
#                 section_ids - set(sections.keys())
#             )

#             if missing_sections:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             f"Invalid Section IDs: "
#                             f"{sorted(missing_sections)}"
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 8: VALIDATE SUBSECTIONS
#             # ==================================================

#             missing_subsections = (
#                 subsection_ids
#                 - set(subsections.keys())
#             )

#             if missing_subsections:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             f"Invalid SubSection IDs: "
#                             f"{sorted(missing_subsections)}"
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 9: VALIDATE QUESTIONS
#             # ==================================================

#             missing_questions = (
#                 question_ids
#                 - set(questions.keys())
#             )

#             if missing_questions:

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             f"Invalid Question IDs: "
#                             f"{sorted(missing_questions)}"
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 10: DUPLICATE QUESTION VALIDATION
#             # ==================================================

#             all_question_ids = []

#             for grade_data in grades_data:

#                 for section_data in grade_data["sections"]:

#                     for subsection_data in (
#                         section_data["subsections"]
#                     ):

#                         all_question_ids.extend(
#                             subsection_data.get(
#                                 "question_ids",
#                                 []
#                             )
#                         )

#             if len(all_question_ids) != len(
#                 set(all_question_ids)
#             ):

#                 return Response(
#                     {
#                         "success": False,
#                         "message": (
#                             "A question cannot be assigned "
#                             "more than once in the same "
#                             "assessment version."
#                         )
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # ==================================================
#             # STEP 11:
#             # QUESTION -> SUBSECTION VALIDATION
#             # ==================================================

#             for grade_data in grades_data:

#                 grade_id = grade_data.get("grade_id")

#                 if grade_id not in grades:

#                     return Response(
#                         {
#                             "success": False,
#                             "message": (
#                                 f"Grade {grade_id} not found."
#                             )
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # ----------------------------------------------
#                 # Sections are optional for draft
#                 # ----------------------------------------------

#                 for section_data in grade_data.get(
#                     "sections",
#                     []
#                 ):

#                     section_id = section_data.get(
#                         "section_id"
#                     )

#                     section = sections.get(
#                         section_id
#                     )

#                     if not section:

#                         return Response(
#                             {
#                                 "success": False,
#                                 "message": (
#                                     f"Section {section_id} "
#                                     f"not found."
#                                 )
#                             },
#                             status=status.HTTP_400_BAD_REQUEST
#                         )

#                     # ------------------------------------------
#                     # SubSections are optional for draft
#                     # ------------------------------------------

#                     for subsection_data in section_data.get(
#                         "subsections",
#                         []
#                     ):

#                         subsection_id = (
#                             subsection_data.get(
#                                 "subsection_id"
#                             )
#                         )

#                         subsection = subsections.get(
#                             subsection_id
#                         )

#                         if not subsection:

#                             return Response(
#                                 {
#                                     "success": False,
#                                     "message": (
#                                         f"SubSection "
#                                         f"{subsection_id} "
#                                         f"not found."
#                                     )
#                                 },
#                                 status=status.HTTP_400_BAD_REQUEST
#                             )

#                         # --------------------------------------
#                         # Questions are optional for draft
#                         # --------------------------------------

#                         for question_id in subsection_data.get(
#                             "question_ids",
#                             []
#                         ):

#                             question = questions.get(
#                                 question_id
#                             )

#                             if not question:

#                                 return Response(
#                                     {
#                                         "success": False,
#                                         "message": (
#                                             f"Question "
#                                             f"{question_id} "
#                                             f"not found."
#                                         )
#                                     },
#                                     status=status.HTTP_400_BAD_REQUEST
#                                 )

#                             if (
#                                 question.subsection_id
#                                 != subsection_id
#                             ):

#                                 return Response(
#                                     {
#                                         "success": False,
#                                         "message": (
#                                             f"Question "
#                                             f"{question_id} "
#                                             f"does not belong "
#                                             f"to SubSection "
#                                             f"{subsection_id}."
#                                         )
#                                     },
#                                     status=status.HTTP_400_BAD_REQUEST
#                                 )

#             # ==================================================
#             # STEP 12:
#             # DELETE OLD BLUEPRINT
#             # ==================================================

#             if not is_draft:

#                 AssessmentBlueprintItem.objects.filter(
#                     assessment_version=version
#                 ).delete()

#             # ==================================================
#             # STEP 13:
#             # CREATE NEW BLUEPRINT
#             # ==================================================

#             blueprint_objects = []

#             sequence_no = 1

#             for grade_data in grades_data:

#                 grade = grades[
#                     grade_data["grade_id"]
#                 ]

#                 for section_data in grade_data.get(
#                     "sections",
#                     []
#                 ):

#                     section = sections[
#                         section_data["section_id"]
#                     ]

#                     for subsection_data in (
#                         section_data.get(
#                             "subsections",
#                             []
#                         )
#                     ):

#                         subsection = subsections[
#                             subsection_data[
#                                 "subsection_id"
#                             ]
#                         ]

#                         for question_id in (
#                             subsection_data.get(
#                                 "question_ids",
#                                 []
#                             )
#                         ):

#                             blueprint_objects.append(

#                                 AssessmentBlueprintItem(

#                                     assessment_version=version,

#                                     grade=grade,

#                                     section=section,

#                                     subsection=subsection,

#                                     question=questions[
#                                         question_id
#                                     ],

#                                     board=(
#                                         request.data.get(
#                                             "board",
#                                             AssessmentBlueprintItem
#                                             .Board.ALL
#                                         )
#                                     ),

#                                     sequence_no=sequence_no,

#                                     status=(
#                                         AssessmentBlueprintItem
#                                         .Status.ACTIVE
#                                     )
#                                 )
#                             )

#                             sequence_no += 1

#             # ==================================================
#             # STEP 14: BULK CREATE
#             # ==================================================

#             if blueprint_objects:

#                 AssessmentBlueprintItem.objects.bulk_create(
#                     blueprint_objects,
#                     batch_size=500
#                 )

#             # ==================================================
#             # STEP 15: UPDATE VERSION COUNTS
#             # ==================================================

#             blueprint_qs = (
#                 AssessmentBlueprintItem.objects
#                 .filter(
#                     assessment_version=version,
#                     question__isnull=False
#                 )
#             )

#             version.total_sections = (
#                 blueprint_qs
#                 .values("section_id")
#                 .distinct()
#                 .count()
#             )

#             version.total_subsections = (
#                 blueprint_qs
#                 .values("subsection_id")
#                 .distinct()
#                 .count()
#             )

#             version.total_questions = (
#                 blueprint_qs.count()
#             )

#             version.total_marks = (
#                 blueprint_qs
#                 .aggregate(
#                     total=Sum("marks_override")
#                 )["total"]
#                 or Decimal("0")
#             )

#             version.save(
#                 update_fields=[
#                     "total_sections",
#                     "total_subsections",
#                     "total_questions",
#                     "total_marks",
#                     "updated_at",
#                 ]
#             )
            
#             # ==================================================
#             # STEP 16: PUBLISH ASSESSMENT
#             # ==================================================

#             if not is_draft:

#                 # ----------------------------------------------
#                 # Validate blueprint exists
#                 # ----------------------------------------------

#                 blueprint_exists = (
#                     AssessmentBlueprintItem.objects
#                     .filter(
#                         assessment_version=version,
#                         question__isnull=False
#                     )
#                     .exists()
#                 )

#                 if not blueprint_exists:

#                     return Response(
#                         {
#                             "success": False,
#                             "message": (
#                                 "Cannot publish assessment "
#                                 "without blueprint questions."
#                             )
#                         },
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 # ----------------------------------------------
#                 # Update Assessment Version
#                 # DRAFT -> PUBLISHED
#                 # ----------------------------------------------

#                 version.status = (
#                     AssessmentVersion.Status.PUBLISHED
#                 )

#                 version.published_by = (
#                     request.user
#                     if request.user.is_authenticated
#                     else None
#                 )

#                 version.published_at = timezone.now()

#                 version.save(
#                     update_fields=[
#                         "status",
#                         "published_by",
#                         "published_at",
#                         "updated_at",
#                     ]
#                 )

#                 # ----------------------------------------------
#                 # Update Assessment
#                 # DRAFT -> ACTIVE
#                 # ----------------------------------------------

#                 assessment = version.assessment

#                 assessment.status = (
#                     Assessment.Status.ACTIVE
#                 )

#                 assessment.save(
#                     update_fields=[
#                         "status",
#                         "updated_at",
#                     ]
#                 )

#             # ==================================================
#             # STEP 17: RESPONSE
#             # ==================================================

#             return Response(
#                 {
#                     "success": True,

#                     "message": (
#                         "Assessment blueprint "
#                         "updated successfully."
#                     ),

#                     "data": {

#                         "assessment_version": {

#                             "id": version.id,

#                             "public_id": str(
#                                 version.public_id
#                             ),

#                             "version_number":
#                                 version.version_number,

#                             "status":
#                                 version.status,

#                             "total_sections":
#                                 version.total_sections,

#                             "total_subsections":
#                                 version.total_subsections,

#                             "total_questions":
#                                 version.total_questions,

#                             "total_marks":
#                                 version.total_marks,
#                         },

#                         "blueprint": grades_data
#                     }
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except IntegrityError as exc:

#             return Response(
#                 {
#                     "success": False,
#                     "message": (
#                         "Blueprint could not be updated "
#                         "because of a database constraint."
#                     ),
#                     "error": str(exc)
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         except Exception as exc:

#             return Response(
#                 {
#                     "success": False,
#                     "message": (
#                         "Something went wrong while "
#                         "updating the blueprint."
#                     ),
#                     "error": str(exc)
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

class AssessmentBlueprintItemUpdateAPIView(APIView):
    """
    Update complete Assessment Blueprint for an Assessment Version.

    PUT /api/assessment-builder/blueprint/<version_id>/
    """

    @transaction.atomic
    def put(self, request, version_id):

        try:

            # ==================================================
            # STEP 1: GET ASSESSMENT VERSION
            # ==================================================

            version = (
                AssessmentVersion.objects
                .select_for_update()
                .filter(id=version_id)
                .first()
            )

            if not version:

                return Response(
                    {
                        "success": False,
                        "message": "Assessment version not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # ==================================================
            # STEP 1A: GET / CREATE ASSESSMENT
            #
            # assessment.name can be:
            #
            # "1"                    -> Existing Assessment ID 1
            # "Aptitude Assessment"  -> Assessment name
            # ==================================================

            assessment_data = request.data.get(
                "assessment"
            )

            if not assessment_data:

                return Response(
                    {
                        "success": False,
                        "message": "Assessment data is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            assessment_name = assessment_data.get(
                "name"
            )

            if not assessment_name:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Assessment name or ID is required."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            assessment_name = str(
                assessment_name
            ).strip()


            # ==================================================
            # CASE 1:
            # name = "1"
            #
            # Treat as existing Assessment ID
            # ==================================================

            if assessment_name.isdigit():

                assessment_id = int(
                    assessment_name
                )

                assessment = (
                    Assessment.objects
                    .filter(
                        id=assessment_id
                    )
                    .first()
                )

                if not assessment:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Assessment with ID "
                                f"{assessment_id} not found."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )


            # ==================================================
            # CASE 2:
            # name = "Aptitude Assessment"
            #
            # Find existing or create new Assessment
            # ==================================================

            else:

                assessment_type = assessment_data.get(
                    "assessment_type"
                )

                if not assessment_type:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                "assessment_type is required "
                                "when creating a new assessment."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                assessment, created = (
                    Assessment.objects.get_or_create(
                        name=assessment_name,
                        defaults={
                            "short_name": assessment_data.get(
                                "short_name",
                                ""
                            ),
                            "assessment_type": assessment_type,
                            "description": assessment_data.get(
                                "description"
                            ),
                            "default_language": assessment_data.get(
                                "default_language",
                                "en"
                            ),
                        }
                    )
                )

                # ----------------------------------------------
                # Update existing assessment fields
                # ----------------------------------------------

                if not created:

                    update_fields = []

                    for field in [
                        "short_name",
                        "assessment_type",
                        "description",
                        "default_language",
                    ]:

                        value = assessment_data.get(
                            field
                        )

                        if value is not None:

                            setattr(
                                assessment,
                                field,
                                value
                            )

                            update_fields.append(
                                field
                            )

                    if update_fields:

                        assessment.save(
                            update_fields=update_fields
                        )


            # ==================================================
            # STEP 1B:
            # Attach Assessment to this Version
            #
            # ALSO UPDATE VERSION FIELDS IF SENT
            # ==================================================

            version_update_fields = []

            # --------------------------------------------------
            # Attach Assessment
            # --------------------------------------------------

            if version.assessment_id != assessment.id:

                version.assessment = assessment

                version_update_fields.append(
                    "assessment"
                )


            # --------------------------------------------------
            # Update Assessment Version fields
            #
            # Only update fields that are provided.
            # Existing logic is not changed.
            # --------------------------------------------------

            version_data = request.data.get(
                "version"
            )

            if version_data:

                version_field_mapping = {
                    "version_number": "version_number",
                    "version_name": "version_name",
                    "report_template_id": "report_template",
                    "release_date": "release_date",
                    "effective_from": "effective_from",
                    "effective_to": "effective_to",
                    "duration_minutes": "duration_minutes",
                    "allow_resume": "allow_resume",
                    "allow_review": "allow_review",
                    "randomize_sections": "randomize_sections",
                    "show_result_immediately": "show_result_immediately",
                    "instructions": "instructions",
                }

                for request_field, model_field in version_field_mapping.items():

                    if request_field not in version_data:
                        continue

                    value = version_data.get(
                        request_field
                    )

                    # ----------------------------------------------
                    # Foreign Key: report_template_id
                    # ----------------------------------------------

                    if request_field == "report_template_id":

                        if value is not None:

                            report_template = (
                                ReportTemplate.objects
                                .filter(id=value)
                                .first()
                            )

                            if not report_template:

                                return Response(
                                    {
                                        "success": False,
                                        "message": (
                                            f"Report template with ID "
                                            f"{value} not found."
                                        )
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

                            version.report_template = (
                                report_template
                            )

                            version_update_fields.append(
                                "report_template"
                            )

                        else:

                            version.report_template = None

                            version_update_fields.append(
                                "report_template"
                            )

                    # ----------------------------------------------
                    # Normal fields
                    # ----------------------------------------------

                    else:

                        setattr(
                            version,
                            model_field,
                            value
                        )

                        version_update_fields.append(
                            model_field
                        )


            # --------------------------------------------------
            # Save Version
            # --------------------------------------------------

            if version_update_fields:

                version_update_fields.append(
                    "updated_at"
                )

                version.save(
                    update_fields=list(
                        set(version_update_fields)
                    )
                )
    
            # ==================================================
            # STEP 2: CHECK VERSION STATUS
            # ==================================================

            if (
                version.status
                == AssessmentVersion.Status.PUBLISHED
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Published assessment version "
                            "cannot be modified."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==================================================
            # STEP 3: GET INPUT
            # ==================================================

            blueprint_items = request.data.get(
                "blueprint_items"
            )

            is_draft = request.data.get(
                "is_draft",
                True
            )
            
            blueprint_status = (
                AssessmentBlueprintItem.Status.DRAFT
                if is_draft
                else AssessmentBlueprintItem.Status.ACTIVE
            )

            # --------------------------------------------------
            # If blueprint_items are not provided
            # --------------------------------------------------
            #
            # Draft:
            #     Allow update without blueprint_items.
            #
            # Publish:
            #     blueprint_items are required.
            # --------------------------------------------------

            if not blueprint_items:

                if not is_draft:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                "blueprint_items is required "
                                "when publishing."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # --------------------------------------------------
                # Draft update without blueprint
                #
                # Do not change existing blueprint.
                # Simply continue and return success.
                # --------------------------------------------------

                return Response(
                    {
                        "success": True,

                        "message": (
                            "Assessment draft updated successfully."
                        ),

                        "data": {
                            "assessment_version": {
                                "id": version.id,

                                "public_id": str(
                                    version.public_id
                                ),

                                "version_number":
                                    version.version_number,

                                "status":
                                    version.status,

                                "total_sections":
                                    version.total_sections,

                                "total_subsections":
                                    version.total_subsections,

                                "total_questions":
                                    version.total_questions,

                                "total_marks":
                                    version.total_marks,
                            },

                            "blueprint": None
                        }
                    },
                    status=status.HTTP_200_OK
                )

            # ==================================================
            # STEP 4: PUBLISH VALIDATION
            # ==================================================

            if not is_draft:

                for grade_data in blueprint_items:

                    # ------------------------------------------
                    # GRADE
                    # ------------------------------------------

                    if not grade_data.get("grade_id"):

                        return Response(
                            {
                                "success": False,
                                "message": (
                                    "Grade ID is required "
                                    "when publishing."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ------------------------------------------
                    # BOARD
                    # ------------------------------------------

                    if not grade_data.get("board"):

                        return Response(
                            {
                                "success": False,
                                "message": (
                                    "Board is required "
                                    "when publishing."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ------------------------------------------
                    # SECTIONS
                    # ------------------------------------------

                    if not grade_data.get("sections"):

                        return Response(
                            {
                                "success": False,
                                "message": (
                                    "Sections are required "
                                    "when publishing."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    for section_data in grade_data["sections"]:

                        # --------------------------------------
                        # SUBSECTIONS
                        # --------------------------------------

                        if not section_data.get("subsections"):

                            return Response(
                                {
                                    "success": False,
                                    "message": (
                                        "SubSections are required "
                                        "when publishing."
                                    )
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        for subsection_data in section_data[
                            "subsections"
                        ]:

                            # ----------------------------------
                            # QUESTIONS
                            # ----------------------------------

                            if not subsection_data.get(
                                "question_ids"
                            ):

                                return Response(
                                    {
                                        "success": False,
                                        "message": (
                                            "Question IDs are required "
                                            "when publishing."
                                        )
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

            # ==================================================
            # STEP 5: COLLECT IDS
            # ==================================================

            grade_ids = set()
            section_ids = set()
            subsection_ids = set()
            question_ids = set()

            for grade_data in blueprint_items:

                grade_id = grade_data.get("grade_id")

                if grade_id:
                    grade_ids.add(grade_id)

                for section_data in grade_data.get(
                    "sections",
                    []
                ):

                    section_id = section_data.get(
                        "section_id"
                    )

                    if section_id:
                        section_ids.add(section_id)

                    for subsection_data in section_data.get(
                        "subsections",
                        []
                    ):

                        subsection_id = subsection_data.get(
                            "subsection_id"
                        )

                        if subsection_id:
                            subsection_ids.add(
                                subsection_id
                            )

                        question_ids.update(
                            subsection_data.get(
                                "question_ids",
                                []
                            )
                        )

            # ==================================================
            # STEP 6: FETCH MASTER DATA
            # ==================================================

            grades = {
                obj.id: obj
                for obj in Grade.objects.filter(
                    id__in=grade_ids
                )
            }

            sections = {
                obj.id: obj
                for obj in Section.objects.filter(
                    id__in=section_ids
                )
            }

            subsections = {
                obj.id: obj
                for obj in SubSection.objects.filter(
                    id__in=subsection_ids
                )
            }

            questions = {
                obj.id: obj
                for obj in Question.objects.filter(
                    id__in=question_ids
                )
            }

            # ==================================================
            # STEP 7: VALIDATE MASTER IDS
            # ==================================================

            missing_grades = (
                grade_ids - set(grades.keys())
            )

            if missing_grades:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Invalid Grade IDs: "
                            f"{sorted(missing_grades)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            missing_sections = (
                section_ids - set(sections.keys())
            )

            if missing_sections:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Invalid Section IDs: "
                            f"{sorted(missing_sections)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            missing_subsections = (
                subsection_ids
                - set(subsections.keys())
            )

            if missing_subsections:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Invalid SubSection IDs: "
                            f"{sorted(missing_subsections)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            missing_questions = (
                question_ids
                - set(questions.keys())
            )

            if missing_questions:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Invalid Question IDs: "
                            f"{sorted(missing_questions)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==================================================
            # STEP 8:
            # DUPLICATE QUESTION VALIDATION
            #
            # Same question CAN be used for different grades.
            #
            # Allowed:
            #
            # Grade 25 + Section 19 + SubSection 29 + Question 20
            # Grade 29 + Section 20 + SubSection 29 + Question 20
            #
            # Not allowed:
            #
            # Grade 25 + Section 19 + SubSection 29 + Question 20
            # Grade 25 + Section 19 + SubSection 29 + Question 20
            # ==================================================

            assigned_questions = set()

            for grade_data in blueprint_items:

                grade_id = grade_data.get(
                    "grade_id"
                )

                for section_data in grade_data.get(
                    "sections",
                    []
                ):

                    section_id = section_data.get(
                        "section_id"
                    )

                    for subsection_data in section_data.get(
                        "subsections",
                        []
                    ):

                        subsection_id = subsection_data.get(
                            "subsection_id"
                        )

                        for question_id in subsection_data.get(
                            "question_ids",
                            []
                        ):

                            assignment_key = (
                                grade_id,
                                section_id,
                                subsection_id,
                                question_id,
                            )

                            if assignment_key in assigned_questions:

                                return Response(
                                    {
                                        "success": False,
                                        "message": (
                                            f"Question {question_id} "
                                            f"is already assigned to "
                                            f"Grade {grade_id}, "
                                            f"Section {section_id}, "
                                            f"SubSection {subsection_id}."
                                        )
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

                            assigned_questions.add(
                                assignment_key
                            )

            # ==================================================
            # STEP 9:
            # VALIDATE HIERARCHY
            #
            # Question does NOT contain subsection_id.
            #
            # Relationship:
            #
            # Grade
            #   ↓
            # Section
            #   ↓
            # SubSection
            #   ↓
            # Blueprint Item
            #   ↓
            # Question
            # ==================================================

            for grade_data in blueprint_items:

                grade_id = grade_data.get("grade_id")

                grade = grades.get(grade_id)

                if not grade:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                f"Grade {grade_id} not found."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # --------------------------------------------------
                # Sections
                # --------------------------------------------------

                for section_data in grade_data.get(
                    "sections",
                    []
                ):

                    section_id = section_data.get(
                        "section_id"
                    )

                    section = sections.get(
                        section_id
                    )

                    if not section:

                        return Response(
                            {
                                "success": False,
                                "message": (
                                    f"Section {section_id} "
                                    f"not found."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # --------------------------------------------------
                    # SubSections
                    # --------------------------------------------------

                    for subsection_data in section_data.get(
                        "subsections",
                        []
                    ):

                        subsection_id = subsection_data.get(
                            "subsection_id"
                        )

                        subsection = subsections.get(
                            subsection_id
                        )

                        if not subsection:

                            return Response(
                                {
                                    "success": False,
                                    "message": (
                                        f"SubSection "
                                        f"{subsection_id} "
                                        f"not found."
                                    )
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        # --------------------------------------------------
                        # Questions
                        #
                        # Question does NOT have subsection_id.
                        # Therefore, only validate that the question exists.
                        # --------------------------------------------------

                        for question_id in subsection_data.get(
                            "question_ids",
                            []
                        ):

                            question = questions.get(
                                question_id
                            )

                            if not question:

                                return Response(
                                    {
                                        "success": False,
                                        "message": (
                                            f"Question "
                                            f"{question_id} "
                                            f"not found."
                                        )
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

            # ==================================================
            # STEP 10:
            # QUESTION -> GRADE MAPPING
            # ==================================================

            question_grade_mappings = set(
                QuestionGradeMapping.objects.filter(
                    question_id__in=question_ids,
                    grade_id__in=grade_ids,
                ).values_list(
                    "question_id",
                    "grade_id",
                )
            )

            for grade_data in blueprint_items:

                grade_id = grade_data.get(
                    "grade_id"
                )

                for section_data in grade_data.get(
                    "sections",
                    []
                ):

                    for subsection_data in section_data.get(
                        "subsections",
                        []
                    ):

                        for question_id in subsection_data.get(
                            "question_ids",
                            []
                        ):

                            if (
                                question_id,
                                grade_id
                            ) not in question_grade_mappings:

                                return Response(
                                    {
                                        "success": False,
                                        "message": (
                                            f"Question "
                                            f"{question_id} "
                                            f"is not mapped "
                                            f"to Grade "
                                            f"{grade_id}."
                                        )
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

            # ==================================================
            # STEP 11:
            # UPDATE / CREATE BLUEPRINT ITEMS
            #
            # IMPORTANT:
            # Existing blueprint rows are NOT deleted.
            #
            # Logic:
            # 1. Exact existing combination -> UPDATE
            # 2. Empty blueprint row -> REUSE ONLY ONCE
            # 3. If no empty row remains -> CREATE NEW
            #
            # Example:
            #
            # Existing DB:
            #   id=10, grade=NULL, section=NULL,
            #          subsection=NULL, question=NULL
            #
            # Request:
            #   Grade 25
            #   Grade 29
            #
            # Result:
            #
            #   id=10 -> Grade 25
            #   new id=11 -> Grade 29
            #
            # NEVER use id=10 for both grades.
            # ==================================================

            existing_blueprint_qs = (
                AssessmentBlueprintItem.objects
                .filter(
                    assessment_version_id=version_id
                )
                .order_by("id")
            )

            existing_blueprints = {
                (
                    item.assessment_version_id,
                    item.grade_id,
                    item.board,
                    item.section_id,
                    item.subsection_id,
                    item.question_id,
                ): item
                for item in existing_blueprint_qs
            }
            
            # ==========================================================
            # HELPER:
            # FIND EXISTING BLUEPRINT
            #
            # Priority:
            #
            # 1. Exact combination
            # 2. Same grade + board + section
            # 3. Same grade + board + section + subsection
            # 4. Existing grade-only row
            #
            # This prevents duplicate rows for the same grade.
            # ==========================================================

            def find_existing_blueprint(
                grade_id,
                board,
                section_id=None,
                subsection_id=None,
                question_id=None,
            ):
                """
                Find an existing blueprint row for UPDATE.

                Priority:
                1. Exact combination
                2. Same version + section + subsection + question
                -> allows grade to be changed
                3. Same version + grade + section + subsection
                -> allows question to be changed
                4. Same version + grade + section
                5. Same version + grade only

                IMPORTANT:
                Exact match always has highest priority.
                """

                # ==========================================================
                # 1. EXACT MATCH
                # ==========================================================

                exact_key = (
                    version_id,
                    grade_id,
                    board,
                    section_id,
                    subsection_id,
                    question_id,
                )

                existing_item = existing_blueprints.get(exact_key)

                if existing_item:
                    return existing_item


                # ==========================================================
                # 2. GRADE UPDATE
                #
                # Existing:
                # version 1 + grade 25 + section 19 + subsection 29
                #
                # Request:
                # version 1 + grade 29 + section 19 + subsection 29
                #
                # Update grade instead of creating a new row.
                #
                # Only use this when the lower hierarchy matches.
                # ==========================================================

                if (
                    section_id is not None
                    and subsection_id is not None
                    and question_id is not None
                ):

                    for item in existing_blueprint_qs:
                        
                        if item.id in used_blueprint_ids:
                            continue

                        if (
                            item.board == board
                            and item.section_id == section_id
                            and item.subsection_id == subsection_id
                            and item.question_id == question_id
                        ):
                            return item


                # ==========================================================
                # 3. SUBSECTION UPDATE
                #
                # Existing:
                # version 1 + grade 25 + section 19 + subsection 29
                #
                # Request:
                # version 1 + grade 25 + section 19 + subsection 30
                #
                # This is harder to distinguish from adding a new subsection.
                #
                # Therefore only match an existing subsection-only row.
                # ==========================================================

                if (
                    section_id is not None
                    and subsection_id is not None
                    and question_id is None
                ):

                    for item in existing_blueprint_qs:

                        if (
                            item.grade_id == grade_id
                            and item.board == board
                            and item.section_id == section_id
                            and item.subsection_id is not None
                            and item.question_id is None
                        ):

                            return item


                # ==========================================================
                # 4. SAME GRADE + BOARD + SECTION + SUBSECTION
                # ==========================================================

                if section_id is not None and subsection_id is not None:

                    for item in existing_blueprint_qs:

                        if (
                            item.grade_id == grade_id
                            and item.board == board
                            and item.section_id == section_id
                            and item.subsection_id == subsection_id
                            and item.question_id is None
                        ):
                            return item


                # ==========================================================
                # 5. SAME GRADE + BOARD + SECTION
                # ==========================================================

                if section_id is not None:

                    for item in existing_blueprint_qs:

                        if (
                            item.grade_id == grade_id
                            and item.board == board
                            and item.section_id == section_id
                            and item.subsection_id is None
                            and item.question_id is None
                        ):
                            return item


                # ==========================================================
                # 6. SAME GRADE + BOARD ONLY
                # ==========================================================

                for item in existing_blueprint_qs:

                    if (
                        item.grade_id == grade_id
                        and item.board == board
                        and item.section_id is None
                        and item.subsection_id is None
                        and item.question_id is None
                    ):
                        return item


                return None

            # ==================================================
            # GET EMPTY BLUEPRINT RECORDS
            # ==================================================

            empty_blueprints = list(
                AssessmentBlueprintItem.objects.filter(
                    assessment_version_id=version_id,
                    grade__isnull=True,
                    section__isnull=True,
                    subsection__isnull=True,
                    question__isnull=True,
                ).order_by("id")
            )


            # ==================================================
            # IMPORTANT:
            # Keep track of EMPTY ROWS ALREADY CONSUMED
            #
            # Once an empty row is assigned to Grade 25,
            # it must NEVER be reused for Grade 29.
            # ==================================================

            used_empty_blueprint_ids = set()
            
            used_blueprint_ids = set()


            sequence_no = 1

            new_blueprint_objects = []
            update_blueprint_objects = []


            # ==================================================
            # HELPER:
            # GET EMPTY BLUEPRINT ONLY ONCE
            # ==================================================

            def get_reusable_empty_blueprint():

                for empty_item in empty_blueprints:

                    if empty_item.id not in used_empty_blueprint_ids:

                        used_empty_blueprint_ids.add(
                            empty_item.id
                        )

                        return empty_item

                return None


            # ==================================================
            # PROCESS BLUEPRINT ITEMS
            # ==================================================

            for grade_data in blueprint_items:

                # ----------------------------------------------
                # GRADE
                # ----------------------------------------------

                grade_id = grade_data["grade_id"]

                grade = grades[grade_id]

                board = grade_data.get(
                    "board",
                    AssessmentBlueprintItem.Board.ALL
                )

                # ----------------------------------------------
                # SECTIONS
                # ----------------------------------------------

                sections_data = grade_data.get(
                    "sections",
                    []
                )


                # ==================================================
                # CASE 1:
                # ONLY GRADE
                #
                # Example:
                #
                # {
                #     "grade_id": 25,
                #     "board": "ALL",
                #     "sections": []
                # }
                # ==================================================

                if not sections_data:

                    blueprint_key = (
                        version_id,
                        grade_id,
                        board,
                        None,
                        None,
                        None,
                    )


                    # ==================================================
                    # 1. EXACT EXISTING RECORD
                    # ==================================================

                    existing_item = existing_blueprints.get(
                        blueprint_key
                    )


                    # ==================================================
                    # 2. REUSE ONE EMPTY RECORD
                    #
                    # ONLY if exact record does not exist.
                    # ==================================================

                    if not existing_item:

                        existing_item = (
                            get_reusable_empty_blueprint()
                        )


                    # ==================================================
                    # EXISTING / EMPTY RECORD -> UPDATE
                    # ==================================================

                    if existing_item:

                        existing_item.grade = grade
                        existing_item.board = board
                        existing_item.section = None
                        existing_item.subsection = None
                        existing_item.question = None

                        existing_item.sequence_no = sequence_no

                        existing_item.marks_override = (
                            grade_data.get(
                                "marks_override"
                            )
                        )

                        existing_item.negative_marks_override = (
                            grade_data.get(
                                "negative_marks_override"
                            )
                        )

                        existing_item.status = blueprint_status

                        update_blueprint_objects.append(
                            existing_item
                        )

                        # ------------------------------------------
                        # VERY IMPORTANT
                        #
                        # Add the updated record into the dictionary.
                        #
                        # This prevents another request item from
                        # accidentally selecting the same record.
                        # ------------------------------------------

                        existing_blueprints[
                            blueprint_key
                        ] = existing_item


                    # ==================================================
                    # NO EMPTY RECORD LEFT -> CREATE NEW
                    # ==================================================

                    else:

                        new_blueprint_objects.append(
                            AssessmentBlueprintItem(

                                assessment_version=version,

                                grade=grade,

                                section=None,

                                subsection=None,

                                question=None,

                                board=board,

                                sequence_no=sequence_no,

                                marks_override=(
                                    grade_data.get(
                                        "marks_override"
                                    )
                                ),

                                negative_marks_override=(
                                    grade_data.get(
                                        "negative_marks_override"
                                    )
                                ),

                                status=blueprint_status,
                            )
                        )


                    sequence_no += 1

                    continue


                # ==================================================
                # CASE 2 / 3 / 4:
                #
                # GRADE + SECTION
                # GRADE + SECTION + SUBSECTION
                # GRADE + SECTION + SUBSECTION + QUESTION
                # ==================================================

                for section_data in sections_data:

                    # ==========================================================
                    # SECTION
                    # ==========================================================

                    section_id = section_data.get("section_id")

                    if not section_id:
                        continue

                    section = sections.get(section_id)

                    if not section:
                        return Response(
                            {
                                "success": False,
                                "message": f"Section {section_id} not found."
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ==========================================================
                    # CHECK WHETHER SUBSECTIONS WERE SENT
                    # ==========================================================

                    subsections_data = section_data.get("subsections", [])


                    # ==========================================================
                    # SECTION ONLY
                    #
                    # Example:
                    #
                    # {
                    #     "grade_id": 25,
                    #     "board": "ALL",
                    #     "sections": [
                    #         {
                    #             "section_id": 19
                    #         }
                    #     ]
                    # }
                    #
                    # Store:
                    #
                    # grade = 25
                    # section = 19
                    # subsection = NULL
                    # question = NULL
                    # ==========================================================

                    if not subsections_data:

                        existing_item = find_existing_blueprint(
                            grade_id=grade_id,
                            board=board,
                            section_id=section_id,
                            subsection_id=None,
                            question_id=None,
                        )

                        if existing_item:
                            
                            used_blueprint_ids.add(existing_item.id)

                            # ----------------------------------------------
                            # UPDATE EXISTING ROW
                            # ----------------------------------------------

                            existing_item.grade = grade
                            existing_item.board = board
                            existing_item.section = section
                            existing_item.subsection = None
                            existing_item.question = None

                            existing_item.sequence_no = sequence_no

                            existing_item.marks_override = (
                                section_data.get(
                                    "marks_override"
                                )
                            )

                            existing_item.negative_marks_override = (
                                section_data.get(
                                    "negative_marks_override"
                                )
                            )

                            # IMPORTANT:
                            # draft -> DRAFT
                            # publish -> ACTIVE
                            existing_item.status = blueprint_status

                            update_blueprint_objects.append(
                                existing_item
                            )

                        else:

                            # ----------------------------------------------
                            # CREATE ONLY IF SAME GRADE/SECTION DOES NOT EXIST
                            # ----------------------------------------------

                            new_blueprint_objects.append(
                                AssessmentBlueprintItem(
                                    assessment_version=version,

                                    grade=grade,

                                    board=board,

                                    section=section,

                                    subsection=None,

                                    question=None,

                                    sequence_no=sequence_no,

                                    marks_override=(
                                        section_data.get(
                                            "marks_override"
                                        )
                                    ),

                                    negative_marks_override=(
                                        section_data.get(
                                            "negative_marks_override"
                                        )
                                    ),

                                    status=blueprint_status,
                                )
                            )

                        sequence_no += 1

                        continue
                    
                    
                    # ==========================================================
                    # SUBSECTION / QUESTION LEVEL
                    # ==========================================================

                    for subsection_data in subsections_data:

                        subsection_id = subsection_data.get(
                            "subsection_id"
                        )

                        if not subsection_id:
                            continue

                        subsection = subsections.get(
                            subsection_id
                        )

                        if not subsection:
                            return Response(
                                {
                                    "success": False,
                                    "message": (
                                        f"SubSection "
                                        f"{subsection_id} not found."
                                    )
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        question_list = subsection_data.get(
                            "question_ids",
                            []
                        )

                        # ======================================================
                        # SUBSECTION ONLY
                        # ======================================================

                        if not question_list:

                            subsection_key = (
                                version_id,
                                grade_id,
                                board,
                                section_id,
                                subsection_id,
                                None,
                            )

                            existing_item = existing_blueprints.get(
                                subsection_key
                            )

                            # --------------------------------------------------
                            # 1. EXISTING EXACT SUBSECTION
                            # --------------------------------------------------

                            if existing_item:
                                
                                used_blueprint_ids.add(existing_item.id)

                                existing_item.grade = grade
                                existing_item.board = board
                                existing_item.section = section
                                existing_item.subsection = subsection
                                existing_item.question = None

                                existing_item.sequence_no = sequence_no

                                existing_item.marks_override = (
                                    subsection_data.get("marks_override")
                                )

                                existing_item.negative_marks_override = (
                                    subsection_data.get("negative_marks_override")
                                )

                                existing_item.status = blueprint_status

                                update_blueprint_objects.append(
                                    existing_item
                                )

                            # --------------------------------------------------
                            # 2. EXISTING SECTION-ONLY RECORD
                            # --------------------------------------------------

                            if not existing_item:

                                section_key = (
                                    version_id,
                                    grade_id,
                                    board,
                                    section_id,
                                    None,
                                    None,
                                )

                                existing_item = existing_blueprints.get(
                                    section_key
                                )

                                if existing_item:

                                    existing_blueprints.pop(
                                        section_key,
                                        None
                                    )

                            # --------------------------------------------------
                            # 3. EXISTING GRADE-ONLY RECORD
                            #
                            # Example:
                            #
                            # Existing:
                            # grade = 25
                            # board = CBSE
                            # section = NULL
                            # subsection = NULL
                            # question = NULL
                            #
                            # Request:
                            # grade = 25
                            # board = CBSE
                            # section = 19
                            # subsection = 30
                            #
                            # Reuse the existing record.
                            # --------------------------------------------------

                            if not existing_item:

                                grade_only_key = (
                                    version_id,
                                    grade_id,
                                    board,
                                    None,
                                    None,
                                    None,
                                )

                                existing_item = existing_blueprints.get(
                                    grade_only_key
                                )

                                if existing_item:

                                    existing_blueprints.pop(
                                        grade_only_key,
                                        None
                                    )

                            # --------------------------------------------------
                            # 4. EXISTING GRADE-ONLY RECORD WITH DIFFERENT BOARD
                            #
                            # USE THIS ONLY IF:
                            # one blueprint per grade is allowed and board can
                            # be changed from ALL -> CBSE or CBSE -> ALL.
                            # --------------------------------------------------

                            if not existing_item:

                                for item in existing_blueprint_qs:

                                    if (
                                        item.grade_id == grade_id
                                        and item.section_id is None
                                        and item.subsection_id is None
                                        and item.question_id is None
                                    ):

                                        existing_item = item

                                        existing_blueprints.pop(
                                            (
                                                version_id,
                                                item.grade_id,
                                                item.board,
                                                None,
                                                None,
                                                None,
                                            ),
                                            None
                                        )

                                        break

                            # --------------------------------------------------
                            # 5. REUSE EMPTY RECORD
                            # --------------------------------------------------

                            if not existing_item:

                                existing_item = (
                                    get_reusable_empty_blueprint()
                                )

                            # --------------------------------------------------
                            # 6. UPDATE EXISTING RECORD
                            # --------------------------------------------------

                            if existing_item:
                                
                                used_blueprint_ids.add(existing_item.id)

                                existing_item.grade = grade
                                existing_item.board = board
                                existing_item.section = section
                                existing_item.subsection = subsection
                                existing_item.question = None

                                existing_item.sequence_no = sequence_no

                                existing_item.marks_override = (
                                    subsection_data.get(
                                        "marks_override"
                                    )
                                )

                                existing_item.negative_marks_override = (
                                    subsection_data.get(
                                        "negative_marks_override"
                                    )
                                )

                                existing_item.status = blueprint_status

                                update_blueprint_objects.append(
                                    existing_item
                                )

                                # Add new key
                                existing_blueprints[
                                    subsection_key
                                ] = existing_item

                            # --------------------------------------------------
                            # 7. CREATE ONLY IF NOTHING EXISTS
                            # --------------------------------------------------

                            else:

                                new_blueprint_objects.append(
                                    AssessmentBlueprintItem(
                                        assessment_version=version,
                                        grade=grade,
                                        board=board,
                                        section=section,
                                        subsection=subsection,
                                        question=None,
                                        sequence_no=sequence_no,

                                        marks_override=(
                                            subsection_data.get(
                                                "marks_override"
                                            )
                                        ),

                                        negative_marks_override=(
                                            subsection_data.get(
                                                "negative_marks_override"
                                            )
                                        ),

                                        status=blueprint_status,
                                    )
                                )

                            sequence_no += 1

                            continue

                        # ======================================================
                        # QUESTION LEVEL
                        # ======================================================

                        for question_id in question_list:

                            question = questions.get(question_id)

                            if not question:
                                return Response(
                                    {
                                        "success": False,
                                        "message": f"Question {question_id} not found."
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )

                            question_key = (
                                version_id,
                                grade_id,
                                board,
                                section_id,
                                subsection_id,
                                question_id,
                            )

                            # ==================================================
                            # 1. EXACT QUESTION RECORD
                            # ==================================================

                            existing_item = existing_blueprints.get(
                                question_key
                            )
                            
                            # ==================================================
                            # 1A. UPDATE EXISTING RECORD WHEN GRADE CHANGES
                            #
                            # Existing:
                            # version 1
                            # grade 25
                            # section 19
                            # subsection 29
                            # question 20
                            #
                            # Request:
                            # version 1
                            # grade 29
                            # section 19
                            # subsection 29
                            # question 20
                            #
                            # Same hierarchy -> update grade.
                            # ==================================================

                            if not existing_item:

                                for item in existing_blueprint_qs:

                                    if (
                                        item.section_id == section_id
                                        and item.subsection_id == subsection_id
                                        and item.question_id == question_id
                                        and item.board == board
                                    ):
                                        existing_item = item

                                        # Remove old dictionary key
                                        existing_blueprints.pop(
                                            (
                                                version_id,
                                                item.grade_id,
                                                item.board,
                                                item.section_id,
                                                item.subsection_id,
                                                item.question_id,
                                            ),
                                            None
                                        )

                                        break

                            # ==================================================
                            # 2. EXISTING SUBSECTION-ONLY RECORD
                            # ==================================================

                            if not existing_item:

                                subsection_key = (
                                    version_id,
                                    grade_id,
                                    board,
                                    section_id,
                                    subsection_id,
                                    None,
                                )

                                existing_subsection_item = (
                                    existing_blueprints.get(
                                        subsection_key
                                    )
                                )

                                if existing_subsection_item:

                                    existing_item = existing_subsection_item

                                    existing_blueprints.pop(
                                        subsection_key,
                                        None
                                    )

                            # ==================================================
                            # 3. EXISTING SECTION-ONLY RECORD
                            # ==================================================

                            if not existing_item:

                                section_key = (
                                    version_id,
                                    grade_id,
                                    board,
                                    section_id,
                                    None,
                                    None,
                                )

                                existing_section_item = (
                                    existing_blueprints.get(
                                        section_key
                                    )
                                )

                                if existing_section_item:

                                    existing_item = existing_section_item

                                    existing_blueprints.pop(
                                        section_key,
                                        None
                                    )

                            # ==================================================
                            # 4. EXISTING GRADE-ONLY RECORD
                            #
                            # THIS IS THE IMPORTANT FIX
                            #
                            # Existing:
                            #
                            # Grade 11
                            # Board CBSE
                            # Section NULL
                            # SubSection NULL
                            # Question NULL
                            #
                            # Request:
                            #
                            # Grade 11
                            # Board CBSE
                            # Section Aptitude
                            # SubSection Logical Reasoning
                            # Question 1
                            #
                            # Reuse the existing grade-only row.
                            # ==================================================

                            if not existing_item:

                                grade_only_key = (
                                    version_id,
                                    grade_id,
                                    board,
                                    None,
                                    None,
                                    None,
                                )

                                existing_grade_item = (
                                    existing_blueprints.get(
                                        grade_only_key
                                    )
                                )

                                if existing_grade_item:

                                    existing_item = existing_grade_item

                                    existing_blueprints.pop(
                                        grade_only_key,
                                        None
                                    )

                            # ==================================================
                            # 5. REUSE EMPTY RECORD
                            # ==================================================

                            if not existing_item:

                                existing_item = (
                                    get_reusable_empty_blueprint()
                                )

                            # ==================================================
                            # 6. UPDATE EXISTING RECORD
                            # ==================================================

                            if existing_item:
                                
                                used_blueprint_ids.add(existing_item.id)

                                existing_item.grade = grade
                                existing_item.board = board
                                existing_item.section = section
                                existing_item.subsection = subsection
                                existing_item.question = question

                                existing_item.sequence_no = sequence_no

                                existing_item.marks_override = (
                                    subsection_data.get(
                                        "marks_override"
                                    )
                                )

                                existing_item.negative_marks_override = (
                                    subsection_data.get(
                                        "negative_marks_override"
                                    )
                                )

                                # IMPORTANT:
                                # draft  -> DRAFT
                                # publish -> ACTIVE
                                existing_item.status = blueprint_status

                                update_blueprint_objects.append(
                                    existing_item
                                )

                                # Add the NEW combination to dictionary
                                existing_blueprints[
                                    question_key
                                ] = existing_item

                            # ==================================================
                            # 7. CREATE ONLY IF NOTHING EXISTS
                            # ==================================================

                            else:

                                new_blueprint_objects.append(
                                    AssessmentBlueprintItem(
                                        assessment_version=version,
                                        grade=grade,
                                        board=board,
                                        section=section,
                                        subsection=subsection,
                                        question=question,
                                        sequence_no=sequence_no,

                                        marks_override=(
                                            subsection_data.get(
                                                "marks_override"
                                            )
                                        ),

                                        negative_marks_override=(
                                            subsection_data.get(
                                                "negative_marks_override"
                                            )
                                        ),

                                        status=blueprint_status,
                                    )
                                )

                            sequence_no += 1
            
            
            # ==================================================
            # STEP 12:
            # BULK CREATE NEW RECORDS
            # ==================================================

            if new_blueprint_objects:

                AssessmentBlueprintItem.objects.bulk_create(
                    new_blueprint_objects,
                    batch_size=500
                )


            # ==================================================
            # STEP 13:
            # BULK UPDATE EXISTING RECORDS
            # ==================================================

            if update_blueprint_objects:

                AssessmentBlueprintItem.objects.bulk_update(
                    update_blueprint_objects,
                    fields=[
                        "grade",
                        "board",
                        "section",
                        "subsection",
                        "question",
                        "sequence_no",
                        "marks_override",
                        "negative_marks_override",
                        "status",
                    ],
                    batch_size=500
                )

            # ==================================================
            # STEP 14: UPDATE VERSION COUNTS
            # ==================================================

            blueprint_qs = (
                AssessmentBlueprintItem.objects
                .filter(
                    assessment_version=version,
                    question__isnull=False
                )
            )

            version.total_sections = (
                blueprint_qs
                .values("section_id")
                .distinct()
                .count()
            )

            version.total_subsections = (
                blueprint_qs
                .values("subsection_id")
                .distinct()
                .count()
            )

            version.total_questions = (
                blueprint_qs.count()
            )

            version.total_marks = (
                blueprint_qs
                .aggregate(
                    total=Sum("marks_override")
                )["total"]
                or Decimal("0")
            )

            version.save(
                update_fields=[
                    "total_sections",
                    "total_subsections",
                    "total_questions",
                    "total_marks",
                    "updated_at",
                ]
            )

            # ==================================================
            # STEP 15: PUBLISH
            # ==================================================

            if not is_draft:

                blueprint_exists = (
                    AssessmentBlueprintItem.objects
                    .filter(
                        assessment_version=version,
                        question__isnull=False
                    )
                    .exists()
                )

                if not blueprint_exists:

                    return Response(
                        {
                            "success": False,
                            "message": (
                                "Cannot publish assessment "
                                "without blueprint questions."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                version.status = (
                    AssessmentVersion.Status.PUBLISHED
                )

                version.published_by = (
                    request.user
                    if request.user.is_authenticated
                    else None
                )

                version.published_at = timezone.now()

                version.save(
                    update_fields=[
                        "status",
                        "published_by",
                        "published_at",
                        "updated_at",
                    ]
                )

                assessment = version.assessment

                assessment.status = (
                    Assessment.Status.ACTIVE
                )

                assessment.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            # ==================================================
            # STEP 16: RESPONSE
            # ==================================================

            # --------------------------------------------------
            # Build response blueprint with question details
            # --------------------------------------------------

            response_blueprint = []

            for grade_data in blueprint_items:

                grade_response = {
                    "grade_id": grade_data.get("grade_id"),
                    "board": grade_data.get("board"),
                    "sections": []
                }

                for section_data in grade_data.get("sections", []):

                    section_response = {
                        "section_id": section_data.get("section_id"),
                        "subsections": []
                    }

                    for subsection_data in section_data.get(
                        "subsections",
                        []
                    ):

                        question_details = []

                        for question_id in subsection_data.get(
                            "question_ids",
                            []
                        ):

                            question = questions.get(question_id)

                            question_details.append(
                                {
                                    "id": question_id,
                                    "question_text": (
                                        question.question_text
                                        if question
                                        else None
                                    )
                                }
                            )

                        subsection_response = {
                            "subsection_id": subsection_data.get(
                                "subsection_id"
                            ),
                            "questions": question_details
                        }

                        section_response["subsections"].append(
                            subsection_response
                        )

                    grade_response["sections"].append(
                        section_response
                    )

                response_blueprint.append(
                    grade_response
                )


            return Response(
                {
                    "success": True,

                    "message": (
                        "Assessment blueprint "
                        "updated successfully."
                    ),

                    "data": {

                        "assessment_version": {

                            "id": version.id,

                            "public_id": str(
                                version.public_id
                            ),

                            "version_number":
                                version.version_number,

                            "status":
                                version.status,

                            "total_sections":
                                version.total_sections,

                            "total_subsections":
                                version.total_subsections,

                            "total_questions":
                                version.total_questions,

                            "total_marks":
                                version.total_marks,
                        },

                        "blueprint": response_blueprint
                    }
                },

                status=status.HTTP_200_OK
            )

        except IntegrityError as exc:

            return Response(
                {
                    "success": False,

                    "message": (
                        "Blueprint could not be updated "
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
                        "Something went wrong while "
                        "updating the blueprint."
                    ),

                    "error": str(exc)
                },

                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssessmentBlueprintListAPIView(APIView):
    """
    Fetch Assessment Version details with
    Grade, Section and SubSection from Blueprint Items.

    GET /api/assessment-builder-list/
    """

    def get(self, request):

        version_qs = (
            AssessmentVersion.objects
            .select_related(
                "assessment",
            )
            .prefetch_related(
                "blueprint_items__grade",
                "blueprint_items__section",
                "blueprint_items__subsection",
            )
            .order_by(
                # "-effective_from",
                # "version_number",
                "-created_at"
            )
        )

        paginator = DefaultPagination()

        page = paginator.paginate_queryset(
            version_qs,
            request
        )

        serializer = AssessmentBlueprintListSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "Assessment blueprint fetched successfully.",
                "data": serializer.data,
            }
        )
        
class AssessmentVersionBlueprintAPIView(APIView):
    """
    Fetch Section and SubSection from
    AssessmentBlueprintItem using AssessmentVersion ID.

    GET /api/assessment-builder/versions/<version_id>/
    """

    def get(self, request, version_id):

        version = (
            AssessmentVersion.objects
            .select_related("assessment")
            .prefetch_related(
                "blueprint_items__section",
                "blueprint_items__subsection",
            )
            .filter(id=version_id)
            .first()
        )

        if not version:
            return Response(
                {
                    "success": False,
                    "message": "Assessment version not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssessmentVersionBlueprintSerializer(
            version
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Assessment version blueprint "
                    "fetched successfully."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )
        
                    
class AssessmentVersionGradesAPIView(APIView):
    """
    Get grades available in an Assessment Version Blueprint.

    GET /api/assessment-builder/versions/<version_id>/grades/
    """

    def get(self, request, version_id):

        try:

            # ==================================================
            # STEP 1: CHECK ASSESSMENT VERSION
            # ==================================================

            version = (
                AssessmentVersion.objects
                .filter(id=version_id)
                .first()
            )

            if not version:

                return Response(
                    {
                        "success": False,
                        "message": "Assessment version not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # ==================================================
            # STEP 2: FETCH GRADES FROM BLUEPRINT
            # ==================================================

            grades = (
                AssessmentBlueprintItem.objects
                .filter(
                    assessment_version_id=version_id,
                    status__in=[
                        AssessmentBlueprintItem.Status.ACTIVE,
                        AssessmentBlueprintItem.Status.DRAFT,
                    ],
                    grade__isnull=False,
                )
                .values(
                    "grade_id",
                    "grade__grade_name",
                )
                .distinct()
                .order_by(
                    "grade_id"
                )
            )

            # ==================================================
            # STEP 3: FORMAT RESPONSE
            # ==================================================

            grade_data = [
                {
                    "grade_id": item["grade_id"],
                    "grade_name": item["grade__grade_name"],
                }
                for item in grades
            ]

            # ==================================================
            # STEP 4: RESPONSE
            # ==================================================

            return Response(
                {
                    "success": True,
                    "message": (
                        "Grades fetched successfully."
                    ),
                    "data": {
                        "assessment_version": {
                            "id": version.id,
                            "version_number": version.version_number,
                        },
                        "grades": grade_data,
                        "total_grades": len(grade_data),
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Something went wrong while "
                        "fetching grades."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
         
         
class QuestionsByGradeTagAPIView(APIView):
    """
    Fetch questions by multiple Grade IDs and Tag IDs.

    GET:
    /api/questions/grades/25,29/tags/3,4,5/
    """

    def get(self, request, grade_ids, tag_ids):

        # ---------------------------------------------
        # Convert URL values to integer lists
        # ---------------------------------------------

        try:
            grade_id_list = [
                int(value)
                for value in grade_ids.split(",")
                if value.strip()
            ]

            tag_id_list = [
                int(value)
                for value in tag_ids.split(",")
                if value.strip()
            ]

        except ValueError:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Grade IDs and Tag IDs must "
                        "contain only integers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------
        # Validate IDs
        # ---------------------------------------------

        if not grade_id_list:

            return Response(
                {
                    "success": False,
                    "message": "At least one grade_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not tag_id_list:

            return Response(
                {
                    "success": False,
                    "message": "At least one tag_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------
        # Fetch mappings
        # ---------------------------------------------

        mappings = (
            QuestionGradeMapping.objects
            .filter(
                grade_id__in=grade_id_list,
                tag_id__in=tag_id_list,
                question__is_active=True,
            )
            .select_related("question")
            .order_by("question__question_code")
        )

        # ---------------------------------------------
        # Remove duplicate questions
        # Same Question + Same Grade + Same Tag
        # = duplicate
        #
        # Same Question + Different Grade/Tag
        # = keep
        # ---------------------------------------------

        question_objects = []
        seen_combinations = set()

        for mapping in mappings:

            question = mapping.question

            combination = (
                question.id,
                mapping.grade_id,
                mapping.tag_id
            )

            if combination not in seen_combinations:

                seen_combinations.add(combination)
                question_objects.append(question)

        # ---------------------------------------------
        # Serialize
        # ---------------------------------------------

        serializer = QuestionListSerializer(
            question_objects,
            many=True
        )

        # ---------------------------------------------
        # Response
        # ---------------------------------------------

        return Response(
            {
                "success": True,
                "message": "Questions fetched successfully.",
                "data": {
                    "grade_ids": grade_id_list,
                    "tag_ids": tag_id_list,
                    "total_questions": len(question_objects),
                    "questions": serializer.data,
                }
            },
            status=status.HTTP_200_OK
        )     
                  
# =========================== Question APIView ===================================

class GenerateQuestionCodeAPIView(APIView):
    """
    Generate Question Code based on Tag.

    Example:
    GET /api/question/generate-code/5/
    """

    def get(self, request, tag_id):

        # -----------------------------------------
        # Get Tag
        # -----------------------------------------

        try:
            tag = Tags.objects.get(id=tag_id)

        except Tags.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Tag not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------------------
        # Generate Prefix from Tag Name
        # -----------------------------------------

        words = tag.tag_name.strip().split()

        if len(words) == 1:
            prefix = words[0][:2].upper()
        else:
            prefix = "".join(
                word[0].upper()
                for word in words
            )

        # -----------------------------------------
        # Get Last Question Code
        # -----------------------------------------

        last_question = (
            Question.objects.filter(
                question_code__startswith=f"{prefix}-"
            )
            .order_by("-question_code")
            .first()
        )

        # -----------------------------------------
        # Generate Next Number
        # -----------------------------------------

        if last_question:

            match = re.search(
                r"(\d+)$",
                last_question.question_code
            )

            if match:
                last_number = int(match.group(1))
            else:
                last_number = 0

        else:
            last_number = 0

        question_code = (
            f"{prefix}-{last_number + 1:04d}"
        )

        # -----------------------------------------
        # Response
        # -----------------------------------------

        return Response(
            {
                "success": True,
                "tag_id": tag.id,
                "tag_name": tag.tag_name,
                "question_code": question_code,
            },
            status=status.HTTP_200_OK
        )
        
        
class QuestionAPIView(APIView):

    """
    POST  -> Create Question
    GET   -> List / Detail (Next)
    PUT   -> Update (Next)
    DELETE-> Archive (Next)
    """

    pagination_class = DefaultPagination

    def get_queryset(self):

        return (
            Question.objects
            .select_related(
                "created_by",
            )
            .prefetch_related(
                Prefetch(
                    "options",
                    queryset=QuestionOption.objects.order_by(
                        "display_order"
                    ),
                ),
                Prefetch(
                    "grade_mappings",
                    queryset=QuestionGradeMapping.objects.select_related(
                        "grade",
                        "tag",
                    ),
                ),
            )
            .order_by(
                "-created_at"
            )
        )
    
    @transaction.atomic
    def post(self, request):

        serializer = QuestionCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        grade_ids = validated_data.pop("grade_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        options = validated_data.pop("options", [])
        is_draft = validated_data.pop("is_draft", True)

        try:

            # -------------------------------
            # Create Question
            # -------------------------------

            question = Question.objects.create(
                **validated_data,
                # created_by=request.user,
                question_status=(
                    Question.QuestionStatus.DRAFT
                    if is_draft
                    else Question.QuestionStatus.PUBLISHED
                ),
            )

            # -------------------------------
            # Bulk Create Options
            # -------------------------------

            if options:
                QuestionOption.objects.bulk_create(
                    [
                        QuestionOption(
                            question=question,
                            **option,
                        )
                        for option in options
                    ]
                )

            # -------------------------------
            # Bulk Create Grade + Tag Mapping
            # -------------------------------

            if grade_ids:

                mappings = []

                for grade_id in grade_ids:

                    # If tags are provided, create one mapping
                    # for each grade + tag combination.
                    if tag_ids:

                        for tag_id in tag_ids:

                            mappings.append(
                                QuestionGradeMapping(
                                    question=question,
                                    grade_id=grade_id,
                                    tag_id=tag_id,
                                )
                            )

                    else:

                        # Preserve existing behavior when no tags
                        # are provided.
                        mappings.append(
                            QuestionGradeMapping(
                                question=question,
                                grade_id=grade_id,
                                tag=None,
                            )
                        )

                QuestionGradeMapping.objects.bulk_create(
                    mappings,
                    ignore_conflicts=True,
                )

            return Response(
                {
                    "success": True,
                    "message": "Question created successfully.",
                    "data": {
                        "id": question.id,
                        "public_id": question.public_id,
                        "question_code": question.question_code,
                        "status": question.question_status,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:

            transaction.set_rollback(True)

            return Response(
                {
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
    
    @transaction.atomic
    def put(self, request, id):

        try:
            # -----------------------------------------
            # Get question
            # -----------------------------------------
            question = (
                Question.objects
                .select_for_update()
                .filter(id=id)
                .first()
            )

            if not question:
                return Response(
                    {
                        "success": False,
                        "message": "Question not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # =================================================
            # STORE OLD GRADE + TAG MAPPINGS
            # =================================================

            old_mappings = set(
                QuestionGradeMapping.objects
                .filter(question=question)
                .values_list(
                    "grade_id",
                    "tag_id",
                )
            )

            # =================================================
            # VALIDATE REQUEST
            # =================================================

            serializer = QuestionCreateUpdateSerializer(
                question,
                data=request.data,
                context={"request": request},
            )

            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            validated_data = serializer.validated_data

            # =================================================
            # CHECK WHICH FIELDS WERE PROVIDED
            # =================================================

            grades_provided = "grade_ids" in validated_data
            tags_provided = "tag_ids" in validated_data
            options_provided = "options" in validated_data

            # =================================================
            # GET SPECIAL FIELDS
            # =================================================

            options = validated_data.pop(
                "options",
                []
            )

            grade_ids = validated_data.pop(
                "grade_ids",
                []
            )

            tag_ids = validated_data.pop(
                "tag_ids",
                []
            )

            is_draft = validated_data.pop(
                "is_draft",
                True
            )

            # =================================================
            # CHECK GRADE + TAG CHANGES
            # =================================================

            mapping_changed = False

            # Only check mapping changes when Grade or Tag
            # was actually provided in the request.

            if grades_provided or tags_provided:

                # -----------------------------------------
                # If only tags are sent, use existing grades
                # -----------------------------------------

                if not grades_provided:

                    grade_ids = list(
                        QuestionGradeMapping.objects
                        .filter(question=question)
                        .values_list(
                            "grade_id",
                            flat=True
                        )
                        .distinct()
                    )

                # -----------------------------------------
                # If only grades are sent, use existing tags
                # -----------------------------------------

                if not tags_provided:

                    existing_tags = list(
                        QuestionGradeMapping.objects
                        .filter(question=question)
                        .values_list(
                            "tag_id",
                            flat=True
                        )
                        .distinct()
                    )

                    # Remove None if present
                    tag_ids = [
                        tag_id
                        for tag_id in existing_tags
                        if tag_id is not None
                    ]

                # -----------------------------------------
                # Build new Grade + Tag combinations
                # -----------------------------------------

                new_mappings_set = set()

                for grade_id in grade_ids:

                    if tag_ids:

                        for tag_id in tag_ids:

                            new_mappings_set.add(
                                (
                                    grade_id,
                                    tag_id,
                                )
                            )

                    else:

                        new_mappings_set.add(
                            (
                                grade_id,
                                None,
                            )
                        )

                # -----------------------------------------
                # Compare old and new mappings
                # -----------------------------------------

                mapping_changed = (
                    old_mappings != new_mappings_set
                )

            # =================================================
            # UPDATE QUESTION STATUS
            # =================================================

            validated_data["question_status"] = (
                Question.QuestionStatus.DRAFT
                if is_draft
                else Question.QuestionStatus.PUBLISHED
            )

            # =================================================
            # UPDATE QUESTION
            # =================================================

            for field, value in validated_data.items():

                setattr(
                    question,
                    field,
                    value,
                )

            question.save()

            # =================================================
            # UPDATE GRADE + TAG MAPPING
            # ONLY WHEN ACTUALLY CHANGED
            # =================================================

            if mapping_changed:

                # -----------------------------------------
                # Delete old mappings
                # -----------------------------------------

                QuestionGradeMapping.objects.filter(
                    question=question
                ).delete()

                # -----------------------------------------
                # Create new mappings
                # -----------------------------------------

                new_mappings = []

                for grade_id in grade_ids:

                    # -----------------------------------------
                    # Tags provided
                    # -----------------------------------------

                    if tag_ids:

                        for tag_id in tag_ids:

                            new_mappings.append(
                                QuestionGradeMapping(
                                    question=question,
                                    grade_id=grade_id,
                                    tag_id=tag_id,
                                )
                            )

                    # -----------------------------------------
                    # No tags
                    # -----------------------------------------

                    else:

                        new_mappings.append(
                            QuestionGradeMapping(
                                question=question,
                                grade_id=grade_id,
                                tag=None,
                            )
                        )

                # -----------------------------------------
                # Bulk create
                # -----------------------------------------

                if new_mappings:

                    QuestionGradeMapping.objects.bulk_create(
                        new_mappings
                    )

            # =================================================
            # UPDATE OPTIONS
            # ONLY WHEN OPTIONS ARE PROVIDED
            # =================================================

            if options_provided and options:

                # -----------------------------------------
                # Get existing options
                # -----------------------------------------

                existing_options = {
                    option.id: option
                    for option in QuestionOption.objects.filter(
                        question=question
                    )
                }

                existing_options_by_code = {
                    option.option_code: option
                    for option in existing_options.values()
                }

                received_option_ids = set()
                new_options = []

                # -----------------------------------------
                # Process received options
                # -----------------------------------------

                for option_data in options:

                    option_data = option_data.copy()

                    option_id = option_data.pop(
                        "id",
                        None
                    )

                    option_code = option_data.get(
                        "option_code"
                    )

                    # =====================================
                    # EXISTING OPTION BY ID
                    # =====================================

                    if option_id:

                        option_obj = existing_options.get(
                            option_id
                        )

                        if not option_obj:

                            raise serializers.ValidationError(
                                {
                                    "options": [
                                        f"Option ID {option_id} "
                                        f"does not belong to this question."
                                    ]
                                }
                            )

                        received_option_ids.add(
                            option_obj.id
                        )

                        for field, value in option_data.items():

                            setattr(
                                option_obj,
                                field,
                                value
                            )

                        option_obj.save()

                    # =====================================
                    # EXISTING OPTION BY OPTION CODE
                    # =====================================

                    elif (
                        option_code
                        and option_code in existing_options_by_code
                    ):

                        option_obj = existing_options_by_code[
                            option_code
                        ]

                        received_option_ids.add(
                            option_obj.id
                        )

                        for field, value in option_data.items():

                            setattr(
                                option_obj,
                                field,
                                value
                            )

                        option_obj.save()

                    # =====================================
                    # NEW OPTION
                    # =====================================

                    else:

                        new_options.append(
                            QuestionOption(
                                question=question,
                                **option_data
                            )
                        )

                # -----------------------------------------
                # Create new options
                # -----------------------------------------

                if new_options:

                    QuestionOption.objects.bulk_create(
                        new_options
                    )

                    received_option_ids.update(
                        option.id
                        for option in new_options
                        if option.id
                    )

                # -----------------------------------------
                # Delete options not present in request
                # -----------------------------------------

                QuestionOption.objects.filter(
                    question=question
                ).exclude(
                    id__in=received_option_ids
                ).delete()

            # =================================================
            # RESPONSE
            # =================================================

            return Response(
                {
                    "success": True,
                    "message": "Question updated successfully.",
                    "data": {
                        "id": question.id,
                        "public_id": question.public_id,
                        "question_code": question.question_code,
                        "status": question.question_status,
                        "mapping_updated": mapping_changed,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # =================================================
        # VALIDATION ERROR
        # =================================================

        except serializers.ValidationError as e:

            return Response(
                {
                    "success": False,
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # OTHER ERROR
        # =================================================

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


            
    def get(self, request, id=None):

        queryset = self.get_queryset()

        # ----------------------------
        # Detail
        # ----------------------------

        if id:

            question = queryset.filter(
                id=id
            ).first()

            if not question:
                return Response(
                    {
                        "success": False,
                        "message": "Question not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = QuestionRetrieveSerializer(question)

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                }
            )

        # ----------------------------
        # Filters
        # ----------------------------

        question_status = request.query_params.get("question_status")

        grade_id = request.query_params.get("grade_id")

        subsection = request.query_params.get("subsection")

        question_type = request.query_params.get("question_type")

        difficulty_level = request.query_params.get(
            "difficulty_level"
        )

        search = request.query_params.get("search")

        if question_status:
            queryset = queryset.filter(
                question_status=question_status
            )

        if subsection:
            queryset = queryset.filter(
                subsection_id=subsection
            )

        if question_type:
            queryset = queryset.filter(
                question_type=question_type
            )

        if difficulty_level:
            queryset = queryset.filter(
                difficulty_level=difficulty_level
            )

        if grade_id:
            queryset = queryset.filter(
                grade_mappings__grade_id=grade_id
            )

        if search:
            queryset = queryset.filter(
                Q(question_code__icontains=search)
                |
                Q(question_text__icontains=search)
            )

        queryset = queryset.distinct()

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = QuestionRetrieveSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "Question list fetched successfully.",
                "data": serializer.data,
            }
        )
 

class QuestionLibraryAPIView(APIView):
    """
        GET /api/questions/library/?tag_id=5
        GET /api/questions/library/?grade_id=9&tag_id=5
        GET /api/questions/library/?search=Q-0001&grade_id=9&tag_id=5
    """
    
    pagination_class = DefaultPagination

    def get_queryset(self):

        return (
            Question.objects
            .prefetch_related(
                Prefetch(
                    "grade_mappings",
                    queryset=QuestionGradeMapping.objects
                    .select_related(
                        "grade",
                        "tag",
                    )
                    .only(
                        "id",
                        "question_id",
                        "grade_id",
                        "grade__id",
                        "grade__grade_name",
                        "tag_id",
                        "tag__id",
                        "tag__tag_name",
                    ),
                )
            )
            .only(
                "id",
                "question_code",
                "question_text",
                "question_type",
                "difficulty_level",
                "question_status",
                "updated_at",
            )
            .order_by("-updated_at")
        )

    def get(self, request):

        queryset = self.get_queryset()

        # -----------------------------------------
        # Filters
        # -----------------------------------------

        search = request.query_params.get("search")

        question_status = request.query_params.get(
            "question_status"
        )

        grade_id = request.query_params.get(
            "grade_id"
        )

        tag_id = request.query_params.get(
            "tag_id"
        )

        question_type = request.query_params.get(
            "question_type"
        )

        difficulty_level = request.query_params.get(
            "difficulty_level"
        )

        # -----------------------------------------
        # Search
        # -----------------------------------------

        if search:

            queryset = queryset.filter(
                Q(question_code__icontains=search)
                |
                Q(question_text__icontains=search)
            )

        # -----------------------------------------
        # Question Status
        # -----------------------------------------

        if question_status:

            queryset = queryset.filter(
                question_status=question_status
            )

        # -----------------------------------------
        # Grade
        # -----------------------------------------

        if grade_id:

            queryset = queryset.filter(
                grade_mappings__grade_id=grade_id
            )

        # -----------------------------------------
        # Tag
        # -----------------------------------------

        if tag_id:

            queryset = queryset.filter(
                grade_mappings__tag_id=tag_id
            )

        # -----------------------------------------
        # Question Type
        # -----------------------------------------

        if question_type:

            queryset = queryset.filter(
                question_type=question_type
            )

        # -----------------------------------------
        # Difficulty
        # -----------------------------------------

        if difficulty_level:

            queryset = queryset.filter(
                difficulty_level=difficulty_level
            )

        # -----------------------------------------
        # Remove duplicates
        # -----------------------------------------

        queryset = queryset.distinct()

        # -----------------------------------------
        # Pagination
        # -----------------------------------------

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        # -----------------------------------------
        # Serializer
        # -----------------------------------------

        serializer = QuestionLibrarySerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "Question library fetched successfully.",
                "data": serializer.data,
            }
        )       
        