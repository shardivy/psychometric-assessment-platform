from collections import OrderedDict

from django.db import IntegrityError
from django.shortcuts import render

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from assessments.models import AssessmentBlueprintItem
from students.models import StudentRegistration
from students.serializers import StudentRegistrationSerializer

class StudentRegistrationAPIView(APIView):

    def post(self, request, registration_token=None):

        # ==================================================
        # COPY REQUEST DATA
        # ==================================================

        data = request.data.copy()

        # ==================================================
        # ORGANIZATION REGISTRATION
        # ==================================================
        # If token is present in URL, add it internally.
        #
        # Example:
        # /students/register/u9vabU386aHBZRsgGxxRjhwQaadrKCG9vqsqxGwYUxU/
        #
        # No registration_token is required in request body.
        # ==================================================

        if registration_token:

            data["registration_token"] = registration_token

        # ==================================================
        # SERIALIZER
        # ==================================================

        serializer = StudentRegistrationSerializer(
            data=data,
            context={
                "request": request
            }
        )

        # ==================================================
        # VALIDATION
        # ==================================================

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

            result = serializer.save()

            student = result["student"]
            registration = result["registration"]
            order = result["order"]
            access_token = result["access_token"]
            refresh_token = result["refresh_token"]

            # ==================================================
            # STUDENT RESPONSE
            # ==================================================

            data = {
                # ==================================================
                # AUTH TOKENS
                # ==================================================

                "access_token": access_token,

                "refresh_token": refresh_token,

                "student": {

                    "id": student.id,

                    "public_id": str(
                        student.public_id
                    ),

                    "student_code":
                        student.student_code,

                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name or ''}"
                    ).strip()
                },

                # ==================================================
                # REGISTRATION
                # ==================================================

                "registration": {

                    "id": registration.id,

                    "public_id": str(
                        registration.public_id
                    ),

                    "registration_number":
                        registration.registration_number,

                    "organization_id": (
                        registration.organization.id
                        if registration.organization
                        else None
                    ),

                    "registration_link": (
                        registration
                        .registration_link
                        .public_slug
                        if registration.registration_link
                        else None
                    ),

                    "registration_type":
                        registration.registration_type,

                    "registration_status":
                        registration.registration_status
                },

                # ==================================================
                # ORDER
                # ==================================================

                "order": None
            }

            # ==================================================
            # ORDER RESPONSE
            # ==================================================

            if order:

                data["order"] = {

                    "id": order.id,

                    "public_id": str(
                        order.public_id
                    ),

                    "order_number":
                        order.order_number,

                    "package_id":
                        order.package_id,

                    "quantity":
                        order.quantity,

                    "unit_price":
                        str(order.unit_price),

                    "total_amount":
                        str(order.total_amount),

                    "status":
                        order.status
                }

            # ==================================================
            # MESSAGE
            # ==================================================

            if (
                result["registration_source"]
                == "ORGANIZATION"
            ):

                message = (
                    "Student registered successfully "
                    "under the organization."
                )

            else:

                message = (
                    "Student registered successfully "
                    "and order created."
                )

            return Response(
                {
                    "success": True,
                    "message": message,
                    "data": data
                },
                status=status.HTTP_201_CREATED
            )

        # ======================================================
        # INTEGRITY ERROR
        # ======================================================

        except IntegrityError as exc:

            error_message = str(exc).lower()

            if "email" in error_message:

                return Response(
                    {
                        "success": False,
                        "message":
                            "This email is already registered.",
                        "errors": {
                            "email": [
                                "This email is already registered."
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if "mobile" in error_message:

                return Response(
                    {
                        "success": False,
                        "message":
                            "This mobile number is already registered.",
                        "errors": {
                            "mobile": [
                                "This mobile number is already registered."
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Student registration failed because "
                        "some information already exists."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # SERIALIZER VALIDATION ERROR
        # ======================================================

        except serializers.ValidationError as exc:

            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": exc.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ======================================================
        # OTHER ERROR
        # ======================================================

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "An unexpected error occurred "
                        "while registering the student."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )           

class StudentAssessmentQuestionsAPIView(APIView):
    """
    Get assessment questions for a student's registration.

    Flow:

    StudentRegistration
        ↓
    Organization
        ↓
    OrganizationPackage
        ↓
    Package
        ↓
    AssessmentVersion
        ↓
    AssessmentBlueprintItem
        ↓
    Grade
        ↓
    Section
        ↓
    SubSection
        ↓
    Question

    GET
    /api/v1/student/registrations/<registration_id>/assessment-questions/
    """

    def get(self, request, registration_id):

        # ==========================================================
        # STEP 1: GET REGISTRATION
        # ==========================================================

        try:
            registration = (
                StudentRegistration.objects
                .select_related(
                    "student",
                    "organization",
                    "grade",
                )
                .only(
                    "id",
                    "registration_number",
                    "student_id",
                    "organization_id",
                    "grade_id",

                    "student__id",

                    "organization__id",
                    "organization__name",

                    "grade__id",
                    "grade__grade_name",
                )
                .get(id=registration_id)
            )

        except StudentRegistration.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Student registration not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ==========================================================
        # STEP 2: VALIDATE ORGANIZATION
        # ==========================================================

        if not registration.organization_id:
            return Response(
                {
                    "success": False,
                    "message": "Organization is not assigned to this registration.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==========================================================
        # STEP 3: VALIDATE GRADE
        # ==========================================================

        if not registration.grade_id:
            return Response(
                {
                    "success": False,
                    "message": "Grade is not assigned to this registration.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        grade_id = registration.grade_id

        # ==========================================================
        # STEP 4:
        # FETCH ONLY ACTIVE ORGANIZATION PACKAGES
        # ==========================================================

        organization_packages = list(
            registration.organization.organization_packages
            .filter(
                status="ACTIVE",
                package__status="ACTIVE",
                package__assessment_version__isnull=False,
            )
            .select_related(
                "package",
                "package__assessment_version",
            )
            .only(
                "id",
                "package_id",

                "package__id",
                "package__package_name",
                "package__package_price",
                "package__assessment_version_id",

                "package__assessment_version__id",
                "package__assessment_version__version_number",
                "package__assessment_version__section_wise_randomize_question",
            )
        )

        # ==========================================================
        # STEP 5:
        # GET UNIQUE ASSESSMENT VERSION IDS
        # ==========================================================

        version_ids = list(
            {
                organization_package.package.assessment_version_id
                for organization_package in organization_packages
            }
        )

        if not version_ids:
            return Response(
                {
                    "success": True,
                    "message": "No active assessment package is assigned to this organization.",
                    "data": {
                        "registration_id": registration.id,
                        "registration_number": (
                            registration.registration_number
                        ),
                        "student": {
                            "id": registration.student_id,
                        },
                        "organization": {
                            "id": registration.organization_id,
                            "name": registration.organization.name,
                        },
                        "grade": {
                            "id": registration.grade_id,
                            "name": registration.grade.grade_name,
                        },
                        "assessments": [],
                    },
                },
                status=status.HTTP_200_OK,
            )

        # ==========================================================
        # STEP 6:
        # FETCH BLUEPRINT ITEMS
        #
        # IMPORTANT:
        # Only fetch questions for:
        #
        # - required assessment versions
        # - student's grade
        # - active blueprint items
        # - actual questions
        # ==========================================================

        blueprint_items = (
            AssessmentBlueprintItem.objects
            .filter(
                assessment_version_id__in=version_ids,
                grade_id=grade_id,
                question_id__isnull=False,
                status=AssessmentBlueprintItem.Status.ACTIVE,
            )
            .select_related(
                "assessment_version",
                "section",
                "subsection",
                "question",
            )
            .only(
                "id",
                "assessment_version_id",
                "section_id",
                "subsection_id",
                "question_id",
                "sequence_no",
                "marks_override",
                "negative_marks_override",

                "assessment_version__id",
                "assessment_version__version_number",
                "assessment_version__section_wise_randomize_question",

                "section__id",
                "section__name",

                "subsection__id",
                "subsection__name",

                "question__id",
                "question__question_code",
                "question__question_text",
            )
            .order_by(
                "assessment_version_id",
                "section_id",
                "subsection_id",
                "sequence_no",
                "id",
            )
        )

        # ==========================================================
        # STEP 7:
        # CREATE ASSESSMENT STRUCTURE
        # ==========================================================

        assessments = {}

        for item in blueprint_items:

            version_id = item.assessment_version_id

            # ------------------------------------------------------
            # CREATE ASSESSMENT
            # ------------------------------------------------------

            if version_id not in assessments:

                assessments[version_id] = {
                    "assessment_version_id": version_id,
                    "version_number": (
                        item.assessment_version.version_number
                    ),
                    "section_wise_randomize_question": (
                        item.assessment_version
                        .section_wise_randomize_question
                    ),
                    "packages": [],
                    "sections": {},
                }

            assessment = assessments[version_id]

            # ------------------------------------------------------
            # CREATE SECTION
            # ------------------------------------------------------

            section_id = item.section_id

            if section_id not in assessment["sections"]:

                assessment["sections"][section_id] = {
                    "section_id": section_id,
                    "section_name": (
                        item.section.name
                        if item.section
                        else None
                    ),
                    "subsections": {},
                }

            section = assessment["sections"][section_id]

            # ------------------------------------------------------
            # CREATE SUBSECTION
            # ------------------------------------------------------

            subsection_id = item.subsection_id

            if subsection_id not in section["subsections"]:

                section["subsections"][subsection_id] = {
                    "subsection_id": subsection_id,
                    "subsection_name": (
                        item.subsection.name
                        if item.subsection
                        else None
                    ),
                    "questions": [],
                }

            subsection = section["subsections"][subsection_id]

            # ------------------------------------------------------
            # QUESTION
            # ------------------------------------------------------

            question = item.question

            subsection["questions"].append(
                {
                    "blueprint_item_id": item.id,
                    "question_id": item.question_id,
                    "question_code": question.question_code,
                    "question_text": question.question_text,
                    "sequence_no": item.sequence_no,
                    "marks": item.marks_override,
                    "negative_marks": item.negative_marks_override,
                }
            )

        # ==========================================================
        # STEP 8:
        # ADD PACKAGE INFORMATION
        # ==========================================================

        for organization_package in organization_packages:

            package = organization_package.package

            version_id = package.assessment_version_id

            if version_id not in assessments:
                continue

            assessments[version_id]["packages"].append(
                {
                    "organization_package_id": (
                        organization_package.id
                    ),
                    "package_id": package.id,
                    "package_name": package.package_name,
                    "package_price": package.package_price,
                }
            )

        # ==========================================================
        # STEP 9:
        # CONVERT DICTIONARIES TO LISTS
        # ==========================================================

        assessment_list = []

        for assessment in assessments.values():

            section_list = []

            for section in assessment["sections"].values():

                subsection_list = list(
                    section["subsections"].values()
                )

                section["subsections"] = subsection_list

                section_list.append(section)

            assessment["sections"] = section_list

            assessment_list.append(assessment)

        # ==========================================================
        # STEP 10:
        # FINAL RESPONSE
        # ==========================================================

        return Response(
            {
                "success": True,
                "message": "Assessment questions fetched successfully.",
                "data": {
                    "registration_id": registration.id,

                    "registration_number": (
                        registration.registration_number
                    ),

                    "student": {
                        "id": registration.student_id,
                    },

                    "organization": {
                        "id": registration.organization_id,
                        "name": registration.organization.name,
                    },

                    "grade": {
                        "id": registration.grade_id,
                        "name": registration.grade.grade_name,
                    },

                    "assessments": assessment_list,
                },
            },
            status=status.HTTP_200_OK,
        )   
     
     
     
            
            