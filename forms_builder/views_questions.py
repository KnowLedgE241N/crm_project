from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

from accounts.utils import can_manage_forms
from .models import FormDefinition, FormField
from .forms import FormFieldForm


@login_required
def questions_list(request, pk: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")

    return render(request, "forms_builder/builder.html", {
        "form_def": form_def,
        "fields": fields,
    })


@login_required
def question_add(request, pk: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)

    if request.method == "POST":
        form = FormFieldForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.form = form_def

            max_order = FormField.objects.filter(form=form_def).aggregate(m=Max("order"))["m"]
            obj.order = (max_order + 1) if max_order is not None else 0

            obj.save()
            return redirect("questions_list", pk=form_def.id)
    else:
        form = FormFieldForm()

    return render(request, "forms_builder/question_form.html", {
        "form_def": form_def,
        "form": form,
        "mode": "add",
    })


@login_required
def question_edit(request, pk: int, field_id: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    field = get_object_or_404(FormField, pk=field_id, form=form_def)

    if request.method == "POST":
        form = FormFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            return redirect("questions_list", pk=form_def.id)
    else:
        form = FormFieldForm(instance=field)

    return render(request, "forms_builder/question_form.html", {
        "form_def": form_def,
        "form": form,
        "mode": "edit",
        "field": field,
    })


@login_required
def question_delete(request, pk: int, field_id: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    field = get_object_or_404(FormField, pk=field_id, form=form_def)

    if request.method == "POST":
        field.delete()
        return redirect("questions_list", pk=form_def.id)

    return render(request, "forms_builder/question_delete.html", {
        "form_def": form_def,
        "field": field,
    })
