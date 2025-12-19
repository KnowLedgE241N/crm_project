from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.utils import can_fill_forms
from .models import HealthCheck, DiabetesRiskAssessment
from .forms import HealthCheckForm, DiabetesRiskForm
from .utils_diabetes import calculate_bmi, bmi_score, waist_score, age_score


# -----------------------------
# Diabetes Risk (combined form)
# -----------------------------
@login_required
def diabetes_risk_create(request):
    if not can_fill_forms(request.user):
        raise Http404()

    if request.method == "POST":
        form = DiabetesRiskForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            bmi = calculate_bmi(cd["height_cm"], cd["weight_kg"])

            # points
            age_pts = age_score(cd["age"])
            gender_pts = {"F": 0, "M": 1}[cd["gender"]]
            eth_pts = {"WHITE": 0, "OTHER": 6}[cd["ethnicity"]]
            fam_pts = {"YES": 5, "NO": 0}[cd["family_history"]]
            bp_pts = {"YES": 5, "NO": 0}[cd["high_bp"]]
            bmi_pts = bmi_score(bmi)
            waist_pts = waist_score(cd["waist_cm"])

            total = age_pts + gender_pts + eth_pts + fam_pts + bmi_pts + waist_pts + bp_pts

            DiabetesRiskAssessment.objects.create(
                submitted_by=request.user,

                forename=cd["forename"],
                surname=cd["surname"],
                gender=cd["gender"],
                ethnicity=cd["ethnicity"],
                postcode=cd.get("postcode", "") or "",
                gp=cd.get("gp", "") or "",
                age=cd["age"],  # ✅ INT AGE

                systolic=cd.get("systolic"),
                diastolic=cd.get("diastolic"),
                pulse=cd.get("pulse"),

                waist_cm=cd["waist_cm"],
                height_cm=cd["height_cm"],
                weight_kg=cd["weight_kg"],
                bmi=bmi,

                family_history=cd["family_history"],
                high_bp=cd["high_bp"],

                age_score=age_pts,
                gender_score=gender_pts,
                ethnicity_score=eth_pts,
                family_history_score=fam_pts,
                waist_score=waist_pts,
                bmi_score=bmi_pts,
                bp_score=bp_pts,
                total_score=total,
            )

            return render(request, "crm/diabetes_result.html", {
                "total": total,
                "bmi": bmi,
                "waist_score": waist_pts,
            })
    else:
        form = DiabetesRiskForm()

    return render(request, "crm/diabetes_form.html", {"form": form})


# -----------------------------
# HealthCheck (existing system)
# -----------------------------
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
            return redirect("dashboard")
    else:
        form = HealthCheckForm()

    return render(request, "crm/healthcheck_form.html", {"form": form})
