from django.conf import settings
from django.db import models

class DiabetesRiskAssessment(models.Model):
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diabetes_risk_assessments",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    forename = models.CharField(max_length=100, blank=True, default="")
    surname = models.CharField(max_length=100, blank=True, default="")
    postcode = models.CharField(max_length=20, blank=True, default="")
    gp = models.CharField(max_length=150, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=10, blank=True, default="")
    ethnicity = models.CharField(max_length=50, blank=True, default="")

    systolic = models.IntegerField(null=True, blank=True)
    diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)

    waist_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.IntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    total_score = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.forename} {self.surname} ({self.submitted_at:%Y-%m-%d})"


class CoffeeMorning(models.Model):
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="coffee_mornings",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    forename = models.CharField(max_length=100, blank=True, default="")
    surname = models.CharField(max_length=100, blank=True, default="")
    postcode = models.CharField(max_length=20, blank=True, default="")
    gp = models.CharField(max_length=150, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=10, blank=True, default="")
    ethnicity = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Coffee Morning"
        verbose_name_plural = "Coffee Mornings"

    def __str__(self):
        return f"{self.forename} {self.surname} ({self.submitted_at:%Y-%m-%d})"
