from django import forms
from django.utils.text import slugify

from .models import FormDefinition, FormField


class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = ["name", "description", "kind"]


class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ["label", "key", "field_type", "required", "choices_text"]
        widgets = {
            "choices_text": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_key(self):
        key = (self.cleaned_data.get("key") or "").strip()
        label = (self.cleaned_data.get("label") or "").strip()

        if not key and label:
            key = slugify(label)[:50]

        return key
