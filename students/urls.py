from django.urls import path

from students.views import StudentAssessmentQuestionsAPIView, StudentRegistrationAPIView

urlpatterns = [

    path(
        "students/register/",
        StudentRegistrationAPIView.as_view(),
        name="student-register"
    ),
    path(
        "students/register/<str:registration_token>/",
        StudentRegistrationAPIView.as_view(),
        name="student-register-with-token"
    ),
    
    # ======================== Student side all question list =========================
    
    path(
        "student/registrations/<int:registration_id>/assessment-questions/",
        StudentAssessmentQuestionsAPIView.as_view(),
        name="student-assessment-questions",
    ),

]