"""
Management command: python manage.py seed

Populates the database with the three demo accounts and enough classroom
data to demonstrate every endpoint live in Postman.

Usage:
    python manage.py seed           # safe to re-run; skips existing records
    python manage.py seed --reset   # wipes classroom data first, then re-seeds

Seeded accounts:
    instructor@demo.dev  /  Demo@1234
    student@demo.dev     /  Demo@1234
    observer@demo.dev    /  Demo@1234
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from classroom.models import Assignment, Enrollment, Submission, Feedback, ObserverLink


INSTRUCTOR_EMAIL = "instructor@demo.dev"
STUDENT_EMAIL    = "student@demo.dev"
OBSERVER_EMAIL   = "observer@demo.dev"
DEMO_PASSWORD    = "Demo@1234"


class Command(BaseCommand):
    help = "Seed the database with demo users and classroom data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all non-superuser accounts and classroom data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        if options["reset"]:
            self.stdout.write("Clearing existing data...")
            Feedback.objects.all().delete()
            Submission.objects.all().delete()
            Enrollment.objects.all().delete()
            ObserverLink.objects.all().delete()
            Assignment.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write("Done.\n")

        # ── Users ──────────────────────────────────────────────────────────
        self.stdout.write("Creating users...")

        instructor, _ = User.objects.get_or_create(
            email=INSTRUCTOR_EMAIL,
            defaults={
                "username": "instructor",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "role": User.Role.INSTRUCTOR,
            },
        )
        instructor.set_password(DEMO_PASSWORD)
        instructor.save()

        student, _ = User.objects.get_or_create(
            email=STUDENT_EMAIL,
            defaults={
                "username": "student",
                "first_name": "Alan",
                "last_name": "Turing",
                "role": User.Role.STUDENT,
            },
        )
        student.set_password(DEMO_PASSWORD)
        student.save()

        observer, _ = User.objects.get_or_create(
            email=OBSERVER_EMAIL,
            defaults={
                "username": "observer",
                "first_name": "Grace",
                "last_name": "Hopper",
                "role": User.Role.OBSERVER,
            },
        )
        observer.set_password(DEMO_PASSWORD)
        observer.save()

        # ── Assignments ────────────────────────────────────────────────────
        self.stdout.write("Creating assignments...")

        assignment1, _ = Assignment.objects.get_or_create(
            title="Introduction to REST APIs",
            defaults={
                "description": (
                    "Build a simple REST API using Django REST Framework. "
                    "Your API should expose at least three endpoints with "
                    "proper HTTP verbs and status codes."
                ),
                "instructor": instructor,
            },
        )

        assignment2, _ = Assignment.objects.get_or_create(
            title="JWT Authentication Deep Dive",
            defaults={
                "description": (
                    "Extend your REST API to add JWT-based authentication. "
                    "Implement login, token refresh, and at least one "
                    "protected endpoint that returns different data depending "
                    "on the authenticated user's role."
                ),
                "instructor": instructor,
            },
        )

        assignment3, _ = Assignment.objects.get_or_create(
            title="Securing Object-Level Access",
            defaults={
                "description": (
                    "Use row-level authorization checks to ensure users can only "
                    "access data rows they are explicitly linked to in the database."
                ),
                "instructor": instructor,
            },
        )

        # ── Enrollments ────────────────────────────────────────────────────
        self.stdout.write("Enrolling student...")

        Enrollment.objects.get_or_create(student=student, assignment=assignment1)
        Enrollment.objects.get_or_create(student=student, assignment=assignment2)
        Enrollment.objects.get_or_create(student=student, assignment=assignment3)

        # ── Submissions ────────────────────────────────────────────────────
        self.stdout.write("Creating submissions...")

        sub1, _ = Submission.objects.get_or_create(
            assignment=assignment1,
            student=student,
            defaults={
                "content": (
                    "I built a Books API with endpoints for listing, creating, "
                    "retrieving, updating, and deleting books. Each endpoint "
                    "returns the correct HTTP status code. I used ModelViewSet "
                    "to keep the code concise."
                ),
            },
        )

        sub2, _ = Submission.objects.get_or_create(
            assignment=assignment2,
            student=student,
            defaults={
                "content": (
                    "I integrated simplejwt into my Books API. "
                    "POST /auth/login/ returns access and refresh tokens. "
                    "POST /auth/refresh/ exchanges a refresh token for a new "
                    "access token. GET /books/ now requires a valid Bearer token."
                ),
            },
        )

        sub3, _ = Submission.objects.get_or_create(
            assignment=assignment3,
            student=student,
            defaults={
                "content": (
                    "I implemented object-level checks using an observer-to-student "
                    "link table so one observer cannot access another student's records "
                    "by changing IDs in the URL."
                ),
            },
        )

        # ── Feedback ───────────────────────────────────────────────────────
        self.stdout.write("Creating feedback...")

        Feedback.objects.get_or_create(
            submission=sub1,
            defaults={
                "instructor": instructor,
                "comment": (
                    "Excellent work, Alan! Your endpoint design is clean and "
                    "your status codes are correct. One suggestion: add "
                    "pagination to the list endpoint — what happens when you "
                    "have 10,000 books?"
                ),
                "grade": "A",
            },
        )

        Feedback.objects.get_or_create(
            submission=sub2,
            defaults={
                "instructor": instructor,
                "comment": (
                    "Great implementation of the refresh flow. In production, "
                    "store tokens in httpOnly cookies rather than localStorage "
                    "to protect against XSS attacks."
                ),
                "grade": "A-",
            },
        )

        Feedback.objects.get_or_create(
            submission=sub3,
            defaults={
                "instructor": instructor,
                "comment": (
                    "Great security thinking. You correctly separated role-level from "
                    "row-level checks and validated access through an explicit link row."
                ),
                "grade": "A",
            },
        )

        # ── Observer link ──────────────────────────────────────────────────
        self.stdout.write("Creating observer link...")

        ObserverLink.objects.get_or_create(observer=observer, student=student)

        # ── Summary ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            "\n✓ Database seeded successfully!\n"
            "\nDemo accounts:\n"
            f"  Instructor : {INSTRUCTOR_EMAIL}  /  {DEMO_PASSWORD}\n"
            f"  Student    : {STUDENT_EMAIL}     /  {DEMO_PASSWORD}\n"
            f"  Observer   : {OBSERVER_EMAIL}    /  {DEMO_PASSWORD}\n"
            "\nData:\n"
            "  3 assignments, 3 enrollments, 3 submissions, 3 feedback records\n"
            "  1 observer → student link\n"
        ))