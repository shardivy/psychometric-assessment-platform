from django.urls import path

from accounts.views import SendStudentEmailOTPAPIView, StudentForgotPasswordAPIView, StudentLoginAPIView, StudentResetPasswordAPIView, VerifyPasswordResetOTPAPIView, VerifyStudentEmailOTPAPIView

# from accounts.views import ChangePasswordAPIView, CurrentUserAPIView, ForgotPasswordAPIView, LoginAPIView, LogoutAPIView, RefreshTokenAPIView, RegisterAPIView, ResendOTPAPIView, ResetPasswordAPIView, VerifyOTPAPIView, VerifyResetOTPAPIView

# urlpatterns = [

#     # ==========================================
#     # Authentication
#     # ==========================================

#     path(
#         "register/",
#         RegisterAPIView.as_view(),
#         name="register",
#     ),
    
#     path(
#         "resend-otp/",
#         ResendOTPAPIView.as_view(),
#         name="resend-otp"
#     ),

#     path(
#         "verify-otp/",
#         VerifyOTPAPIView.as_view(),
#         name="verify_otp",
#     ),

#     path(
#         "login/",
#         LoginAPIView.as_view(),
#         name="login",
#     ),

#     path(
#         "refresh/",
#         RefreshTokenAPIView.as_view(),
#         name="refresh_token",
#     ),
    
#     path(
#         "verify-reset-otp/",
#         VerifyResetOTPAPIView.as_view(),
#         name="verify_reset_otp",
#     ),

#     path(
#         "logout/",
#         LogoutAPIView.as_view(),
#         name="logout",
#     ),

#     # ==========================================
#     # Password Management
#     # ==========================================

#     path(
#         "forgot-password/",
#         ForgotPasswordAPIView.as_view(),
#         name="forgot_password",
#     ),

#     path(
#         "reset-password/",
#         ResetPasswordAPIView.as_view(),
#         name="reset_password",
#     ),

#     path(
#         "change-password/",
#         ChangePasswordAPIView.as_view(),
#         name="change_password",
#     ),

#     # ==========================================
#     # Current User
#     # ==========================================

#     path(
#         "me/",
#         CurrentUserAPIView.as_view(),
#         name="current_user",
#     ),
# ]

urlpatterns = [

    path(
        "student/send-email-otp/",
        SendStudentEmailOTPAPIView.as_view(),
        name="student-send-email-otp"
    ),
    path(
        "student/verify-email-otp/",
        VerifyStudentEmailOTPAPIView.as_view(),
        name="student-verify-email-otp"
    ),
    path(
        "students/login/",
        StudentLoginAPIView.as_view(),
        name="student-login"
    ),
    path(
        "students/forgot-password/",
        StudentForgotPasswordAPIView.as_view(),
        name="student-forgot-password"
    ),
    path(
        "students/verify-password-otp/",
        VerifyPasswordResetOTPAPIView.as_view(),
        name="student-verify-password"
    ),
     path(
        "students/reset-password/",
        StudentResetPasswordAPIView.as_view(),
        name="student-reset-password"
    ),

]