from datetime import timedelta
import random

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import PasswordResetOTP


def generate_otp():

    return str(
        random.randint(
            100000,
            999999
        )
    )


def get_client_ip(request):

    forwarded = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded:
        return forwarded.split(",")[0]

    return request.META.get("REMOTE_ADDR")


def get_device(request):

    return request.META.get(
        "HTTP_USER_AGENT",
        ""
    )
    
def send_email_verification_otp(
    email,
    otp
):

    subject = "Verify Your Email"

    message = f"""
Hello,

Your email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request this verification, please ignore this email.

Regards,
The Career Sutra
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False
    )
    
def send_password_reset_otp_email(
    user,
    otp
):

    subject = "Password Reset OTP"

    message = f"""
Hello {user.first_name or 'Student'},

We received a request to reset your password.

Your password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset, please ignore this email.

Regards,
The Career Sutra
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[
            user.email
        ],
        fail_silently=False
    )


def create_and_send_password_reset_otp(
    user
):

    # ==================================================
    # GENERATE OTP
    # ==================================================

    otp = generate_otp()

    # ==================================================
    # EXPIRY
    # ==================================================

    expires_at = (
        timezone.now()
        + timedelta(minutes=10)
    )

    # ==================================================
    # INVALIDATE OLD OTPs
    # ==================================================

    PasswordResetOTP.objects.filter(
        user=user,
        is_used=False
    ).update(
        is_used=True
    )

    # ==================================================
    # CREATE OTP
    # ==================================================

    password_reset_otp = (
        PasswordResetOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at
        )
    )

    # ==================================================
    # SEND EMAIL
    # ==================================================

    send_password_reset_otp_email(
        user=user,
        otp=otp
    )

    return password_reset_otp