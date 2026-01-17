from django import forms


def build_dynamic_form(fields):
    """
    fields: queryset/list of FormField
    returns: a Django Form class
    """

    class DynamicForm(forms.Form):
        pass

    for f in fields:
        kwargs = {"label": f.label, "required": f.required}

        if f.field_type == "text":
            field = forms.CharField(**kwargs)
        elif f.field_type == "number":
            field = forms.IntegerField(**kwargs)
        elif f.field_type == "decimal":
            field = forms.DecimalField(**kwargs)
        elif f.field_type == "date":
            field = forms.DateField(
                **kwargs,
                widget=forms.DateInput(attrs={"type": "date"})
            )
        elif f.field_type == "choice":
            choices = f.choices_list()
            field = forms.ChoiceField(choices=choices, **kwargs)
        else:
            field = forms.CharField(**kwargs)

        DynamicForm.base_fields[f.key] = field

    return DynamicForm
