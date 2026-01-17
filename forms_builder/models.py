from datetime import date
from django.conf import settings
from django.db import models


class FormDefinition(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # optional but useful if you want to lock “system forms” later
    # is_system = models.BooleanField(default=False)

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
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="form_submissions"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Dynamic answers (DB-only approach)
    answers = models.JSONField(default=dict)

    # Indexed identity fields for global search + “person activity”
    forename = models.CharField(max_length=120, blank=True, default="")
    surname = models.CharField(max_length=120, blank=True, default="")
    postcode = models.CharField(max_length=20, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.form.name} submission #{self.id}"

    def sync_identity_from_answers(self):
        ans = self.answers or {}

        self.forename = (str(ans.get("forename", "")) or "").strip().lower()
        self.surname = (str(ans.get("surname", "")) or "").strip().lower()
        self.postcode = (str(ans.get("postcode", "")) or "").strip().lower()

        dob = ans.get("date_of_birth") or ans.get("dob") or ""
        if isinstance(dob, str) and dob:
            try:
                self.date_of_birth = date.fromisoformat(dob)
            except Exception:
                self.date_of_birth = None
        else:
            self.date_of_birth = None

    def save(self, *args, **kwargs):
        self.sync_identity_from_answers()
        super().save(*args, **kwargs)
