from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that replaces Django's built-in User.

    We always define a custom user model at project start — even when we
    don't need extra fields yet — because swapping AUTH_USER_MODEL after
    the first migration requires a full database reset. It's a one-time
    decision that saves a lot of pain later.

    Changes from the default:
      - email is now the login field (USERNAME_FIELD = "email")
      - email is unique across the table
      - role is a required field choosing between INSTRUCTOR / STUDENT / OBSERVER
    """

    class Role(models.TextChoices):
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"
        OBSERVER = "OBSERVER", "Observer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    # Use email as the primary login credential instead of username.
    # USERNAME_FIELD tells Django's auth backend which field to match the
    # password against during login.
    USERNAME_FIELD = "email"

    # AbstractUser still requires a username column — we keep it but
    # auto-populate it in the seed command so users never have to set it.
    REQUIRED_FIELDS = ["username", "role"]

    def __str__(self):
        return f"{self.email} ({self.role})"