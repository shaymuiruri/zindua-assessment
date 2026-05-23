# Custom DRF permission classes for the Classroom Feedback API.
#
# ───────────────────────────────────────────────────────────────────
# TEACHING COMMENT — READ THIS BEFORE YOU READ THE REST OF THE FILE
# ───────────────────────────────────────────────────────────────────
#
# There are two levels at which you can restrict access to data:
#
#   1. ROLE-LEVEL:  "Only Observers may reach this endpoint."
#                   You check request.user.role == 'OBSERVER'. Done.
#
#   2. ROW-LEVEL:   "Only the Observer linked to THIS student may see
#                   THIS specific piece of data."
#                   A role check alone is not enough. You must query the
#                   database — ObserverLink in our case — and ask:
#                   does a row exist connecting this observer to the
#                   student who owns the requested data?
#
# Why does this distinction matter in the real world?
#
#     Think of a bank. "Only account holders can see account data" is
#     role-level. "Only YOU can see YOUR account balance" is row-level.
#     Most real-world API security bugs come from doing the role check
#     and forgetting the row check.
#
#     The OWASP API Security Top 10 calls this mistake "Broken Object
#     Level Authorization" (BOLA) — and it is consistently ranked the
#     #1 vulnerability in API systems. It's the bug behind incidents
#     like "I could see other users' orders by changing the ID in the
#     URL."
#
#     The fix is always the same pattern:
#         1. Fetch the object from the database.
#         2. Ask: does the authenticated user have an explicit, stored
#            relationship to THIS object?
#         3. If no row proves it — deny access.
#
# In this file:
#   - IsInstructor, IsStudent, IsObserver  -> role-level only
#   - CanViewFeedback                      -> role-level + row-level
#
# Read CanViewFeedback.has_object_permission carefully and notice
# where the database query happens and why.
# ───────────────────────────────────────────────────────────────────

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