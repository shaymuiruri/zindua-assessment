from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Assignment, Submission, Feedback, Enrollment
from .permissions import IsInstructor, IsStudent, CanViewFeedback
from .serializers import (
    AssignmentSerializer,
    SubmissionSerializer,
    FeedbackSerializer,
    FeedbackCreateSerializer,
)


class AssignmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/assignments/
        Returns only the assignments the authenticated user is allowed to see:
          - INSTRUCTOR → assignments they created
          - STUDENT    → assignments they are enrolled in
          - OBSERVER   → assignments their linked student is enrolled in

    POST /api/v1/assignments/
        Creates a new assignment. Restricted to INSTRUCTOR role.
    """

    serializer_class = AssignmentSerializer

    def get_permissions(self):
        # Different HTTP verbs require different permission levels.
        # POST (create) is instructor-only; GET (list) just needs authentication.
        if self.request.method == "POST":
            return [IsInstructor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        if user.role == "INSTRUCTOR":
            return Assignment.objects.filter(instructor=user)

        if user.role == "STUDENT":
            enrolled_ids = Enrollment.objects.filter(
                student=user
            ).values_list("assignment_id", flat=True)
            return Assignment.objects.filter(id__in=enrolled_ids)

        if user.role == "OBSERVER":
            # Row-level: only the assignments for the observer's linked student.
            # If no ObserverLink exists for this observer, return nothing.
            try:
                linked_student = user.observer_link.student
            except Exception:
                return Assignment.objects.none()

            enrolled_ids = Enrollment.objects.filter(
                student=linked_student
            ).values_list("assignment_id", flat=True)
            return Assignment.objects.filter(id__in=enrolled_ids)

        return Assignment.objects.none()

    def perform_create(self, serializer):
        # Automatically set the instructor to the currently logged-in user.
        # This means the client never needs to send instructor in the request body.
        serializer.save(instructor=self.request.user)


class SubmissionCreateView(generics.CreateAPIView):
    """
    POST /api/v1/submissions/
        Students submit their work. Restricted to STUDENT role.
        Business rules (enrollment check, duplicate check) are enforced
        in SubmissionSerializer.validate().
    """

    serializer_class = SubmissionSerializer
    permission_classes = [IsStudent]

    def perform_create(self, serializer):
        # Same pattern as above — pin the student to the logged-in user.
        serializer.save(student=self.request.user)


class SubmissionFeedbackView(APIView):
    """
    GET  /api/v1/submissions/{id}/feedback/
        Returns the feedback for a submission.
        Access is controlled by CanViewFeedback (role-level + row-level).

    POST /api/v1/submissions/{id}/feedback/
        Instructor leaves feedback on a submission.
        Restricted to the instructor who owns the assignment.
    """

    permission_classes = [CanViewFeedback]

    def get(self, request, pk):
        try:
            submission = Submission.objects.select_related(
                "feedback",
                "student",
                "assignment__instructor",
            ).get(pk=pk)
        except Submission.DoesNotExist:
            return Response(
                {"detail": "Submission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # IMPORTANT: on APIView, has_object_permission is NOT called
        # automatically — unlike on ModelViewSet. We must call it ourselves.
        # Skipping this line would make the row-level check never run,
        # leaving the endpoint open to any authenticated user.
        self.check_object_permissions(request, submission)

        try:
            feedback = submission.feedback
        except Feedback.DoesNotExist:
            return Response(
                {"detail": "No feedback has been left for this submission yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data)

    def post(self, request, pk):
        """Instructor submits feedback for a submission."""
        if request.user.role != "INSTRUCTOR":
            return Response(
                {"detail": "Only instructors can leave feedback."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            submission = Submission.objects.select_related(
                "assignment__instructor"
            ).get(pk=pk)
        except Submission.DoesNotExist:
            return Response(
                {"detail": "Submission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # An instructor may only give feedback on their own assignments.
        if submission.assignment.instructor != request.user:
            return Response(
                {"detail": "You can only leave feedback on submissions for your own assignments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if hasattr(submission, "feedback"):
            return Response(
                {"detail": "Feedback already exists for this submission."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(submission=submission, instructor=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)