import random

from django.db import transaction
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from accounts.serializers import SendStudentEmailOTPSerializer, StudentForgotPasswordSerializer, StudentLoginSerializer, StudentResetPasswordSerializer, VerifyPasswordResetOTPSerializer, VerifyStudentEmailOTPSerializer
from accounts.models import EmailVerificationOTP, User
from accounts.utils import create_and_send_password_reset_otp, send_email_verification_otp

class SendStudentEmailOTPAPIView(APIView):

    def post(self, request):

        serializer = SendStudentEmailOTPSerializer(
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

            result = serializer.save()

            if result["already_verified"]:

                return Response(
                    {
                        "success": True,
                        "message": (
                            "Email is already verified. Please use another email."
                        )
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    "success": True,
                    "message": (
                        "OTP has been sent successfully "
                        "to your email."
                    )
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to send verification OTP."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class VerifyStudentEmailOTPAPIView(APIView):

    def post(self, request):

        serializer = VerifyStudentEmailOTPSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "OTP verification failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            user = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": (
                        "Email verified successfully. "
                        "You can now complete student registration."
                    ),
                    "data": {
                        "user_id": user.id,
                        "email": user.email,
                        "is_email_verified":
                            user.is_email_verified
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
                        "while verifying the email."
                    ),
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class StudentLoginAPIView(APIView):

    def post(self, request):

        # ==================================================
        # SERIALIZER
        # ==================================================

        serializer = StudentLoginSerializer(
            data=request.data,
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
                    "message": "Login failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            # ==================================================
            # GET DATA
            # ==================================================

            user = serializer.validated_data["user"]

            student = serializer.validated_data[
                "student"
            ]

            role = serializer.validated_data[
                "role"
            ]

            access_token = serializer.validated_data[
                "access_token"
            ]

            refresh_token = serializer.validated_data[
                "refresh_token"
            ]

            # ==================================================
            # RESPONSE
            # ==================================================

            data = {

                # ==================================================
                # AUTH
                # ==================================================

                "access_token": access_token,

                "refresh_token": refresh_token,

                # ==================================================
                # USER
                # ==================================================

                "user": {

                    "id": user.id,

                    "public_id": str(
                        user.public_id
                    ),

                    "email": user.email,

                    "mobile": user.mobile,

                    "first_name": user.first_name,

                    "last_name": user.last_name,

                    "is_email_verified":
                        user.is_email_verified
                },

                # ==================================================
                # STUDENT
                # ==================================================

                "student": {

                    "id": student.id,

                    "public_id": str(
                        student.public_id
                    ),

                    "student_code":
                        student.student_code,

                    "first_name":
                        student.first_name,

                    "last_name":
                        student.last_name,

                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name or ''}"
                    ).strip()
                },

                # ==================================================
                # ROLE
                # ==================================================

                "role": {

                    "id": role.id,

                    "name": role.name
                }
            }

            return Response(
                {
                    "success": True,

                    "message": (
                        "Student login successful."
                    ),

                    "data": data
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,

                    "message": (
                        "An unexpected error occurred "
                        "during student login."
                    ),

                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
class StudentForgotPasswordAPIView(APIView):

    def post(self, request):

        serializer = (
            StudentForgotPasswordSerializer(
                data=request.data
            )
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

            user = serializer.validated_data[
                "user"
            ]

            # ==================================================
            # CREATE + SEND OTP
            # ==================================================

            password_reset_otp = (
                create_and_send_password_reset_otp(
                    user=user
                )
            )

            return Response(
                {
                    "success": True,

                    "message": (
                        "Password reset OTP has been "
                        "sent successfully to your email."
                    ),

                    "data": {

                        "email": user.email,

                        "expires_in": 600
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,

                    "message": (
                        "Unable to send password "
                        "reset OTP."
                    ),

                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
class VerifyPasswordResetOTPAPIView(APIView):

    def post(self, request):

        serializer = (
            VerifyPasswordResetOTPSerializer(
                data=request.data
            )
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "OTP verification failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        password_reset_otp = (
            serializer.validated_data[
                "password_reset_otp"
            ]
        )

        return Response(
            {
                "success": True,

                "message": (
                    "OTP verified successfully. "
                    "You can now reset your password."
                ),

                "data": {

                    "reset_token": str(
                        password_reset_otp.public_id
                    ),

                    "email": (
                        serializer.validated_data[
                            "user"
                        ].email
                    )
                }
            },
            status=status.HTTP_200_OK
        )

class StudentResetPasswordAPIView(APIView):

    def post(self, request):

        # ==================================================
        # SERIALIZER
        # ==================================================

        serializer = (
            StudentResetPasswordSerializer(
                data=request.data
            )
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

            user = serializer.validated_data[
                "_user"
            ]

            password = serializer.validated_data[
                "password"
            ]

            password_reset_otp = (
                serializer.validated_data[
                    "_password_reset_otp"
                ]
            )

            # ==================================================
            # DATABASE TRANSACTION
            # ==================================================

            with transaction.atomic():

                # ==================================================
                # UPDATE PASSWORD
                # ==================================================

                user.set_password(
                    password
                )

                user.save(
                    update_fields=[
                        "password"
                    ]
                )

                # ==================================================
                # MARK OTP AS USED
                # ==================================================

                password_reset_otp.is_used = True

                password_reset_otp.save(
                    update_fields=[
                        "is_used",
                        "updated_at"
                    ]
                )

            # ==================================================
            # RESPONSE
            # ==================================================

            return Response(
                {
                    "success": True,

                    "message": (
                        "Password reset successfully. "
                        "You can now login with your new password."
                    )
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,

                    "message": (
                        "Unable to reset password."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
