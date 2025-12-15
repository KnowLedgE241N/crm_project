from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

from accounts.utils import can_add_records, can_view_all
from .models import FormDefinition, FormField
from .forms import FormFieldForm


@login_required
def questions_list(request, pk: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)

    # Optional restriction: only creator or admin can edit questions
    if not can_view_all(request.user) and form_def.created_by != request.user:
        raise Http404()

    fields = FormField.objects.filter(form=form_def).order_by("order", "id")
    return render(request, "forms_builder/questions_list.html", {
        "form_def": form_def,
        "fields": fields,
    })


@login_required
def question_add(request, pk: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)

    if not can_view_all(request.user) and form_def.created_by != request.user:
        raise Http404()

    if request.method == "POST":
        form = FormFieldForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.form = form_def
            obj.save()
            return redirect("questions_list", pk=form_def.id)
    else:
        form = FormFieldForm()

    return render(request, "forms_builder/question_form.html", {
        "form_def": form_def,
        "form": form,
        "mode": "Add",
    })


@login_required
def question_edit(request, pk: int, field_id: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)
    field = get_object_or_404(FormField, pk=field_id, form=form_def)

    if not can_view_all(request.user) and form_def.created_by != request.user:
        raise Http404()

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
        "mode": "Edit",
    })


@login_required
def question_delete(request, pk: int, field_id: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)
    field = get_object_or_404(FormField, pk=field_id, form=form_def)

    if not can_view_all(request.user) and form_def.created_by != request.user:
        raise Http404()

    if request.method == "POST":
        field.delete()
        return redirect("questions_list", pk=form_def.id)

    return render(request, "forms_builder/question_delete.html", {
        "form_def": form_def,
        "field": field,
    })
