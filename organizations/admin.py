from django.contrib import admin

from organizations.models import Campaign, Organization, OrganizationMember, OrganizationPackage, Package, RegistrationChannel, RegistrationLink

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):

    # ==================================================
    # LIST DISPLAY
    # ==================================================

    list_display = (
        "id",
        "public_id",
        "package_name",
        "assessment_version",
        "grade",
        "package_price",
        "status",
        "created_at",
        "updated_at",
    )

    # ==================================================
    # SEARCH
    # ==================================================

    search_fields = (
        "package_name",
        "public_id",
        "assessment_version__version_number",
        "assessment_version__version_name",
    )

    # ==================================================
    # FILTERS
    # ==================================================

    list_filter = (
        "status",
        "assessment_version",
    )

    # ==================================================
    # DEFAULT ORDERING
    # ==================================================

    ordering = (
        "id",
    )

    # ==================================================
    # READ ONLY FIELDS
    # ==================================================

    readonly_fields = (
        "id",
        "public_id",
    )

    # ==================================================
    # FORM LAYOUT
    # ==================================================

    fieldsets = (

        (
            "Package Information",
            {
                "fields": (
                    "id",
                    "public_id",
                    "assessment_version",
                    "package_name",
                    "package_price",
                    "status",
                    "package_description",
                )
            },
        ),

        (
            "Package Features",
            {
                "fields": (
                    "package_features1",
                    "package_features2",
                    "package_features3",
                    "package_features4",
                    "package_features5",
                )
            },
        ),

        (
            "Package Deliverables",
            {
                "fields": (
                    "package_deliverable1",
                    "package_deliverable2",
                    "package_deliverable3",
                    "package_deliverable4",
                    "package_deliverable5",
                )
            },
        ),
    )

    # ==================================================
    # FOREIGN KEY DISPLAY
    # ==================================================

    autocomplete_fields = (
        "assessment_version",
    )

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
        "-created_at",
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
    
    
@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "public_id",
        "organization",
        "user",
        "member_type",
        "status",
        "joined_at",
        "invited_by",
        "created_at",
    )

    list_filter = (
        "member_type",
        "status",
        "organization",
    )

    search_fields = (
        "organization__name",
        "organization__organization_code",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "organization",
        "user",
        "invited_by",
    )

    ordering = (
        "-created_at",
    )

@admin.register(OrganizationPackage)
class OrganizationPackageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "public_id",
        "organization",
        "package",
        "negotiated_price",
        "currency",
        "seat_limit",
        "used_seats",
        "valid_from",
        "valid_until",
        "status",
        "assigned_by",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "organization",
        "package",
        "valid_from",
        "valid_until",
    )

    search_fields = (
        "organization__name",
        "organization__organization_code",
        "package__package_name",
        "contract_code",
        "notes",
        "assigned_by__email",
    )

    readonly_fields = (
        "public_id",
        "used_seats",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "organization",
        "package",
        "assigned_by",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25


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
        "public_id",
        "organization",
        "public_slug",
        "link_name",
        "status",
        "expires_at",
        "max_registrations",
        "registration_count",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "organization",
        "created_at",
    )

    search_fields = (
        "public_slug",
        "link_name",
        "organization__name",
        "organization__organization_code",
    )

    readonly_fields = (
        "public_id",
        "token_hash",
        "registration_count",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "organization",
        "created_by",
    )

    ordering = (
        "-created_at",
    )
