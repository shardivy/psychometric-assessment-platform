from django.urls import path

from organizations.views import (
    OrganizationCreateAPIView,
    OrganizationDraftDetailAPIView,
    OrganizationDraftUpdateAPIView,
    OrganizationListAPIView,
    OrganizationUpdateAPIView,
    PackageCreateAPIView,
    PackageListAPIView,
    PackageUpdateAPIView,
    PublicOrganizationCreateAPIView,
    PublishedAssessmentVersionListAPIView,
)

urlpatterns = [

    #============================= PACKAGE ==========================
    path(
        "packages/",
        PackageCreateAPIView.as_view(),
        name="package-create"
    ),
    path(
        "packages/<int:package_id>/",
        PackageUpdateAPIView.as_view(),
        name="package-update"
    ),
    path(
        "packages-list/",
        PackageListAPIView.as_view(),
        name="package-list"
    ),
    path(
        "assessment-versions/published/",
        PublishedAssessmentVersionListAPIView.as_view(),
        name="published-assessment-versions"
    ),
    
    #============================ ORGANIZATION ==========================
    
    path(
        "organizations/",
        OrganizationCreateAPIView.as_view(),
        name="organization-create"
    ),
     path(
        "organizations/<int:organization_id>/",
        OrganizationUpdateAPIView.as_view(),
        name="organization-update"
    ),
     path(
        "organizations/list/",
        OrganizationListAPIView.as_view(),
        name="organization-list"
    ),
     path(
        "organizations/create/",
        PublicOrganizationCreateAPIView.as_view(),
        name="organization-create"
    ),
    path(
        "organizations/<int:organization_id>/draft/",
        OrganizationDraftDetailAPIView.as_view(),
        name="organization-draft-detail"
    ),
    path(
        "organizations/<int:organization_id>/update/",
        OrganizationDraftUpdateAPIView.as_view(),
        name="organization-draft-update"
    ),
    

]