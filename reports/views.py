from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from assessments.pagination import DefaultPagination
from reports.models import ReportTemplate
from reports.serializers import ReportTemplateListSerializer, ReportTemplateSerializer

class ReportTemplateAPIView(APIView):

    # permission_classes = [IsAuthenticated]

    pagination_class = DefaultPagination

    # -------------------------------------------------------
    # POST
    # Create Report Template
    # -------------------------------------------------------
    def post(self, request):

        serializer = ReportTemplateSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            # Only one default template per report type
            if serializer.validated_data.get("is_default"):

                ReportTemplate.objects.filter(
                    report_type=serializer.validated_data["report_type"],
                    is_default=True
                ).update(is_default=False)

            serializer.save(
                # created_by=request.user,
                status=ReportTemplate.Status.ACTIVE
            )

            return Response(
                {
                    "success": True,
                    "message": "Report template created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError:

            return Response(
                {
                    "success": False,
                    "message": "Template code already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "message": "Something went wrong.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
    # -------------------------------------------------------
    # GET
    # List Report Templates / Single Report Template
    # -------------------------------------------------------
    def get(self, request, id=None):

        # ---------------------------------------------------
        # Single Report Template
        # ---------------------------------------------------
        if id:

            try:

                report_template = (
                    ReportTemplate.objects
                    .select_related("created_by")
                    .get(id=id)
                )

            except ReportTemplate.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Report template not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ReportTemplateSerializer(
                report_template
            )

            return Response(
                {
                    "success": True,
                    "message": "Report template fetched successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # ---------------------------------------------------
        # List Report Templates
        # ---------------------------------------------------

        report_templates = (
            ReportTemplate.objects
            .select_related("created_by")
            .only(
                "id",
                "public_id",
                "template_code",
                "name",
                "report_type",
                "version",
                "language",
                "is_default",
                "status",
                "created_at",
                "created_by__id",
                "created_by__first_name",
                "created_by__last_name",
                "created_by__email",
            )
            .order_by("-created_at")
        )

        # ---------------------------------------------------
        # Filters
        # ---------------------------------------------------

        search = request.query_params.get("search")
        report_type = request.query_params.get("report_type")
        status_filter = request.query_params.get("status")
        language = request.query_params.get("language")
        is_default = request.query_params.get("is_default")

        if search:

            report_templates = report_templates.filter(
                Q(template_code__icontains=search) |
                Q(name__icontains=search) |
                Q(version__icontains=search)
            )

        if report_type:

            report_templates = report_templates.filter(
                report_type=report_type
            )

        if status_filter:

            report_templates = report_templates.filter(
                status=status_filter
            )

        if language:

            report_templates = report_templates.filter(
                language__iexact=language
            )

        if is_default:

            if is_default.lower() == "true":

                report_templates = report_templates.filter(
                    is_default=True
                )

            elif is_default.lower() == "false":

                report_templates = report_templates.filter(
                    is_default=False
                )

        # ---------------------------------------------------
        # Pagination
        # ---------------------------------------------------

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            report_templates,
            request
        )

        serializer = ReportTemplateListSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )
        
    # -------------------------------------------------------
    # PUT
    # Update Report Template
    # -------------------------------------------------------
    def put(self, request, id):

        try:

            report_template = ReportTemplate.objects.get(id=id)

        except ReportTemplate.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Report template not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReportTemplateSerializer(
            report_template,
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

            # Only one default template per report type
            if serializer.validated_data.get("is_default"):

                report_type = serializer.validated_data.get(
                    "report_type",
                    report_template.report_type
                )

                ReportTemplate.objects.filter(
                    report_type=report_type,
                    is_default=True
                ).exclude(
                    id=report_template.id
                ).update(
                    is_default=False
                )

            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Report template updated successfully.",
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
    # Archive Report Template
    # -------------------------------------------------------
    def delete(self, request, id):

        try:

            report_template = ReportTemplate.objects.get(id=id)

        except ReportTemplate.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Report template not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        report_template.status = ReportTemplate.Status.ARCHIVED
        report_template.save(update_fields=["status"])

        return Response(
            {
                "success": True,
                "message": "Report template archived successfully."
            },
            status=status.HTTP_200_OK
        )
