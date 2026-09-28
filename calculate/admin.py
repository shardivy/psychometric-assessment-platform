from django.contrib import admin

from calculate.models import AssessmentSectionCalculationRule, CalculationFormula

# ==========================================================
# CALCULATION FORMULA ADMIN
# ==========================================================

@admin.register(CalculationFormula)
class CalculationFormulaAdmin(admin.ModelAdmin):

    # ------------------------------------------------------
    # LIST DISPLAY
    # ------------------------------------------------------

    list_display = (
        "id",
        "case_number",
        "case_name",
        "result_unit",
        "status",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------

    list_filter = (
        "status",
        "result_unit",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

    search_fields = (
        "public_id",
        "case_name",
        "description",
        "formula",
    )

    # ------------------------------------------------------
    # ORDERING
    # ------------------------------------------------------

    ordering = (
        "case_number",
    )

    # ------------------------------------------------------
    # READONLY FIELDS
    # ------------------------------------------------------

    readonly_fields = (
        "id",
        "public_id",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # FIELDSETS
    # ------------------------------------------------------

    fieldsets = (

        (
            "Case Information",
            {
                "fields": (
                    "id",
                    "public_id",
                    "case_number",
                    "case_name",
                    "description",
                )
            }
        ),

        (
            "Formula",
            {
                "fields": (
                    "formula",
                    "variables",
                    "result_unit",
                )
            }
        ),

        (
            "Status",
            {
                "fields": (
                    "status",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )
    
# ==========================================================
# ASSESSMENT SECTION CALCULATION RULE ADMIN
# ==========================================================

@admin.register(AssessmentSectionCalculationRule)
class AssessmentSectionCalculationRuleAdmin(admin.ModelAdmin):

    # ------------------------------------------------------
    # LIST DISPLAY
    # ------------------------------------------------------

    list_display = (
        "id",
        "assessment_version",
        "section",
        "grade",
        "board",
        "calculation_formula",
        "status",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------

    list_filter = (
        "status",
        "board",
        "grade",
        "assessment_version",
        "section",
        "calculation_formula",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

    search_fields = (
        "public_id",
        "assessment_version__version_number",
        "section__name",
        "calculation_formula__case_name",
        "calculation_formula__formula",
    )

    # ------------------------------------------------------
    # ORDERING
    # ------------------------------------------------------

    ordering = (
        "assessment_version",
        "section",
        "grade",
        "board",
    )

    # ------------------------------------------------------
    # READONLY FIELDS
    # ------------------------------------------------------

    readonly_fields = (
        "id",
        "public_id",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # FIELDSETS
    # ------------------------------------------------------

    fieldsets = (

        (
            "Assessment",
            {
                "fields": (
                    "id",
                    "public_id",
                    "assessment_version",
                )
            }
        ),

        (
            "Blueprint Section",
            {
                "fields": (
                    "section",
                    "grade",
                    "board",
                )
            }
        ),

        (
            "Calculation Formula",
            {
                "fields": (
                    "calculation_formula",
                )
            }
        ),

        (
            "Status",
            {
                "fields": (
                    "status",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )
    
