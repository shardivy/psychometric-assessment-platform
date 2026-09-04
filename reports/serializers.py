from rest_framework import serializers

from reports.models import ReportTemplate

class ReportTemplateSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = ReportTemplate
        fields = [
            "id",
            "public_id",
            "template_code",
            "name",
            "report_type",
            "version",
            "description",
            "template_config_json",
            "language",
            "is_default",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "id",
            "public_id",
            "created_by",
            "created_at",
            "updated_at",
        )

    # ---------------------------------------
    # Created By
    # ---------------------------------------
    def get_created_by(self, obj):
        if obj.created_by:
            full_name = (
                f"{obj.created_by.first_name} "
                f"{obj.created_by.last_name}"
            ).strip()

            return full_name or obj.created_by.email

        return None

    # ---------------------------------------
    # Template Code Validation
    # ---------------------------------------
    def validate_template_code(self, value):

        queryset = ReportTemplate.objects.filter(
            template_code__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Template code already exists."
            )

        return value

    # ---------------------------------------
    # Template Config JSON Validation
    # ---------------------------------------
    def validate_template_config_json(self, value):

        if value is None:
            return value

        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "template_config_json must be a JSON object."
            )

        return value

    # ---------------------------------------
    # Name + Version Validation
    # ---------------------------------------
    def validate(self, attrs):

        name = attrs.get(
            "name",
            self.instance.name if self.instance else None,
        )

        version = attrs.get(
            "version",
            self.instance.version if self.instance else None,
        )

        queryset = ReportTemplate.objects.filter(
            name__iexact=name,
            version__iexact=version,
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "name": (
                        "A report template with this "
                        "name and version already exists."
                    )
                }
            )

        return attrs
    
# serializers.py

class ReportTemplateListSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = ReportTemplate
        fields = [
            "id",
            "public_id",
            "template_code",
            "name",
            "report_type",
            "version",
            "language",
            "is_default",
            "status",
            "created_by",
            "created_at",
        ]

    def get_created_by(self, obj):
        if obj.created_by:
            full_name = (
                f"{obj.created_by.first_name} "
                f"{obj.created_by.last_name}"
            ).strip()

            return full_name or obj.created_by.email

        return None