from rest_framework import serializers
from .models import Assignment, Enrollment, Submission, Feedback


class AssignmentSerializer(serializers.ModelSerializer):
    instructor_email = serializers.EmailField(source="instructor.email", read_only=True)

    class Meta:
        model = Assignment
        fields = ["id", "title", "description", "instructor_email", "created_at"]
        read_only_fields = ["id", "instructor_email", "created_at"]


class FeedbackSerializer(serializers.ModelSerializer):
    instructor_email = serializers.EmailField(source="instructor.email", read_only=True)

    class Meta:
        model = Feedback
        fields = ["id", "comment", "grade", "instructor_email", "created_at"]
        read_only_fields = ["id", "instructor_email", "created_at"]


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Slim serializer used when an instructor POSTs new feedback."""

    class Meta:
        model = Feedback
        fields = ["comment", "grade"]


class SubmissionSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "assignment_title",
            "student_email",
            "content",
            "submitted_at",
            "feedback",
        ]
        read_only_fields = [
            "id",
            "student_email",
            "assignment_title",
            "submitted_at",
            "feedback",
        ]

    def validate(self, attrs):
        """
        Two business-rule checks before saving a submission:
          1. The student must be enrolled in the assignment they are submitting to.
          2. The student must not have already submitted to this assignment.
        Doing this in the serializer keeps the view thin and the logic testable.
        """
        request = self.context["request"]
        student = request.user
        assignment = attrs["assignment"]

        if not Enrollment.objects.filter(student=student, assignment=assignment).exists():
            raise serializers.ValidationError(
                "You are not enrolled in this assignment."
            )

        if Submission.objects.filter(student=student, assignment=assignment).exists():
            raise serializers.ValidationError(
                "You have already submitted work for this assignment."
            )

        return attrs