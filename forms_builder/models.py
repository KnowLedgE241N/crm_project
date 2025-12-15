from django.conf import settings
from django.db import models
from crm.table_registry import TABLES


from django.conf import settings
from django.db import models

storage_key = models.CharField(max_length=50, blank=True, default="healthchecks")

class FormDefinition(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_definitions")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FormField(models.Model):
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

    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="fields")
    key = models.SlugField(max_length=50, help_text="Unique key like: bmi, diastolic, postcode")
    label = models.CharField(max_length=120)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default=TEXT)
    required = models.BooleanField(default=False)
    choices_text = models.TextField(blank=True, help_text="For Choice type: one option per line")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("form", "key")]
        ordering = ["order", "id"]

    def choices_list(self):
        return [(c.strip(), c.strip()) for c in self.choices_text.splitlines() if c.strip()]

    def __str__(self):
        return f"{self.form.name}: {self.label}"


class FormSubmission(models.Model):
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField(default=dict)  # works on SQLite too

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.form.name} submission #{self.id}"

