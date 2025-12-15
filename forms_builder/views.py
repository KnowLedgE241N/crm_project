from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.db.models import Q

from accounts.utils import can_view_all, can_add_records
from .models import FormDefinition, FormField, FormSubmission
from .forms import FormDefinitionForm
from .utils import build_dynamic_form


@login_required
def forms_page(request):
    qs = FormDefinition.objects.all().order_by("-created_at")
    if not can_view_all(request.user):
        qs = qs.filter(created_by=request.user)
    return render(request, "forms_builder/forms_page.html", {"forms": qs})


@login_required
def form_create(request):
    if not can_add_records(request.user):
        raise Http404()

    if request.method == "POST":
        form = FormDefinitionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect("forms_page")
    else:
        form = FormDefinitionForm()

    return render(request, "forms_builder/form_create.html", {"form": form})


@login_required
def form_fill(request, pk: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")

    DynamicForm = build_dynamic_form(fields)

    if request.method == "POST":
        form = DynamicForm(request.POST)
        if form.is_valid():
            FormSubmission.objects.create(
                form=form_def,
                submitted_by=request.user,
                answers=form.cleaned_data,
            )
            return redirect("form_results", pk=form_def.id)
    else:
        form = DynamicForm()

    return render(request, "forms_builder/form_fill.html", {
        "form_def": form_def,
        "form": form,
        "fields_count": fields.count(),
    })


@login_required
def form_results(request, pk: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")

    # Role-safe: staff only see submissions they made; admins/managers see all
    qs = FormSubmission.objects.filter(form=form_def)
    if not can_view_all(request.user):
        qs = qs.filter(submitted_by=request.user)

    # Simple search: checks if query appears in ANY value in answers
    q = (request.GET.get("q") or "").strip().lower()
    if q:
        # For MVP: do a Python filter after fetching a reasonable slice
        raw = list(qs[:500])
        raw = [s for s in raw if any(q in str(v).lower() for v in s.answers.values())]
        submissions = raw
    else:
        submissions = list(qs[:200])

    column_keys = [f.key for f in fields]
    column_labels = [f.label for f in fields]

    # Build rows for template
    rows = []
    for s in submissions:
        rows.append({
            "id": s.id,
            "submitted_at": s.submitted_at,
            "submitted_by": s.submitted_by,
            "answers": s.answers,
        })

    return render(request, "forms_builder/form_results.html", {
        "form_def": form_def,
        "q": request.GET.get("q", ""),
        "column_keys": column_keys,
        "column_labels": column_labels,
        "rows": rows,
    })
