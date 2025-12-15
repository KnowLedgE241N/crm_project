from django import forms
from .models import FormField

def build_dynamic_form(fields):
    """
    fields: queryset/list of FormField
    returns: a Django Form class
    """
    form_fields = {}

    for f in fields:
        common = {"label": f.label, "required": f.required}

        if f.field_type == FormField.TEXT:
            form_fields[f.key] = forms.CharField(**common)

        elif f.field_type == FormField.NUMBER:
            form_fields[f.key] = forms.IntegerField(**common)

        elif f.field_type == FormField.DECIMAL:
            form_fields[f.key] = forms.DecimalField(**common)

        elif f.field_type == FormField.DATE:
            form_fields[f.key] = forms.DateField(
                **common,
                widget=forms.DateInput(attrs={"type": "date"})
            )

        elif f.field_type == FormField.CHOICE:
            choices = f.choices_list()
            form_fields[f.key] = forms.ChoiceField(**common, choices=choices)

        else:
            form_fields[f.key] = forms.CharField(**common)

    return type("DynamicForm", (forms.Form,), form_fields)
