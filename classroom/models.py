from django.db import models
from django.conf import settings


class Assignment(models.Model):
    """A piece of work set by an Instructor."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments_created",
        limit_choices_to={"role": "INSTRUCTOR"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """Records that a Student is enrolled in an Assignment."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "STUDENT"},
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    class Meta:
        unique_together = ("student", "assignment")

    def __str__(self):
        return f"{self.student.email} → {self.assignment.title}"


class Submission(models.Model):
    """A student's submitted work for one assignment."""

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={"role": "STUDENT"},
    )
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One submission per student per assignment
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"{self.student.email} → {self.assignment.title}"


class Feedback(models.Model):
    """Feedback left by an Instructor on a Submission."""

    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback_given",
        limit_choices_to={"role": "INSTRUCTOR"},
    )
    comment = models.TextField()
    grade = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback on {self.submission}"


class ObserverLink(models.Model):
    """
    Links exactly one Observer to exactly one Student.

    This table is what makes row-level permission possible for the Observer role.
    Without it, all we could check is: "Is this user an Observer?"
    With it, we can check: "Is this Observer linked to THIS student?"

    The difference matters enormously in security terms. Two observers must
    never be able to see each other's students — this table is the enforcement
    mechanism. See classroom/permissions.py for the teaching comment that
    explains why this distinction is the #1 API security mistake in practice.
    """

    observer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="observer_link",
        limit_choices_to={"role": "OBSERVER"},
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="observed_by",
        limit_choices_to={"role": "STUDENT"},
    )

    def __str__(self):
        return f"{self.observer.email} observes {self.student.email}"
