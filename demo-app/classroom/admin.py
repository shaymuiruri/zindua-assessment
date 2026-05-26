from django.contrib import admin
from .models import Assignment, Enrollment, Submission, Feedback, ObserverLink


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "instructor", "created_at"]
    list_filter = ["instructor"]
    search_fields = ["title", "instructor__email"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment"]
    list_filter = ["assignment"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment", "submitted_at"]
    list_filter = ["assignment"]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["submission", "instructor", "grade", "created_at"]


@admin.register(ObserverLink)
class ObserverLinkAdmin(admin.ModelAdmin):
    list_display = ["observer", "student"]
