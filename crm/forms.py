from django import forms
from .models import HealthCheck

class HealthCheckForm(forms.ModelForm):
    class Meta:
        model = HealthCheck
        # include the fields users should fill in (exclude created_by/created_at)
        fields = [
            "forename", "surname", "gender", "ethnicity", "postcode", "age", "gp",
            "systolic", "diastolic", "pulse", "bmi", "risk",
            "check_date",
        ]
        widgets = {
            "check_date": forms.DateInput(attrs={"type": "date"}),
        }
