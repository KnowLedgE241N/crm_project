import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.utils import can_manage_forms, can_fill_forms, can_view_all
from .models import FormDefinition, FormField, FormSubmission
from .forms import FormDefinitionForm
from .utils import build_dynamic_form


@login_required
def forms_page(request):
    # Everyone logged in (including volunteers) can see forms
    qs = FormDefinition.objects.all().order_by("-created_at")
    return render(request, "forms_builder/forms_page.html", {"forms": qs})



@login_required
def form_create(request):
    # Volunteers cannot create forms
    if not can_manage_forms(request.user):
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
    # Volunteers ARE allowed to fill
    if not can_fill_forms(request.user):
        raise Http404()

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
            # after submit, volunteer should not go to results page
            # so we redirect them back to the fill page
            if can_manage_forms(request.user):
                return redirect("form_results", pk=form_def.id)
            return redirect("form_fill", pk=form_def.id)
    else:
        form = DynamicForm()

    return render(request, "forms_builder/form_fill.html", {
        "form_def": form_def,
        "form": form,
        "fields_count": fields.count(),
    })


@login_required
def form_results(request, pk: int):
    # Volunteers cannot view results
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    fields = FormField.objects.filter(form=form_def).order_by("order", "id")

    qs = FormSubmission.objects.filter(form=form_def).order_by("-submitted_at")

    # Optional: If you still want staff to only see their own submissions,
    # uncomment this. Otherwise, all non-volunteers see all submissions.
    # if not can_view_all(request.user):
    #     qs = qs.filter(submitted_by=request.user)

    q = (request.GET.get("q") or "").strip().lower()
    submissions = list(qs[:500])

    if q:
        submissions = [s for s in submissions if any(q in str(v).lower() for v in s.answers.values())]

    column_keys = [f.key for f in fields]
    column_labels = [f.label for f in fields]

    rows = [{"answers": s.answers} for s in submissions]

    return render(request, "forms_builder/form_results.html", {
        "form_def": form_def,
        "q": request.GET.get("q", ""),
        "column_keys": column_keys,
        "column_labels": column_labels,
        "rows": rows,
    })


@login_required
@require_POST
def form_delete(request, pk: int):
    # Volunteers cannot delete forms
    if not can_manage_forms(request.user):
        raise Http404()

    form_def = get_object_or_404(FormDefinition, pk=pk)
    form_def.delete()
    return redirect("forms_page")


@login_required
@require_POST
def fields_reorder(request, pk: int):
    # Volunteers cannot reorder questions
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
