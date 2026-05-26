# Custom DRF permission classes for the Classroom Feedback API.
#
# ───────────────────────────────────────────────────────────────────
# TEACHING COMMENT — READ THIS BEFORE YOU READ THE REST OF THE FILE
# ───────────────────────────────────────────────────────────────────
#
# There are two different questions this file answers:
#
#   1. ROLE-LEVEL: "Is this a person who is allowed into this part of the API?"
#      Example: only an observer should reach the observer branch.
#
#   2. ROW-LEVEL: "Is this exact observer linked to this exact student?"
#      Example: the observer on record can read one student's feedback,
#      but not every student's feedback.
#
# That second check is the important one for this project. The observer
# role alone is too broad, because every observer would look identical
# unless we ask the database for the actual ObserverLink row.
#
# The security bug this prevents is Broken Object Level Authorization
# (BOLA): the classic "change the ID in the URL and see someone else's
# data" problem. The pattern we use here is:
#   1. Load the submission from the database.
#   2. Ask whether this user has a stored relationship to that row.
#   3. Deny access if no matching relationship exists.
#
# In this file:
#   - IsInstructor, IsStudent, IsObserver  -> role check only
#   - CanViewFeedback                      -> role check + ObserverLink check
#
# The most important line is the ObserverLink query inside
# CanViewFeedback.has_object_permission.
# ─────────────────────────────────────────────────────────────────

from rest_framework.permissions import BasePermission
from .models import ObserverLink


class IsInstructor(BasePermission):
    """Grants access only to authenticated users with the INSTRUCTOR role."""

    message = "Only instructors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "INSTRUCTOR"
        )


class IsStudent(BasePermission):
    """Grants access only to authenticated users with the STUDENT role."""

    message = "Only students can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "STUDENT"
        )


class IsObserver(BasePermission):
    """Grants access only to authenticated users with the OBSERVER role.

    Note: this is role-level only. It confirms the user IS an observer,
    but does not confirm which student they are linked to. For row-level
    enforcement, see CanViewFeedback below.
    """

    message = "Only observers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "OBSERVER"
        )


class CanViewFeedback(BasePermission):
    """
    Controls access to GET /api/v1/submissions/{id}/feedback/.

    has_permission  — broad gate: must be authenticated
    has_object_permission — fine gate: depends on role + row-level link

    Who is allowed:
      STUDENT   → only for their own submission
      INSTRUCTOR → only for submissions on their own assignments
      OBSERVER  → only if linked (via ObserverLink) to the submission's student

    Who is denied:
      Any OBSERVER not linked to the submission's student.
      Any STUDENT trying to see another student's submission.
      Any INSTRUCTOR trying to see another instructor's assignment submissions.
    """

    message = "You do not have permission to view this feedback."

    def has_permission(self, request, view):
        # Step 1: must be logged in at all
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # obj is a Submission instance.
        # This method is called after has_permission returns True AND
        # after the object has been fetched from the database.
        #
        # On APIView (which SubmissionFeedbackView inherits from), DRF does
        # NOT call has_object_permission automatically. You must call
        # self.check_object_permissions(request, obj) manually in the view.
        # See classroom/views.py — SubmissionFeedbackView.get() for that call.

        user = request.user

        if user.role == "STUDENT":
            # Students may only see feedback on their own submissions.
            return obj.student == user

        if user.role == "INSTRUCTOR":
            # Instructors may only see feedback on submissions for
            # assignments they created.
            return obj.assignment.instructor == user

        if user.role == "OBSERVER":
            # ── ROW-LEVEL CHECK ────────────────────────────────────────────
            # Checking user.role == "OBSERVER" got us here, but that is
            # only role-level. We still do not know whether THIS observer
            # is linked to THIS submission's student.
            #
            # We query ObserverLink. If a row exists connecting this
            # observer to this submission's student, access is granted.
            # If no row exists — even if the user is a valid observer —
            # access is denied.
            #
            # This means two observers logged in at the same time cannot
            # see each other's students, even though they have the same role.
            return ObserverLink.objects.filter(
                observer=user,
                student=obj.student,
            ).exists()

        # Any role not handled above is denied by default
        return False