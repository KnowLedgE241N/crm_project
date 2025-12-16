from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        STAFF = "STAFF", "Staff"
        VOLUNTEER = "VOLUNTEER", "Volunteer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
