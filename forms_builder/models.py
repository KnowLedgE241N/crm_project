from django.conf import settings
from django.db import models


class FormDefinition(models.Model):
    KIND_GENERIC = "GENERIC"
    KIND_HEALTHCHECK = "HEALTHCHECK"
    KIND_COFFEE = "COFFEE"

    KIND_CHOICES = [
        (KIND_GENERIC, "Generic"),
        (KIND_HEALTHCHECK, "Health Check"),
        (KIND_COFFEE, "Coffee Morning"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    kind = models.CharField(
        max_length=30,
        choices=KIND_CHOICES,
        default=KIND_GENERIC
    )

    is_system = models.BooleanField(default=False)  # 🔒 system form flag

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FormField(models.Model):
    is_displayed = models.BooleanField(default=True)
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    DATE = "date"
    CHOICE = "choice"

    FIELD_TYPES = [
        (TEXT, "Text"),
        (NUMBER, "Number"),
        (DECIMAL, "Decimal"),
        (DATE, "Date"),
        (CHOICE, "Choice"),
    ]

    form = models.ForeignKey(
        FormDefinition,
        on_delete=models.CASCADE,
        related_name="fields"
    )
    key = models.SlugField(max_length=50)
    label = models.CharField(max_length=120)
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        default=TEXT
    )
    required = models.BooleanField(default=False)
    choices_text = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("form", "key")]

    def __str__(self):
        return f"{self.form.name}: {self.label}"


class FormSubmission(models.Model):
    def choices_list(self):
        return [
            (c.strip(), c.strip())
            for c in (self.choices_text or "").splitlines()
            if c.strip()
        ]



    form = models.ForeignKey(
        FormDefinition,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField(default=dict)

    class Meta:
        ordering = ["-submitted_at"]
