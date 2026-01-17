import json
from datetime import date, datetime
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.utils import can_manage_forms, can_fill_forms
from .models import FormDefinition, FormField, FormSubmission
from .forms import FormDefinitionForm
from .utils import build_dynamic_form


def _json_safe_answers(cleaned):
    out = {}
    for k, v in (cleaned or {}).items():
        if isinstance(v, (date, datetime)):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            # Convert Decimal safely to float for JSON
            try:
                out[k] = float(v)
            except Exception:
                out[k] = None
        else:
            out[k] = v
    return out


@login_required
def forms_page(request):
    qs = FormDefinition.objects.all().order_by("order", "created_at", "id")
    return render(request, "forms_builder/forms_page.html", {
        "forms": qs,
        "can_manage": can_manage_forms(request.user),
    })


@login_required
def form_create(request):
    if not can_manage_forms(request.user):
        raise Http404()

    if request.method == "POST":
        form = FormDefinitionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            max_order = FormDefinition.objects.aggregate(Max("order")).get("order__max")
            obj.order = (max_order or 0) + 1
            obj.save()
            return redirect("forms_page")
    else:
        form = FormDefinitionForm()

    return render(request, "forms_builder/form_create.html", {"form": form})


@login_required
def form_fill(request, pk: int):
    if not can_fill_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")
    DynamicForm = build_dynamic_form(fields)

    # ALWAYS define form
    form = DynamicForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        answers = _json_safe_answers(form.cleaned_data)

        submission = FormSubmission.objects.create(
            form=form_def,
            submitted_by=request.user,
            answers=answers,
        )

        # OPTIONAL: sync certain forms into CRM models for analytics
        try:
            if form_def.id == 8:
                from crm.sync import sync_submission_to_diabetes_risk
                sync_submission_to_diabetes_risk(submission)
            elif (form_def.name or "").strip().lower() == "coffee morning":
                from crm.sync import sync_submission_to_coffee_morning
                sync_submission_to_coffee_morning(submission)
        except Exception:
            # Keep form submission working even if sync fails
            pass

        # Volunteers go back to fill; staff/admin can go to results
        if can_manage_forms(request.user):
            return redirect("form_results", pk=form_def.id)
        return redirect("form_fill", pk=form_def.id)

    return render(request, "forms_builder/form_fill.html", {
        "form_def": form_def,
        "form": form,
        "fields_count": fields.count(),
    })


@login_required
def form_results(request, pk: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")

    qs = FormSubmission.objects.filter(form=form_def).order_by("-submitted_at")

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(forename__icontains=q) |
            Q(surname__icontains=q) |
            Q(postcode__icontains=q) |
            Q(answers__icontains=q)
        )

    submissions = list(qs[:800])

    column_keys = [f.key for f in fields]
    column_labels = [f.label for f in fields]
    rows = [{"sub": s, "answers": s.answers} for s in submissions]

    return render(request, "forms_builder/form_results.html", {
        "form_def": form_def,
        "q": q,
        "column_keys": column_keys,
        "column_labels": column_labels,
        "rows": rows,
    })


@login_required
@require_POST
def form_delete(request, pk: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    form_def.delete()
    return redirect("forms_page")


@login_required
@require_POST
def fields_reorder(request, pk: int):
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)

    data = json.loads(request.body.decode("utf-8"))
    ids = data.get("ids", [])

    try:
        ids_int = [int(x) for x in ids]
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid ids"}, status=400)

    id_to_pos = {fid: idx for idx, fid in enumerate(ids_int)}
    qs = FormField.objects.filter(form=form_def, id__in=id_to_pos.keys())

    for f in qs:
        f.order = id_to_pos[f.id]

    FormField.objects.bulk_update(qs, ["order"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def forms_reorder(request):
    if not can_manage_forms(request.user):
        raise Http404()

    data = json.loads(request.body.decode("utf-8"))
    ids = data.get("ids", [])

    try:
        ids_int = [int(x) for x in ids]
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid ids"}, status=400)

    id_to_pos = {fid: idx for idx, fid in enumerate(ids_int)}
    qs = FormDefinition.objects.filter(id__in=id_to_pos.keys())

    for f in qs:
        f.order = id_to_pos[f.id]

    FormDefinition.objects.bulk_update(qs, ["order"])
    return JsonResponse({"ok": True})
