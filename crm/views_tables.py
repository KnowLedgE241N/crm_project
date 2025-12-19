from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.urls import reverse
from .table_registry import TABLES
from django.shortcuts import render, redirect, get_object_or_404
from accounts.utils import can_view_all, can_add_records, can_manage_record
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, date
from django.db import models
from accounts.utils import can_access_tables
from types import SimpleNamespace
from forms_builder.models import FormDefinition, FormField, FormSubmission

@login_required
def tables_page(request):
    if not can_access_tables(request.user):
        raise Http404()

    # -----------------------------
    # Build dropdown: model tables + forms
    # -----------------------------
    dropdown = list(TABLES.values())  # your TableConfig objects

    form_defs = FormDefinition.objects.all().order_by("-created_at")
    for f in form_defs:
        dropdown.append(SimpleNamespace(
            key=f"form:{f.id}",
            label=f.name,
            form_id=f.id
        ))

    if not dropdown:
        raise Http404("No tables/forms available")

    # Selected key
    selected_key = request.GET.get("table") or dropdown[0].key

    # Shared filters
    q = (request.GET.get("q") or "").strip()
    date_filter = request.GET.get("date") or "all"

    # -----------------------------
    # CASE A) FORM RESULTS (JSON)
    # -----------------------------
    if str(selected_key).startswith("form:"):
        try:
            form_id = int(str(selected_key).split(":", 1)[1])
        except (ValueError, IndexError):
            raise Http404("Invalid form key")

        form_def = get_object_or_404(FormDefinition, id=form_id)
        selected = SimpleNamespace(
            key=f"form:{form_def.id}",
            label=f"Form: {form_def.name}",
            form_id=form_def.id
        )

        fields = list(FormField.objects.filter(form=form_def).order_by("order", "id"))
        column_keys = [f.key for f in fields]
        column_names = [f.label for f in fields]

        subs = FormSubmission.objects.filter(form=form_def)

        # Row-level visibility for staff (optional but matches your style)
        if not can_view_all(request.user) and hasattr(FormSubmission, "submitted_by_id"):
            subs = subs.filter(submitted_by=request.user)

        # Date filter (FormSubmission has created_at DateTimeField)
        if date_filter != "all":
            today = timezone.localdate()

            if date_filter == "today":
                start = today
            elif date_filter == "week":
                start = today - timedelta(days=7)
            elif date_filter == "month":
                start = date(today.year, today.month, 1)
            elif date_filter == "30d":
                start = today - timedelta(days=30)
            else:
                start = None

            if start:
                subs = subs.filter(submitted_at__date__gte=start)


        # Search in JSON + username
        if q:
            subs = subs.filter(
                Q(answers__icontains=q) |
                Q(submitted_by__username__icontains=q)
            )

        subs = subs.order_by("-id")[:200]

        # Build rows for template
        rows = []
        for s in subs:
            rows.append({
                "answers": s.answers or {},
                "submitted_by": getattr(s.submitted_by, "username", "") if s.submitted_by else "",
                "submitted_at": s.submitted_at,
            })

        # Add meta cols
        column_names += ["Submitted By", "Submitted At"]
        column_keys += ["__submitted_by", "__submitted_at"]


        context = {
            "tables": dropdown,
            "selected": selected,
            "rows": rows,
            "column_names": column_names,
            "column_keys": column_keys,
            "q": q,
            "date_filter": date_filter,
            "can_add": False,      # we don’t add submissions from Tables page
            "mode": "form",
        }

        template_name = "crm/tables.html"
        if request.headers.get("HX-Request") == "true":
            template_name = "crm/partials/table_tbody.html"

        return render(request, template_name, context)

    # -----------------------------
    # CASE B) MODEL TABLE (existing behaviour)
    # -----------------------------
    cfg = _get_table_or_404(selected_key)
    selected = cfg

    qs = cfg.model.objects.all()

    # Row-level visibility for staff
    if not can_view_all(request.user) and hasattr(cfg.model, "created_by"):
        qs = qs.filter(created_by=request.user)

    # ---- SEARCH ----
    if q and cfg.search_fields:
        search_q = Q()
        for field in cfg.search_fields:
            search_q |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(search_q)

    # ---- DATE FILTER ----
    if cfg.date_field and date_filter != "all":
        today = timezone.localdate()

        if date_filter == "today":
            start = today
        elif date_filter == "week":
            start = today - timedelta(days=7)
        elif date_filter == "month":
            start = date(today.year, today.month, 1)
        elif date_filter == "30d":
            start = today - timedelta(days=30)
        else:
            start = None

        if start:
            field_obj = cfg.model._meta.get_field(cfg.date_field)

            # DateTimeField -> use __date__gte
            if isinstance(field_obj, models.DateTimeField):
                qs = qs.filter(**{f"{cfg.date_field}__date__gte": start})
            else:
                # DateField -> use __gte
                qs = qs.filter(**{f"{cfg.date_field}__gte": start})

    qs = qs.order_by("-id")[:200]

    fields = [f for f in cfg.model._meta.fields if f.name != "id"]
    column_names = [f.verbose_name.title() for f in fields]
    column_keys = [f.name for f in fields]

    display_rows = [{"obj": r, "can_manage": can_manage_record(request.user, r)} for r in qs]

    context = {
        "tables": dropdown,
        "selected": selected,
        "rows": display_rows,
        "column_names": column_names,
        "column_keys": column_keys,
        "q": q,
        "date_filter": date_filter,
        "can_add": can_add_records(request.user),
        "mode": "model",
    }

    template_name = "crm/tables.html"
    if request.headers.get("HX-Request") == "true":
        template_name = "crm/partials/table_tbody.html"

    return render(request, template_name, context)




def _get_table_or_404(key: str):
    try:
        return TABLES[key]
    except KeyError:
        raise Http404("Unknown table")
def _editable_field_names(cfg):
    # Only fields that are editable and NOT ownership/audit fields
    excluded = {"id", "created_by", "created_at"}
    return {
        f.name
        for f in cfg.model._meta.fields
        if getattr(f, "editable", True) and f.name not in excluded
    }








@login_required
def table_add_record(request, table_key: str):
    cfg = _get_table_or_404(table_key)

    if not can_add_records(request.user):
        raise Http404()  # or return 403; MVP-friendly to hide it

    FormClass = cfg.form

    if request.method == "POST":
        form = FormClass(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)

            # attach owner if model supports it
            if hasattr(obj, "created_by_id") and not obj.created_by_id:
                obj.created_by = request.user

            obj.save()
            return redirect(f"{reverse('tables_page')}?table={cfg.key}")
    else:
        form = FormClass()

    return render(request, "crm/table_add_record.html", {"form": form, "selected": cfg})

@login_required
def table_edit_record(request, table_key: str, pk: int):
    cfg = _get_table_or_404(table_key)
    obj = get_object_or_404(cfg.model, pk=pk)

    if not can_manage_record(request.user, obj):
        raise Http404()

    FormClass = cfg.form

    if request.method == "POST":
        form = FormClass(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('tables_page')}?table={cfg.key}")
    else:
        form = FormClass(instance=obj)

    return render(request, "crm/table_edit_record.html", {"form": form, "selected": cfg, "obj": obj})


@login_required
def table_delete_record(request, table_key: str, pk: int):
    cfg = _get_table_or_404(table_key)
    obj = get_object_or_404(cfg.model, pk=pk)

    if not can_manage_record(request.user, obj):
        raise Http404()

    if request.method == "POST":
        obj.delete()
        return redirect(f"{reverse('tables_page')}?table={cfg.key}")

    return render(request, "crm/table_confirm_delete.html", {"selected": cfg, "obj": obj})

def table_row_display(request, table_key: str, pk: int):
    cfg = _get_table_or_404(table_key)
    obj = get_object_or_404(cfg.model, pk=pk)

    # Visibility (staff shouldn't be able to fetch other people’s rows)
    if not can_view_all(request.user) and hasattr(obj, "created_by_id") and obj.created_by_id != request.user.id:
        raise Http404()

    html = render_to_string(
        "crm/partials/table_row_display.html",
        {
            "selected": cfg,
            "row_obj": obj,
            "column_keys": [f.name for f in cfg.model._meta.fields if f.name != "id"],
            "can_manage": can_manage_record(request.user, obj),
        },
        request=request,
    )
    return HttpResponse(html)

@login_required
def table_row_edit(request, table_key: str, pk: int):
    cfg = _get_table_or_404(table_key)
    obj = get_object_or_404(cfg.model, pk=pk)

    if not can_manage_record(request.user, obj):
        raise Http404()

    FormClass = cfg.form
    form = FormClass(instance=obj)

    editable = _editable_field_names(cfg)
    column_keys = [f.name for f in cfg.model._meta.fields if f.name != "id"]

    html = render_to_string(
        "crm/partials/table_row_edit.html",
        {
            "selected": cfg,
            "row_obj": obj,
            "form": form,
            "editable_fields": editable,
            "column_keys": column_keys,
        },
        request=request,
    )
    return HttpResponse(html)

@login_required
def table_row_save(request, table_key: str, pk: int):
    cfg = _get_table_or_404(table_key)
    obj = get_object_or_404(cfg.model, pk=pk)

    if not can_manage_record(request.user, obj):
        raise Http404()

    FormClass = cfg.form
    form = FormClass(request.POST, instance=obj)

    column_keys = [f.name for f in cfg.model._meta.fields if f.name != "id"]

    if form.is_valid():
        form.save()
        html = render_to_string(
            "crm/partials/table_row_display.html",
            {
                "selected": cfg,
                "row_obj": obj,
                "column_keys": column_keys,
                "can_manage": can_manage_record(request.user, obj),
            },
            request=request,
        )
        return HttpResponse(html)

    # If invalid, return the edit row with errors
    editable = _editable_field_names(cfg)
    html = render_to_string(
        "crm/partials/table_row_edit.html",
        {
            "selected": cfg,
            "row_obj": obj,
            "form": form,
            "editable_fields": editable,
            "column_keys": column_keys,
        },
        request=request,
    )
    return HttpResponse(html)

