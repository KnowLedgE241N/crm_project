from django.conf import settings
from django.db import models

class HealthCheck(models.Model):
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=50, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gp = models.CharField(max_length=150, blank=True)

    systolic = models.IntegerField(null=True, blank=True)
    diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    risk = models.CharField(max_length=100, blank=True)

    # key fields for permissions + progress charts later
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="healthchecks")
    check_date = models.DateField(null=True, blank=True)  # optional, but useful for “progress over time”
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.forename} {self.surname} ({self.created_at:%Y-%m-%d})"
