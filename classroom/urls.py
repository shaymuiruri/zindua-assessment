from django.urls import path
from .views import (
    AssignmentListCreateView,
    SubmissionCreateView,
    SubmissionFeedbackView,
)

urlpatterns = [
    path("assignments/", AssignmentListCreateView.as_view(), name="assignment-list-create"),
    path("submissions/", SubmissionCreateView.as_view(), name="submission-create"),
    path("submissions/<int:pk>/feedback/", SubmissionFeedbackView.as_view(), name="submission-feedback"),
]