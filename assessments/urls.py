from django.urls import path

from assessments.views import AssessmentAPIView, AssessmentBlueprintDraftDetailAPIView, AssessmentBlueprintItemUpdateAPIView, AssessmentBlueprintListAPIView, AssessmentBuilderAPIView, AssessmentVersionAPIView, AssessmentVersionBlueprintAPIView, AssessmentVersionGradesAPIView, GenerateAssessmentVersionAPIView, GenerateQuestionCodeAPIView, GradeAPIView, QuestionAPIView, QuestionLibraryAPIView, QuestionsByGradeTagAPIView, SectionAPIView, SubSectionAPIView, TagsAPIView


urlpatterns = [
    
    # ======================== Assessment =====================
    path(
        "assessments/",
        AssessmentAPIView.as_view(),
        name="assessment-list-create",
    ),

    path(
        "assessments/<int:id>/",
        AssessmentAPIView.as_view(),
        name="assessment-detail",
    ),
    
    # ======================== Assessment Version ====================
    
    path(
        "assessment-versions/",
        AssessmentVersionAPIView.as_view(),
        name="assessment-version-list-create",
    ),

    path(   
        "assessment-versions/<int:id>/",
        AssessmentVersionAPIView.as_view(),
        name="assessment-version-detail",
    ),
    
    # ==================== Grade ===========================
    path(
        "grades/",
        GradeAPIView.as_view(),
        name="grade-list-create",
    ),
    path(
        "grades/<int:id>/",
        GradeAPIView.as_view(),
        name="grade-detail",
    ),
    
    # ===================== Tags ==============================
    path(
        "tags/",
        TagsAPIView.as_view(),
        name="tags",
    ),

    path(
        "tags/<int:id>/",
        TagsAPIView.as_view(),
        name="tag-detail",
    ),
    
    # ========================= Section ========================
    path(
        "sections/",
        SectionAPIView.as_view(),
        name="section-list-create",
    ),
    path(
        "sections/<int:id>/",
        SectionAPIView.as_view(),
        name="section-detail",
    ),
    
    # ========================= Sub-Section ========================
    path(
        "subsections/",
        SubSectionAPIView.as_view(),
        name="subsection-list-create",
    ),
    path(
        "subsections/<int:id>/",
        SubSectionAPIView.as_view(),
        name="subsection-detail",
    ),
    
    # ======================= Assessment Builder =================
    path(
        "assessment/<int:assessment_id>/next-version/",
        GenerateAssessmentVersionAPIView.as_view(),
        name="generate-assessment-version",
    ),
    path(
        "assessment-builder/",
        AssessmentBuilderAPIView.as_view(),
        name="assessment-builder",
    ),
    path(
        "assessment-builder/draft/<int:blueprint_id>/",
        AssessmentBlueprintDraftDetailAPIView.as_view(),
        name="assessment-builder-draft-detail",
    ),
    path(
        "assessment-builder/blueprint-update/<int:version_id>/",
        AssessmentBlueprintItemUpdateAPIView.as_view(),
        name="assessment-blueprint-update",
    ),
    path(
        "assessment-builder-list/",
        AssessmentBlueprintListAPIView.as_view(),
        name="assessment-blueprint-list",
    ),
    path(
        "assessment-builder/versions/<int:version_id>/",
        AssessmentVersionBlueprintAPIView.as_view(),
        name="assessment-version-blueprint",
    ),
    path(
        "assessment-builder/versions/<int:version_id>/grades/",
        AssessmentVersionGradesAPIView.as_view(),
        name="assessment-version-grades",
    ),
    path(
        "assessment-questions/grades/<str:grade_ids>/tags/<str:tag_ids>/",
        QuestionsByGradeTagAPIView.as_view(),
        name="questions-by-grade-tag",
    ),
            


    
    # ======================== Questions =====================

    path(
        "question/generate-code/<int:tag_id>/",
        GenerateQuestionCodeAPIView.as_view(),
        name="generate-question-code",
    ),
    path(
        "questions/",
        QuestionAPIView.as_view(),
        name="question-api",
    ),
    path(
        "questions/<int:id>/",
        QuestionAPIView.as_view(),
        name="question-detail",
    ),
    
    path(
        "question-library/",
        QuestionLibraryAPIView.as_view(),
        name="question-library",
    ),

]