import re

from rest_framework import serializers
from django.db.models import Max

from assessments.models import Assessment, AssessmentBlueprintItem, AssessmentVersion, Grade, InterpretationRule, Question, QuestionOption, Section, SubSection, Tags

# ========================= Assessment =============================

class AssessmentSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            "id",
            "public_id",
            "assessment_code",
            "name",
            "short_name",
            "assessment_type",
            "description",
            "default_language",
            "icon",
            "thumbnail",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "public_id",
            "created_by",
            "created_at",
            "updated_at",
        )
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if request:
            if instance.icon:
                data["icon"] = request.build_absolute_uri(instance.icon.url)

            if instance.thumbnail:
                data["thumbnail"] = request.build_absolute_uri(
                    instance.thumbnail.url
                )

        return data

    def get_created_by(self, obj):
        if obj.created_by:
            full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return full_name or obj.created_by.email
        return None

    def validate_assessment_code(self, value):
        queryset = Assessment.objects.filter(
            assessment_code__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Assessment code already exists."
            )

        return value

    def validate(self, attrs):
        assessment_type = attrs.get(
            "assessment_type",
            self.instance.assessment_type if self.instance else None,
        )

        name = attrs.get(
            "name",
            self.instance.name if self.instance else None,
        )

        queryset = Assessment.objects.filter(
            assessment_type=assessment_type,
            name__iexact=name,
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "name": (
                        "Assessment name already exists "
                        "for this assessment type."
                    )
                }
            )

        return attrs
    
# ======================== Assessment Version =====================
class AssessmentVersionSerializer(serializers.ModelSerializer):

    assessment_name = serializers.CharField(
        source="assessment.name",
        read_only=True
    )

    report_template_name = serializers.CharField(
        source="report_template.name",
        read_only=True
    )

    published_by = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentVersion

        fields = [
            "id",
            "public_id",

            "assessment",
            "assessment_name",

            "report_template",
            "report_template_name",

            "version_number",
            "version_name",

            "release_date",
            "effective_from",
            "effective_to",

            "duration_minutes",

            "total_sections",
            "total_subsections",
            "total_questions",

            "total_marks",
            "minimum_qualifying_marks",
            "minimum_qualifying_percentage",

            "allow_resume",
            "allow_review",
            "randomize_sections",
            "randomize_questions",
            "show_result_immediately",

            "instructions",

            "status",

            "published_by",
            "published_at",

            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "id",
            "public_id",
            "published_by",
            "published_at",
            "created_at",
            "updated_at",
        )
        
    # -------------------------------------------------------
    # Published By
    # -------------------------------------------------------

    def get_published_by(self, obj):

        if obj.published_by:

            full_name = (
                f"{obj.published_by.first_name} "
                f"{obj.published_by.last_name}"
            ).strip()

            return full_name or obj.published_by.email

        return None
    
    # -------------------------------------------------------
    # Version Number Validation
    # -------------------------------------------------------

    def validate(self, value):

        assessment = self.initial_data.get("assessment")

        queryset = AssessmentVersion.objects.filter(
            assessment_id=assessment,
            version_number__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():

            raise serializers.ValidationError(
                "Version number already exists for this assessment."
            )

        return value

    # -------------------------------------------------------
    # Effective Date Validation
    # -------------------------------------------------------

    def validate(self, attrs):

        effective_from = attrs.get(
            "effective_from",
            self.instance.effective_from if self.instance else None
        )

        effective_to = attrs.get(
            "effective_to",
            self.instance.effective_to if self.instance else None
        )

        if (
            effective_from and
            effective_to and
            effective_to < effective_from
        ):

            raise serializers.ValidationError(
                {
                    "effective_to":
                    "Effective To must be greater than Effective From."
                }
            )

        total_marks = attrs.get(
            "total_marks",
            self.instance.total_marks if self.instance else None
        )

        minimum_marks = attrs.get(
            "minimum_qualifying_marks",
            self.instance.minimum_qualifying_marks if self.instance else None
        )

        if (
            minimum_marks is not None and
            total_marks is not None and
            minimum_marks > total_marks
        ):

            raise serializers.ValidationError(
                {
                    "minimum_qualifying_marks":
                    "Minimum qualifying marks cannot be greater than total marks."
                }
            )

        minimum_percentage = attrs.get(
            "minimum_qualifying_percentage",
            self.instance.minimum_qualifying_percentage if self.instance else None
        )

        if minimum_percentage is not None:

            if minimum_percentage < 0 or minimum_percentage > 100:

                raise serializers.ValidationError(
                    {
                        "minimum_qualifying_percentage":
                        "Percentage must be between 0 and 100."
                    }
                )

        total_sections = attrs.get(
            "total_sections",
            self.instance.total_sections if self.instance else None
        )

        total_subsections = attrs.get(
            "total_subsections",
            self.instance.total_subsections if self.instance else None
        )

        total_questions = attrs.get(
            "total_questions",
            self.instance.total_questions if self.instance else None
        )

        if total_sections <= 0:

            raise serializers.ValidationError(
                {
                    "total_sections":
                    "Total sections must be greater than zero."
                }
            )

        if total_subsections <= 0:

            raise serializers.ValidationError(
                {
                    "total_subsections":
                    "Total subsections must be greater than zero."
                }
            )

        if total_questions <= 0:

            raise serializers.ValidationError(
                {
                    "total_questions":
                    "Total questions must be greater than zero."
                }
            )

        return attrs
        
class AssessmentVersionListSerializer(serializers.ModelSerializer):

    assessment_name = serializers.CharField(
        source="assessment.name",
        read_only=True
    )

    report_template_name = serializers.CharField(
        source="report_template.name",
        read_only=True
    )

    published_by = serializers.SerializerMethodField()

    class Meta:

        model = AssessmentVersion

        fields = [
            "id",
            "public_id",

            "assessment",
            "assessment_name",

            "report_template",
            "report_template_name",

            "version_number",
            "version_name",

            "effective_from",
            "effective_to",

            "duration_minutes",

            "total_sections",
            "total_subsections",
            "total_questions",

            "total_marks",

            "status",

            "published_by",
            "published_at",

            "created_at",
        ]

    # -------------------------------------------------------
    # Published By
    # -------------------------------------------------------

    def get_published_by(self, obj):

        if obj.published_by:

            full_name = (
                f"{obj.published_by.first_name} "
                f"{obj.published_by.last_name}"
            ).strip()

            return full_name or obj.published_by.email

        return None

    # -------------------------------------------------------
    # Version Number Validation
    # -------------------------------------------------------

    def validate_version_number(self, value):

        assessment = self.initial_data.get("assessment")

        queryset = AssessmentVersion.objects.filter(
            assessment_id=assessment,
            version_number__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():

            raise serializers.ValidationError(
                "Version number already exists for this assessment."
            )

        return value

    # -------------------------------------------------------
    # Effective Date Validation
    # -------------------------------------------------------

    def validate(self, attrs):

        effective_from = attrs.get(
            "effective_from",
            self.instance.effective_from if self.instance else None
        )

        effective_to = attrs.get(
            "effective_to",
            self.instance.effective_to if self.instance else None
        )

        if (
            effective_from and
            effective_to and
            effective_to < effective_from
        ):

            raise serializers.ValidationError(
                {
                    "effective_to":
                    "Effective To must be greater than Effective From."
                }
            )

        total_marks = attrs.get(
            "total_marks",
            self.instance.total_marks if self.instance else None
        )

        minimum_marks = attrs.get(
            "minimum_qualifying_marks",
            self.instance.minimum_qualifying_marks if self.instance else None
        )

        if (
            minimum_marks is not None and
            total_marks is not None and
            minimum_marks > total_marks
        ):

            raise serializers.ValidationError(
                {
                    "minimum_qualifying_marks":
                    "Minimum qualifying marks cannot be greater than total marks."
                }
            )

        minimum_percentage = attrs.get(
            "minimum_qualifying_percentage",
            self.instance.minimum_qualifying_percentage if self.instance else None
        )

        if minimum_percentage is not None:

            if minimum_percentage < 0 or minimum_percentage > 100:

                raise serializers.ValidationError(
                    {
                        "minimum_qualifying_percentage":
                        "Percentage must be between 0 and 100."
                    }
                )

        total_sections = attrs.get(
            "total_sections",
            self.instance.total_sections if self.instance else None
        )

        total_subsections = attrs.get(
            "total_subsections",
            self.instance.total_subsections if self.instance else None
        )

        total_questions = attrs.get(
            "total_questions",
            self.instance.total_questions if self.instance else None
        )

        if total_sections <= 0:

            raise serializers.ValidationError(
                {
                    "total_sections":
                    "Total sections must be greater than zero."
                }
            )

        if total_subsections <= 0:

            raise serializers.ValidationError(
                {
                    "total_subsections":
                    "Total subsections must be greater than zero."
                }
            )

        if total_questions <= 0:

            raise serializers.ValidationError(
                {
                    "total_questions":
                    "Total questions must be greater than zero."
                }
            )

        return attrs
    
# ========================== Grade ========================
class GradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Grade
        fields = [
            "id",
            "public_id",
            "grade_code",
            "grade_name",
            "education_level",
            "display_order",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "id",
            "public_id",
            "grade_code",
            "created_at",
            "updated_at",
        )

    # -------------------------------------------------------
    # Grade Name Validation
    # -------------------------------------------------------
    def validate_grade_name(self, value):

        value = value.strip()

        queryset = Grade.objects.filter(
            grade_name__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "Grade name already exists."
            )

        return value

    # -------------------------------------------------------
    # Display Order Validation
    # -------------------------------------------------------
    def validate_display_order(self, value):

        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Display order must be greater than zero."
            )

        return value

    # -------------------------------------------------------
    # Generate Grade Code
    # -------------------------------------------------------
    # Creates a grade code from the grade name.
    # Removes spaces, underscores, hyphens, and special characters,
    # converts the text to uppercase, and adds the "GRADE" prefix.
    # Examples:
    # Grade 10   -> GRADE10
    # Grade_10   -> GRADE10
    # Grade-10   -> GRADE10
    # 10         -> GRADE10
    
    @staticmethod
    def generate_grade_code(grade_name):

        # Convert to uppercase
        code = grade_name.upper().strip()

        # Remove all non-alphanumeric characters
        code = re.sub(r'[^A-Z0-9]', '', code)

        # Remove leading GRADE if already present
        if code.startswith("GRADE"):
            code = code[5:]

        # Add prefix
        code = f"GRADE{code}"

        return code

    # -------------------------------------------------------
    # Validate
    # -------------------------------------------------------
    def validate(self, attrs):

        grade_name = attrs.get(
            "grade_name",
            getattr(self.instance, "grade_name", None)
        )

        grade_code = self.generate_grade_code(grade_name)

        queryset = Grade.objects.filter(
            grade_code=grade_code
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "grade_name": "A grade with this code already exists."
                }
            )

        attrs["grade_code"] = grade_code

        return attrs
    
    # -------------------------------------------------------
    # Generate Display Order
    # -------------------------------------------------------
    @staticmethod
    def generate_display_order():

        max_order = Grade.objects.aggregate(
            max_order=Max("display_order")
        )["max_order"]

        if max_order is None:
            return 1

        return max_order + 1

    # -------------------------------------------------------
    # Create
    # -------------------------------------------------------
    def create(self, validated_data):

        validated_data["grade_code"] = self.generate_grade_code(
            validated_data["grade_name"]
        )
        
        # Auto generate display order if not provided
        if not validated_data.get("display_order"):
            validated_data["display_order"] = self.generate_display_order()

        return super().create(validated_data)

    # -------------------------------------------------------
    # Update
    # -------------------------------------------------------
    def update(self, instance, validated_data):

        if "grade_name" in validated_data:
            validated_data["grade_code"] = self.generate_grade_code(
                validated_data["grade_name"]
            )

        return super().update(instance, validated_data)
    
    
# ======================== Tags ========================

class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags

        fields = (
            "id",
            "public_id",
            "tag_name",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "public_id",
            "created_at",
            "updated_at",
        )

    def validate_tag_name(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Tag name is required."
            )

        queryset = Tags.objects.filter(
            tag_name__iexact=value
        )

        # During PUT, exclude current tag
        if self.instance:
            queryset = queryset.exclude(
                id=self.instance.id
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Tag already exists."
            )

        return value



# =========================== Section =====================

class SectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Section
        fields = [
            "id",
            "public_id",
            "section_code",
            "name",
            "description",
            "instructions",
            "display_order",
            "is_mandatory",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "id",
            "public_id",
            "section_code",
            "created_at",
            "updated_at",
        )

    # ---------------------------------------------------------
    # Generate Section Code
    # ---------------------------------------------------------
    @staticmethod
    def generate_section_code(name):

        words = re.findall(r"[A-Za-z0-9]+", name.upper())

        if len(words) == 1:
            return words[0][:3]

        return "".join(word[0] for word in words)

    # ---------------------------------------------------------
    # Name Validation
    # ---------------------------------------------------------
    def validate_name(self, value):

        value = value.strip()

        queryset = Section.objects.filter(
            name__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "Section name already exists."
            )

        return value
    
    # ---------------------------------------------------------
    # Display Order Validation
    # ---------------------------------------------------------
    def validate_display_order(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Display order must be greater than zero."
            )

        queryset = Section.objects.filter(
            display_order=value
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                f"Display order '{value}' is already assigned to another section. Please choose a different display order."
            )

        return value

        # ---------------------------------------------------------
        # Object Validation
        # ---------------------------------------------------------
    def validate(self, attrs):

            name = attrs.get(
                "name",
                getattr(self.instance, "name", "")
            )

            section_code = self.generate_section_code(name)

            queryset = Section.objects.filter(
                section_code=section_code
            )

            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():

                raise serializers.ValidationError(
                    {
                        "name": f'Section code "{section_code}" already exists.'
                    }
                )

            attrs["section_code"] = section_code

            return attrs

        # ---------------------------------------------------------
        # Create
        # ---------------------------------------------------------
    def create(self, validated_data):

            validated_data["section_code"] = self.generate_section_code(
                validated_data["name"]
            )

            return super().create(validated_data)

        # ---------------------------------------------------------
        # Update
        # ---------------------------------------------------------
    def update(self, instance, validated_data):

            if "name" in validated_data:
                validated_data["section_code"] = (
                    self.generate_section_code(
                        validated_data["name"]
                    )
                )

            return super().update(instance, validated_data)  
        
# ====================== Sub-Section ======================
class SubSectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubSection
        fields = [
            "id",
            "public_id",
            "subsection_code",
            "name",
            "description",
            "instructions",
            "display_order",
            "time_limit_minutes",
            "question_limit",
            "randomize_questions",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = (
            "id",
            "public_id",
            "subsection_code",
            "created_at",
            "updated_at",
        )

    # ---------------------------------------------------------
    # Generate Sub Section Code
    # ---------------------------------------------------------
    @staticmethod
    def generate_subsection_code(name):

        words = re.findall(r"[A-Za-z0-9]+", name.upper())

        # Single word
        if len(words) == 1:
            return words[0][:3]

        # Multiple words
        return "".join(word[0] for word in words)

    # ---------------------------------------------------------
    # Name Validation
    # ---------------------------------------------------------
    def validate_name(self, value):

        value = value.strip()

        queryset = SubSection.objects.filter(
            name__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "Sub section name already exists."
            )

        return value

    # ---------------------------------------------------------
    # Display Order Validation
    # ---------------------------------------------------------
    def validate_display_order(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Display order must be greater than zero."
            )

        queryset = SubSection.objects.filter(
            display_order=value
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                f"Display order '{value}' is already assigned to another subsection."
            )

        return value

    # ---------------------------------------------------------
    # Time Limit Validation
    # ---------------------------------------------------------
    def validate_time_limit_minutes(self, value):

        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Time limit must be greater than zero."
            )

        return value

    # ---------------------------------------------------------
    # Question Limit Validation
    # ---------------------------------------------------------
    def validate_question_limit(self, value):

        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Question limit must be greater than zero."
            )

        return value

    # ---------------------------------------------------------
    # Object Validation
    # ---------------------------------------------------------
    def validate(self, attrs):

        name = attrs.get(
            "name",
            getattr(self.instance, "name", "")
        )

        subsection_code = self.generate_subsection_code(name)

        queryset = SubSection.objects.filter(
            subsection_code=subsection_code
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():

            raise serializers.ValidationError(
                {
                    "name":
                        f'Sub section code "{subsection_code}" already exists.'
                }
            )

        attrs["subsection_code"] = subsection_code

        return attrs

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------
    def create(self, validated_data):

        validated_data["subsection_code"] = (
            self.generate_subsection_code(
                validated_data["name"]
            )
        )

        return super().create(validated_data)

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------
    def update(self, instance, validated_data):

        if "name" in validated_data:

            validated_data["subsection_code"] = (
                self.generate_subsection_code(
                    validated_data["name"]
                )
            )

        return super().update(instance, validated_data)
    
# ===================== Builder Serializers =============================

class AssessmentVersionInputSerializer(serializers.Serializer):

    report_template_id = serializers.IntegerField()

    version_number = serializers.CharField(
        max_length=20
    )

    version_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    release_date = serializers.DateField(
        required=False,
        allow_null=True
    )

    effective_from = serializers.DateField()

    effective_to = serializers.DateField(
        required=False,
        allow_null=True
    )

    duration_minutes = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1
    )

    allow_resume = serializers.BooleanField(
        required=False,
        default=False
    )

    allow_review = serializers.BooleanField(
        required=False,
        default=True
    )

    randomize_sections = serializers.BooleanField(
        required=False,
        default=False
    )
    
    section_wise_randomize_question = serializers.BooleanField(
        required=False,
        default=False
    )

    show_result_immediately = serializers.BooleanField(
        required=False,
        default=False
    )

    instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    
class AssessmentQuestionInputSerializer(serializers.Serializer):

    subsection_id = serializers.IntegerField(
        min_value=1
    )

    question_ids = serializers.ListField(
        child=serializers.IntegerField(
            min_value=1
        ),
        allow_empty=False
    )

    def validate_question_ids(self, value):

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate question IDs are not allowed."
            )

        return value
    
class AssessmentSubSectionInputSerializer(serializers.Serializer):

    subsection_id = serializers.IntegerField(
        min_value=1
    )

    questions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )

    def validate(self, attrs):

        questions = attrs.get("questions", [])

        question_ids = [
            question.get("question_id")
            for question in questions
        ]

        if any(not question_id for question_id in question_ids):
            raise serializers.ValidationError({
                "questions": "Each question must contain question_id."
            })

        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError({
                "questions": "Duplicate question IDs are not allowed."
            })

        return attrs
    
class AssessmentSectionInputSerializer(serializers.Serializer):

    section_id = serializers.IntegerField(
        min_value=1
    )

    subsections = AssessmentSubSectionInputSerializer(
        many=True,
        allow_empty=False,
        required=False
    )

    # def validate(self, attrs):

    #     subsection_ids = [
    #         item["subsection_id"]
    #         for item in attrs["subsections"]
    #     ]

    #     if len(subsection_ids) != len(set(subsection_ids)):
    #         raise serializers.ValidationError(
    #             "Duplicate subsection IDs are not allowed."
    #         )

    #     return attrs
    
class AssessmentBlueprintInputSerializer(serializers.Serializer):

    grade_id = serializers.IntegerField(
        min_value=1
    )

    sections = AssessmentSectionInputSerializer(
        many=True,
        allow_empty=True,
        required=False
    )

    board = serializers.ChoiceField(
        choices=AssessmentBlueprintItem.Board.choices,
        required=False,
        default=AssessmentBlueprintItem.Board.ALL
    )

    sequence_start = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1
    )

    marks_override = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    negative_marks_override = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    is_mandatory = serializers.BooleanField(
        required=False,
        default=True
    )

    is_randomizable = serializers.BooleanField(
        required=False,
        default=False
    )

    is_visible = serializers.BooleanField(
        required=False,
        default=True
    )

    def validate(self, attrs):

        section_ids = [
            section["section_id"]
            for section in attrs["sections"]
        ]

        if len(section_ids) != len(set(section_ids)):
            raise serializers.ValidationError(
                "Duplicate section IDs are not allowed."
            )

        return attrs
    
    
class AssessmentBuilderSerializer(serializers.Serializer):

    assessment = serializers.DictField(
        required=True
    )

    version_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1
    )

    version = AssessmentVersionInputSerializer(
        required=False,
        allow_null=True
    )

    is_draft = serializers.BooleanField(
        default=True
    )

    blueprint_items = AssessmentBlueprintInputSerializer(
        many=True,
        required=False,
        allow_empty=True
    )

    def validate(self, attrs):

        assessment_data = attrs.get("assessment")

        version_id = attrs.get("version_id")

        version_data = attrs.get("version")

        # ==================================================
        # 1. ASSESSMENT REQUIRED
        # ==================================================

        if not assessment_data:
            raise serializers.ValidationError({
                "assessment": "Assessment data is required."
            })

        # ==================================================
        # 2. NAME
        # ==================================================

        name = assessment_data.get("name")

        if not name:
            raise serializers.ValidationError({
                "assessment": {
                    "name": "This field is required."
                }
            })

        # ==================================================
        # 3. NAME CAN BE:
        #
        # "Aptitude Assessment" -> NEW ASSESSMENT
        #
        # "1" -> EXISTING ASSESSMENT ID 1
        # ==================================================

        if isinstance(name, str):

            name = name.strip()

            # ----------------------------------------------
            # Numeric string = Assessment ID
            # ----------------------------------------------

            if name.isdigit():

                assessment_id = int(name)

                if assessment_id <= 0:
                    raise serializers.ValidationError({
                        "assessment": {
                            "name": (
                                "Assessment ID must be "
                                "greater than 0."
                            )
                        }
                    })

                # Store normalized ID
                assessment_data["id"] = assessment_id

                # Optional: remove name because it is ID
                assessment_data.pop("name", None)

            else:

                # ------------------------------------------
                # Normal text = New Assessment
                # ------------------------------------------

                assessment_data["name"] = name

                if not assessment_data.get(
                    "assessment_type"
                ):
                    raise serializers.ValidationError({
                        "assessment": {
                            "assessment_type":
                                "This field is required "
                                "for a new assessment."
                        }
                    })

        else:

            raise serializers.ValidationError({
                "assessment": {
                    "name": (
                        "Name must be a string containing "
                        "either an assessment name or "
                        "an assessment ID."
                    )
                }
            })

        # ==================================================
        # 4. VERSION VALIDATION
        # ==================================================

        if version_id and version_data:

            raise serializers.ValidationError({
                "version": (
                    "Provide either version_id "
                    "or version details, not both."
                )
            })

        return attrs
 
class AssessmentBlueprintListSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    assessment_name = serializers.CharField(
        source="assessment.name",
        read_only=True
    )

    assessment_type = serializers.CharField(
        source="assessment.assessment_type",
        read_only=True
    )

    grades = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    subsections = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentVersion

        fields = [
            "id",
            "public_id",

            # Assessment
            "assessment_name",
            "assessment_type",

            # Version
            "version_number",
            "version_name",
            "status",
            "updated_at",

            # Blueprint hierarchy
            "grades",
            "sections",
            "subsections",
        ]

    def get_id(self, obj):
        blueprint = (
            obj.blueprint_items
            .order_by("id")
            .first()
        )

        return blueprint.id if blueprint else None

    def get_grades(self, obj):
        grades = (
            obj.blueprint_items
            .filter(grade__isnull=False)
            .values(
                "grade_id",
                "grade__grade_name"
            )
            .distinct()
            .order_by("grade_id")
        )

        return [
            {
                "id": item["grade_id"],
                "name": item["grade__grade_name"],
            }
            for item in grades
        ]

    def get_sections(self, obj):
        sections = (
            obj.blueprint_items
            .filter(section__isnull=False)
            .values(
                "section_id",
                "section__name"
            )
            .distinct()
            .order_by("section_id")
        )

        return [
            {
                "id": item["section_id"],
                "name": item["section__name"],
            }
            for item in sections
        ]

    def get_subsections(self, obj):
        subsections = (
            obj.blueprint_items
            .filter(subsection__isnull=False)
            .values(
                "subsection_id",
                "subsection__name"
            )
            .distinct()
            .order_by("subsection_id")
        )

        return [
            {
                "id": item["subsection_id"],
                "name": item["subsection__name"],
            }
            for item in subsections
        ] 
        
class AssessmentVersionBlueprintSerializer(serializers.ModelSerializer):

    assessment_name = serializers.CharField(
        source="assessment.name",
        read_only=True
    )

    assessment_type = serializers.CharField(
        source="assessment.assessment_type",
        read_only=True
    )

    sections = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentVersion

        fields = [
            "id",
            "public_id",
            "assessment_name",
            "assessment_type",
            "version_number",
            "version_name",
            "status",
            "sections",
        ]

    def get_sections(self, obj):

        blueprint_items = obj.blueprint_items.all()

        sections = {}

        for item in blueprint_items:

            if not item.section:
                continue

            section_id = item.section_id

            if section_id not in sections:
                sections[section_id] = {
                    "section_id": section_id,
                    "section_name": item.section.name,
                    "subsections": {}
                }

            if not item.subsection:
                continue

            subsection_id = item.subsection_id

            sections[section_id]["subsections"][
                subsection_id
            ] = {
                "subsection_id": subsection_id,
                "subsection_name": item.subsection.name
            }

        return [
            {
                "section_id": section["section_id"],
                "section_name": section["section_name"],
                "subsections": list(
                    section["subsections"].values()
                )
            }
            for section in sections.values()
        ]   
              
class QuestionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = [
            "id",
            "public_id",
            "question_code",
            "question_type",
            "difficulty_level",
            "question_text",
            "media_type",
            "media_url",
            "is_mandatory",
            "explanation",
            "default_marks",
            "negative_marks",
            "expected_time_seconds",
            "language",
            "question_status",
        ]
        


# ==================== Questions ==============================

class GradeListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Grade
        fields = (
            "id",
            "grade_code",
            "grade_name",
        )
        
class TagsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = (
            "id",
            "public_id",
            "tag_name",
            "created_at",
            "updated_at",
        )
        
class SubSectionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubSection
        fields = (
            "id",
            "subsection_code",
            "name",
        )
        
class QuestionOptionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionOption
        fields = (
            "id",
            "option_code",
            "option_text",
            "option_image",
            "option_value",
            "display_order",
            "is_correct",
            "status",
        )
        
class QuestionRetrieveSerializer(serializers.ModelSerializer):

    options = QuestionOptionListSerializer(
        many=True,
        read_only=True,
    )

    grades = serializers.SerializerMethodField()

    tags = serializers.SerializerMethodField()

    created_by = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
    )

    class Meta:
        model = Question

        fields = (
            "id",
            "public_id",
            "question_code",
            "question_type",
            "difficulty_level",
            "question_text",
            "media_url",
            "media_file",
            "media_type",
            "is_mandatory",
            "explanation",
            "default_marks",
            "negative_marks",
            "expected_time_seconds",
            "language",
            "question_status",
            "is_active",
            "grades",
            "tags",
            "options",
            "created_by",
            "created_at",
            "updated_at",
        )

    def get_grades(self, obj):

        grades = []

        seen = set()

        for mapping in obj.grade_mappings.all():

            if mapping.grade_id and mapping.grade_id not in seen:

                grades.append(
                    {
                        "id": mapping.grade.id,
                        "grade_name": mapping.grade.grade_name,
                    }
                )

                seen.add(mapping.grade_id)

        return grades

    def get_tags(self, obj):

        tags = []

        seen = set()

        for mapping in obj.grade_mappings.all():

            if mapping.tag_id and mapping.tag_id not in seen:

                tags.append(
                    {
                        "id": mapping.tag.id,
                        "tag_name": mapping.tag.tag_name,
                    }
                )

                seen.add(mapping.tag_id)

        return tags
    
    
class QuestionOptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False
    )
    
    option_image = serializers.FileField(
            write_only=True,
            required=False,
            allow_null=True
        )

    class Meta:
        model = QuestionOption
        fields = (
            "id",
            "option_code",
            "option_text",
            "option_image",
            "option_value",
            "display_order",
            "is_correct",
            "status",
        )
        
class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    media_file = serializers.ImageField(
        write_only=True,
        required=False,
        allow_null=True
    )

    grade_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )

    options = QuestionOptionSerializer(
        many=True,
        write_only=True,
        required=False,
    )

    is_draft = serializers.BooleanField(
        write_only=True,
        required=False,
        default=True,
    )

    class Meta:
        model = Question

        fields = (
            "public_id",
            "question_code",
            "question_type",
            "difficulty_level",
            "question_text",
            "media_file",
            "media_url",
            "media_type",
            "is_mandatory",
            "explanation",
            "default_marks",
            "negative_marks",
            "expected_time_seconds",
            "language",
            "grade_ids",
            "tag_ids",
            "options",
            "is_draft",
        )
        
    def validate_grade_ids(self, value):

        if not value:
            raise serializers.ValidationError(
                "At least one grade is required."
            )

        # grades = Grade.objects.filter(
        #     id__in=value,
        # )

        # if grades.count() != len(set(value)):
        #     raise serializers.ValidationError(
        #         "One or more grade ids are invalid."
        #     )

        return value
    
    def validate_tag_ids(self, value):

        if not value:
            return []

        return list(set(value))
    
    def validate_options(self, value):

        if not value:
            raise serializers.ValidationError(
                "At least one option is required."
            )

        option_codes = set()
        display_orders = set()
        correct_answers = 0

        for option in value:

            if option["option_code"] in option_codes:
                raise serializers.ValidationError(
                    "Duplicate option_code found."
                )

            option_codes.add(
                option["option_code"]
            )

            if option["display_order"] in display_orders:
                raise serializers.ValidationError(
                    "Duplicate display_order found."
                )

            display_orders.add(
                option["display_order"]
            )

            if option.get("is_correct"):
                correct_answers += 1

        # if correct_answers == 0:
        #     raise serializers.ValidationError(
        #         "At least one correct option is required."
        #     )

        return value
    
    def validate_question_code(self, value):

        queryset = Question.objects.filter(
            question_code=value
        )

        if self.instance is not None:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Question code already exists."
            )

        return value
    
    # def validate_subsection(self, value):

    #     if value is None:
    #         raise serializers.ValidationError(
    #             "Subsection is required."
    #         )

    #     return value
    
    def validate(self, attrs):

        media_type = attrs.get("media_type")
        media_file = attrs.get("media_file")
        media_url = attrs.get("media_url")

        if media_type == Question.MediaType.NONE:
            attrs["media_file"] = None
            attrs["media_url"] = None

        elif media_type == Question.MediaType.IMAGE:

            if not media_file:
                raise serializers.ValidationError({
                    "media_file": "Image file is required."
                })

        elif media_type in (
            Question.MediaType.AUDIO,
            Question.MediaType.VIDEO,
        ):

            if not media_file and not media_url:
                raise serializers.ValidationError({
                    "media": "Upload a file or provide a URL."
                })

        return attrs

class QuestionLibrarySerializer(serializers.ModelSerializer):

    grades = serializers.SerializerMethodField()

    tags = serializers.SerializerMethodField()

    class Meta:
        model = Question

        fields = (
            "id",
            "question_code",
            "question_text",
            "question_type",
            "difficulty_level",
            "question_status",
            "updated_at",
            "grades",
            "tags",
        )

    def get_grades(self, obj):

        return [
            {
                "id": mapping.grade.id,
                "grade_name": mapping.grade.grade_name,
            }
            for mapping in obj.grade_mappings.all()
            if mapping.grade
        ]

    def get_tags(self, obj):

        tags = {}

        for mapping in obj.grade_mappings.all():

            if mapping.tag:

                tags[mapping.tag.id] = {
                    "id": mapping.tag.id,
                    "tag_name": mapping.tag.tag_name,
                }

        return list(tags.values())
    
# ================================ Interpretation Serializer =============================
    
class InterpretationRuleSubsectionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    
    subsection_id = serializers.IntegerField()

    min_score = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    max_score = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    rating = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )

    title = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )

    performance_analysis = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan_option1 = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan_option2 = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan_option3 = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan_option4 = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    action_plan_option5 = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    display_color = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    status = serializers.ChoiceField(
        choices=InterpretationRule.Status.choices,
        required=False
    )


class InterpretationRuleBulkCreateSerializer(serializers.Serializer):

    assessment_version_id = serializers.IntegerField()

    is_draft = serializers.BooleanField(
        default=True
    )

    subsections = InterpretationRuleSubsectionSerializer(
        many=True
    )

    def validate(self, attrs):

        assessment_version_id = attrs.get(
            "assessment_version_id"
        )

        is_draft = attrs.get(
            "is_draft",
            True
        )

        subsections = attrs.get(
            "subsections",
            []
        )

        # ==================================================
        # VALIDATE ASSESSMENT VERSION
        # ==================================================

        try:

            assessment_version = (
                AssessmentVersion.objects.get(
                    id=assessment_version_id
                )
            )

        except AssessmentVersion.DoesNotExist:

            raise serializers.ValidationError({
                "assessment_version_id": (
                    "Assessment version not found."
                )
            })

        # ==================================================
        # SUBSECTIONS REQUIRED
        # ==================================================

        if not subsections:

            raise serializers.ValidationError({
                "subsections": (
                    "At least one subsection is required."
                )
            })

        # ==================================================
        # VALIDATE SUBSECTION IDs
        # ==================================================

        subsection_ids = [
            item["subsection_id"]
            for item in subsections
        ]

        existing_ids = set(
            SubSection.objects.filter(
                id__in=subsection_ids
            ).values_list(
                "id",
                flat=True
            )
        )

        invalid_ids = [
            subsection_id
            for subsection_id in subsection_ids
            if subsection_id not in existing_ids
        ]

        if invalid_ids:

            raise serializers.ValidationError({
                "subsections": (
                    f"Invalid subsection IDs: "
                    f"{invalid_ids}"
                )
            })

        # ==================================================
        # NON-DRAFT VALIDATION
        # ==================================================

        if not is_draft:

            errors = {}

            for index, item in enumerate(subsections):

                required_fields = [
                    "min_score",
                    "max_score",
                    "rating",
                    "title",
                    "display_color",
                ]

                missing_fields = []

                for field in required_fields:

                    value = item.get(field)

                    if value is None or value == "":

                        missing_fields.append(
                            field
                        )

                if missing_fields:

                    errors[index] = {
                        "missing_fields": missing_fields
                    }

            if errors:

                raise serializers.ValidationError({
                    "subsections": errors
                })

        # ==================================================
        # ADD ASSESSMENT VERSION OBJECT
        # ==================================================

        attrs["assessment_version"] = (
            assessment_version
        )

        return attrs
    
class InterpretationRuleBulkUpdateSerializer(serializers.Serializer):

    assessment_version_id = serializers.IntegerField()

    is_draft = serializers.BooleanField(
        default=True
    )

    subsections = InterpretationRuleSubsectionSerializer(
        many=True
    )

    def validate(self, attrs):

        assessment_version_id = attrs.get(
            "assessment_version_id"
        )

        is_draft = attrs.get(
            "is_draft",
            True
        )

        subsections = attrs.get(
            "subsections",
            []
        )

        # ==================================================
        # VALIDATE ASSESSMENT VERSION
        # ==================================================

        try:

            assessment_version = (
                AssessmentVersion.objects.get(
                    id=assessment_version_id
                )
            )

        except AssessmentVersion.DoesNotExist:

            raise serializers.ValidationError({
                "assessment_version_id":
                    "Assessment version not found."
            })

        # ==================================================
        # SUBSECTIONS REQUIRED
        # ==================================================

        if not subsections:

            raise serializers.ValidationError({
                "subsections":
                    "At least one subsection is required."
            })

        # ==================================================
        # DUPLICATE INTERPRETATION IDS
        # ==================================================

        interpretation_ids = [
            item["id"]
            for item in subsections
            if item.get("id") is not None
        ]

        if (
            len(interpretation_ids)
            != len(set(interpretation_ids))
        ):

            raise serializers.ValidationError({
                "subsections":
                    "Duplicate interpretation rule IDs are not allowed."
            })

        # ==================================================
        # VALIDATE SUBSECTIONS
        # ==================================================

        subsection_ids = [
            item["subsection_id"]
            for item in subsections
        ]

        existing_subsection_ids = set(
            SubSection.objects.filter(
                id__in=subsection_ids
            ).values_list(
                "id",
                flat=True
            )
        )

        invalid_subsection_ids = [
            subsection_id
            for subsection_id in subsection_ids
            if subsection_id not in existing_subsection_ids
        ]

        if invalid_subsection_ids:

            raise serializers.ValidationError({
                "subsections":
                    f"Invalid subsection IDs: "
                    f"{invalid_subsection_ids}"
            })


        # ==================================================
        # DUPLICATE SCORE RANGE VALIDATION
        # ==================================================

        score_range_errors = {}

        for index, item in enumerate(subsections):

            interpretation_id = item.get("id")

            subsection_id = item.get(
                "subsection_id"
            )

            min_score = item.get(
                "min_score"
            )

            max_score = item.get(
                "max_score"
            )

            # ----------------------------------------------
            # Draft mode can have incomplete score values
            # ----------------------------------------------

            if min_score is None or max_score is None:
                continue

            # ----------------------------------------------
            # Validate min <= max
            # ----------------------------------------------

            if min_score > max_score:

                score_range_errors[index] = {
                    "subsection_id": subsection_id,
                    "message": (
                        "min_score cannot be greater "
                        "than max_score."
                    )
                }

                continue

            # ----------------------------------------------
            # Check duplicate inside current request
            # ----------------------------------------------

            for other_index, other_item in enumerate(
                subsections
            ):

                if index == other_index:
                    continue

                if (
                    other_item.get("subsection_id")
                    != subsection_id
                ):
                    continue

                other_min = other_item.get(
                    "min_score"
                )

                other_max = other_item.get(
                    "max_score"
                )

                if (
                    other_min is None
                    or other_max is None
                ):
                    continue

                if (
                    min_score == other_min
                    and max_score == other_max
                ):

                    score_range_errors[index] = {
                        "subsection_id": subsection_id,
                        "min_score": str(min_score),
                        "max_score": str(max_score),
                        "message": (
                            "This score range is duplicated "
                            "for this subsection in the request."
                        )
                    }

                    break

            # ----------------------------------------------
            # Check existing database record
            # ----------------------------------------------

            existing_rule_query = (
                InterpretationRule.objects.filter(
                    assessment_version_id=assessment_version_id,
                    subsection_id=subsection_id,
                    min_score=min_score,
                    max_score=max_score,
                )
            )

            # ----------------------------------------------
            # If updating, exclude current record
            # ----------------------------------------------

            if interpretation_id:

                existing_rule_query = (
                    existing_rule_query.exclude(
                        id=interpretation_id
                    )
                )

            existing_rule = (
                existing_rule_query.first()
            )

            if existing_rule:

                score_range_errors[index] = {
                    "subsection_id": subsection_id,
                    "min_score": str(min_score),
                    "max_score": str(max_score),
                    "existing_interpretation_id": (
                        existing_rule.id
                    ),
                    "message": (
                        "This min_score and max_score "
                        "already exist for this subsection."
                    )
                }


        if score_range_errors:

            raise serializers.ValidationError({
                "subsections": score_range_errors
            })

        # ==================================================
        # VALIDATE INTERPRETATION RULE IDS
        # ==================================================

        if interpretation_ids:

            rules = InterpretationRule.objects.filter(
                id__in=interpretation_ids
            )

            existing_rule_ids = set(
                rules.values_list(
                    "id",
                    flat=True
                )
            )

            invalid_rule_ids = [
                rule_id
                for rule_id in interpretation_ids
                if rule_id not in existing_rule_ids
            ]

            if invalid_rule_ids:

                raise serializers.ValidationError({
                    "subsections":
                        f"Invalid interpretation rule IDs: "
                        f"{invalid_rule_ids}"
                })

            # ==================================================
            # MAKE SURE RULE BELONGS TO SAME VERSION
            # ==================================================

            wrong_version_ids = list(
                rules.exclude(
                    assessment_version_id=assessment_version_id
                ).values_list(
                    "id",
                    flat=True
                )
            )

            if wrong_version_ids:

                raise serializers.ValidationError({
                    "subsections":
                        "These interpretation rule IDs do not "
                        "belong to the selected assessment version: "
                        f"{wrong_version_ids}"
                })

        # # ==================================================
        # # PUBLISHED VERSION CHECK
        # # ==================================================

        # if hasattr(assessment_version, "status"):

        #     if assessment_version.status == "PUBLISHED":

        #         raise serializers.ValidationError({
        #             "assessment_version_id":
        #                 "Published assessment version cannot "
        #                 "be modified."
        #         })

        # ==================================================
        # NON-DRAFT VALIDATION
        # ==================================================

        if not is_draft:

            errors = {}

            required_fields = [
                "min_score",
                "max_score",
                "rating",
                "display_color",
            ]

            for index, item in enumerate(subsections):

                missing_fields = []

                for field in required_fields:

                    value = item.get(field)

                    if value is None or value == "":

                        missing_fields.append(
                            field
                        )

                if missing_fields:

                    errors[index] = {
                        "missing_fields":
                            missing_fields
                    }

            if errors:

                raise serializers.ValidationError({
                    "subsections": errors
                })

        attrs["assessment_version"] = assessment_version

        return attrs

