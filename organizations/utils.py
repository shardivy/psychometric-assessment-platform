from django.utils import timezone

from organizations.models import Organization


def generate_organization_code():
    """
    Generate a unique organization code.

    Format:
    ORG-YYYY-000001
    """

    year = timezone.now().year

    prefix = f"ORG-{year}-"

    last_code = (
        Organization.objects
        .filter(organization_code__startswith=prefix)
        .order_by("-id")
        .values_list("organization_code", flat=True)
        .first()
    )

    if last_code:
        try:
            last_number = int(last_code.split("-")[-1])
        except (ValueError, IndexError):
            last_number = 0
    else:
        last_number = 0

    return f"{prefix}{last_number + 1:06d}"