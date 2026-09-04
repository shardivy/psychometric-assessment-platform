from django.urls import path

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