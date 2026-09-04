import random


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