from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, date
from django.db import models

from types import SimpleNamespace
from forms_builder.models import FormDefinition, FormField, FormSubmission
from .table_registry import TABLES

from forms_builder.models import FormSubmission, FormDefinition

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, DateTimeField, DateField
from accounts.utils import can_access_tables, can_view_all, can_add_records, can_manage_record

















def _get_table_or_404(key: str):
    if key in TABLES:
        return TABLES[key]
    raise Http404("Unknown table")


@login_required
def tables_page(request):
    if not can_access_tables(request.user):
        raise Http404()

    selected_key = request.GET.get("table") or next(iter(TABLES.keys()))
    cfg = _get_table_or_404(selected_key)

    qs = cfg.model.objects.all()

    # Staff visibility (if you add created_by later)
    if not can_view_all(request.user) and hasattr(cfg.model, "submitted_by_id"):
        qs = qs.filter(submitted_by=request.user)

    # Search
    q = (request.GET.get("q") or "").strip()
    if q and cfg.search_fields:
        search_q = Q()
        for field in cfg.search_fields:
            search_q |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(search_q)

    # Date filters
    date_filter = request.GET.get("date") or "all"
    start = None
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

    if start:
        field_obj = cfg.model._meta.get_field(cfg.date_field)
        if isinstance(field_obj, models.DateTimeField):
            qs = qs.filter(**{f"{cfg.date_field}__date__gte": start})
        else:
            qs = qs.filter(**{f"{cfg.date_field}__gte": start})

    qs = qs.order_by("-id")[:500]

    fields = [f for f in cfg.model._meta.fields if f.name != "id"]
    column_names = [f.verbose_name.title() for f in fields]
    column_keys = [f.name for f in fields]

    context = {
        "tables": list(TABLES.values()),
        "selected": cfg,
        "rows": qs,
        "column_names": column_names,
        "column_keys": column_keys,
        "q": q,
        "date_filter": date_filter,

        # IMPORTANT: only show Add if table has a form
        "can_add": False,
    }
    return render(request, "crm/tables.html", context)

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
    if cfg.form is None:
        raise Http404("This table is not form-backed")
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

