from django import forms
from .models import HealthCheck
from django.forms.widgets import DateInput

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

class DiabetesRiskForm(forms.Form):

    # --- Identity ---
    forename = forms.CharField(max_length=100, label="Forename")
    surname = forms.CharField(max_length=100, label="Surname")

    # --- Demographics ---
    gender = forms.ChoiceField(
        choices=[("F", "Female"), ("M", "Male")],
        widget=forms.RadioSelect,
        label="Gender",
    )

    ethnicity = forms.ChoiceField(
        choices=[("WHITE", "Only white European"), ("OTHER", "Other ethnic group")],
        widget=forms.RadioSelect,
        label="Ethnicity",
    )

    postcode = forms.CharField(max_length=20, required=False, label="Postcode")
    gp = forms.CharField(max_length=150, required=False, label="GP")

    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=DateInput(attrs={
            "type": "date",
            "class": "form-control",
        }),
    )



    # --- Vitals ---
    systolic = forms.IntegerField(required=False, label="Systolic (mmHg)")
    diastolic = forms.IntegerField(required=False, label="Diastolic (mmHg)")
    pulse = forms.IntegerField(required=False, label="Pulse (bpm)")

    # --- Measurements (BMI derived) ---
    waist_cm = forms.FloatField(label="Waist circumference (cm)")
    height_cm = forms.IntegerField(label="Height (cm)")
    weight_kg = forms.FloatField(label="Weight (kg)")

    # --- Diabetes risk questions ---
    family_history = forms.ChoiceField(
        choices=[("YES", "Yes"), ("NO", "No")],
        widget=forms.RadioSelect,
        label="Do you have a parent/sibling/child with Type 1 or Type 2 diabetes?",
    )

    high_bp = forms.ChoiceField(
        choices=[("YES", "Yes"), ("NO", "No")],
        widget=forms.RadioSelect,
        label="Have you been given medicine for high blood pressure OR told you have high blood pressure?",
    )
