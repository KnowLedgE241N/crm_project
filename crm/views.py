from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import date
from .models import HealthCheck
from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import HealthCheckForm
from django.http import Http404
from accounts.utils import can_manage_forms, can_fill_forms


def _visible_healthchecks(user):
    qs = HealthCheck.objects.all()
    if user.is_superuser or getattr(user, "role", None) in ("ADMIN", "MANAGER"):
        return qs
    return qs.filter(created_by=user)

@login_required
def dashboard(request):
    qs = _visible_healthchecks(request.user)

    today = timezone.localdate()
    month_start = date(today.year, today.month, 1)

    context = {
        "total_health_checks": qs.count(),
        "health_checks_this_month": qs.filter(created_at__date__gte=month_start).count(),
    }
    return render(request, "crm/dashboard.html", context)

@login_required
def healthcheck_create(request):
    if request.method == "POST":
        form = HealthCheckForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect("dashboard")  # later we’ll redirect to a list page
    else:
        form = HealthCheckForm()

    return render(request, "crm/healthcheck_form.html", {"form": form})
