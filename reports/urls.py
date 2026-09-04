from django.urls import path

from reports.views import ReportTemplateAPIView


urlpatterns = [
    
    path(
        "report-templates/",
        ReportTemplateAPIView.as_view(),
        name="report-templates"      
    ),
    path(
        "report-templates/<int:id>/",
        ReportTemplateAPIView.as_view(),
        name="report-templates-update-delete"      
    ),
]