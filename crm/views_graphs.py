import json
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404

from accounts.utils import can_access_tables  # reuse same gate as Tables
from forms_builder.models import FormDefinition, FormField, FormSubmission


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


@login_required
def graphs_page(request):
    if not can_access_tables(request.user):
        raise Http404()

    # Pick default form: try RiskAssessment by name, else first form
    risk = FormDefinition.objects.filter(name__iexact="RiskAssessment").first()
    form_id = request.GET.get("form_id")
    if form_id:
        form_def = get_object_or_404(FormDefinition, pk=form_id)
    else:
        form_def = risk or FormDefinition.objects.order_by("id").first()

    if not form_def:
        return render(request, "crm/graphs.html", {
            "forms": [],
            "form_def": None,
            "fields": [],
        })

    forms = FormDefinition.objects.order_by("-created_at")

    fields = list(FormField.objects.filter(form=form_def).order_by("order", "id"))
    field_choices = [{"key": f.key, "label": f.label} for f in fields]

    return render(request, "crm/graphs.html", {
        "forms": forms,
        "form_def": form_def,
        "fields": field_choices,
    })


@login_required
def graphs_data(request):
    if not can_access_tables(request.user):
        raise Http404()

    form_id = request.GET.get("form_id")
    x_key = request.GET.get("x")
    y_key = request.GET.get("y")

    if not (form_id and x_key and y_key):
        return JsonResponse({"ok": False, "error": "Missing params"}, status=400)

    form_def = get_object_or_404(FormDefinition, pk=form_id)

    qs = FormSubmission.objects.filter(form=form_def).order_by("-submitted_at")[:1500]

    points = []
    for s in qs:
        ans = s.answers or {}
        x = _to_float(ans.get(x_key))
        y = _to_float(ans.get(y_key))
        if x is None or y is None:
            continue
        points.append({"x": x, "y": y})

    return JsonResponse({
        "ok": True,
        "points": points,
        "count": len(points),
    })
