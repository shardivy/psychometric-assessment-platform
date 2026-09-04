from django.contrib import admin

from organizations.models import Campaign, Organization, RegistrationChannel, RegistrationLink

# ==========================================================
# Organization Admin
# ==========================================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization_code",
        "name",
        "organization_type",
        "city",
        "state",
        "phone",
        "email",
        "status",
        "created_at",
    )

    list_filter = (
        "organization_type",
        "status",
        "country",
        "state",
    )

    search_fields = (
        "organization_code",
        "name",
        "short_name",
        "email",
        "phone",
        "city",
        "state",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        (
            "Organization Information",
            {
                "fields": (
                    "public_id",
                    "organization_code",
                    "organization_type",
                    "name",
                    "short_name",
                )
            },
        ),
        (
            "Contact Details",
            {
                "fields": (
                    "email",
                    "phone",
                    "website",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address",
                    "city",
                    "state",
                    "country",
                    "pincode",
                )
            },
        ),
        (
            "Other Information",
            {
                "fields": (
                    "logo_url",
                    "timezone",
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Campaign Admin
# ==========================================================

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "campaign_code",
        "name",
        "organization",
        "assessment",
        "start_date",
        "end_date",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "organization",
        "assessment",
    )

    search_fields = (
        "campaign_code",
        "name",
        "organization__name",
    )

    autocomplete_fields = (
        "organization",
        "assessment",
        "created_by",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "Campaign",
            {
                "fields": (
                    "public_id",
                    "campaign_code",
                    "name",
                    "description",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": (
                    "organization",
                    "assessment",
                    "max_attempts",
                )
            },
        ),
        (
            "Duration",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "created_by",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Registration Channel Admin
# ==========================================================

@admin.register(RegistrationChannel)
class RegistrationChannelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "channel_code",
        "channel_name",
        "campaign",
        "channel_type",
        "display_order",
        "status",
    )

    list_filter = (
        "channel_type",
        "status",
        "campaign",
    )

    search_fields = (
        "channel_code",
        "channel_name",
        "campaign__name",
    )

    autocomplete_fields = (
        "campaign",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "display_order",
        "channel_name",
    )

    fieldsets = (
        (
            "Channel",
            {
                "fields": (
                    "public_id",
                    "campaign",
                    "channel_code",
                    "channel_name",
                    "channel_type",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "display_order",
                    "status",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ==========================================================
# Registration Link Admin
# ==========================================================

@admin.register(RegistrationLink)
class RegistrationLinkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "link_code",
        "display_name",
        "campaign",
        "registration_channel",
        "registration_source",
        "registrations_count",
        "max_registrations",
        "is_active",
        "expires_at",
    )

    list_filter = (
        "registration_channel",
        "registration_source",
        "is_active",
        "campaign",
    )

    search_fields = (
        "link_code",
        "display_name",
        "campaign__name",
    )

    autocomplete_fields = (
        "campaign",
        "assessment_version",
        "created_by",
    )

    readonly_fields = (
        "public_id",
        "registrations_count",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "Registration Link",
            {
                "fields": (
                    "public_id",
                    "campaign",
                    "link_code",
                    "display_name",
                )
            },
        ),
        (
            "Registration Settings",
            {
                "fields": (
                    "registration_channel",
                    "registration_source",
                    "assessment_version",
                )
            },
        ),
        (
            "Limits",
            {
                "fields": (
                    "max_registrations",
                    "registrations_count",
                    "expires_at",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "allow_duplicate_email",
                    "allow_duplicate_mobile",
                    "is_active",
                )
            },
        ),
        (
            "Created By",
            {
                "fields": (
                    "created_by",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )