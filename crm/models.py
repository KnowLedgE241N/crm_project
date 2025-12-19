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

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="healthchecks"
    )
    check_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.forename} {self.surname} ({self.created_at:%Y-%m-%d})"



class DiabetesRiskAssessment(models.Model):
    # ---- Identity ----
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)

    gender = models.CharField(max_length=10)          # F / M
    ethnicity = models.CharField(max_length=20)       # WHITE / OTHER
    postcode = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField()
    gp = models.CharField(max_length=150, blank=True)

    # ---- Vitals ----
    systolic = models.IntegerField(null=True, blank=True)
    diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)

    # ---- Measurements ----
    waist_cm = models.FloatField()
    height_cm = models.IntegerField()
    weight_kg = models.FloatField()
    bmi = models.FloatField()

    # ---- Diabetes risk inputs ----
    family_history = models.CharField(max_length=5)   # YES / NO
    high_bp = models.CharField(max_length=5)          # YES / NO

    # ---- Scoring breakdown ----
    age_score = models.IntegerField()
    gender_score = models.IntegerField()
    ethnicity_score = models.IntegerField()
    family_history_score = models.IntegerField()
    waist_score = models.IntegerField()
    bmi_score = models.IntegerField()
    bp_score = models.IntegerField()

    total_score = models.IntegerField()

    # ---- Hybrid JSON snapshot ----
    json_path = models.CharField(max_length=300, blank=True)

    # ---- Metadata ----
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diabetes_risk_assessments",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.forename} {self.surname} ({self.total_score}"

