from django import forms
from .models import FormDefinition, FormField


class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = ["name", "description"]


class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ["order", "label", "key", "field_type", "required", "choices_text"]
        widgets = {
            "choices_text": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_key(self):
        key = (self.cleaned_data["key"] or "").strip().lower()
        key = key.replace(" ", "_")
        return key
