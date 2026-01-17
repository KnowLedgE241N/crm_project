from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from accounts.utils import can_fill_forms
from .models import DiabetesRiskAssessment
from .forms import DiabetesRiskForm
from .utils_diabetes import (
    calculate_bmi,
    bmi_score,
    waist_score,
    age_score,
    age_from_dob,
    risk_level_from_total,
)
from collections import Counter, defaultdict

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
            age = age_from_dob(cd["date_of_birth"])
            age_pts = age_score(age)

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
                date_of_birth=cd["date_of_birth"],
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

def _person_key(record) -> str:
    # Prefer DOB + postcode (best)
    if isinstance(record, dict):
        dob = (record or {}).get("date_of_birth", "") or ""
        pc = (record or {}).get("postcode", "") or ""
        fn = (record or {}).get("forename", "") or ""
        sn = (record or {}).get("surname", "") or ""
    else:
        dob = getattr(record, "date_of_birth", "") or ""
        pc = getattr(record, "postcode", "") or ""
        fn = getattr(record, "forename", "") or ""
        sn = getattr(record, "surname", "") or ""
    return f"{dob}|{pc}|{str(fn).lower()}|{str(sn).lower()}"


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None

@login_required
def dashboard(request):
    qs = DiabetesRiskAssessment.objects.all()

    today = timezone.localdate()
    month_start = date(today.year, today.month, 1)
    last_30 = today - timedelta(days=30)

    total = qs.count()
    this_month = qs.filter(submitted_at__date__gte=month_start).count()
    last30_qs = qs.filter(submitted_at__date__gte=last_30)

    # Unique people
    people = set()
    for s in qs.only("forename", "surname", "postcode", "date_of_birth"):
        people.add(_person_key(s))
    unique_people = len(people)

    # Avg risk score
    scores = list(qs.exclude(total_score__isnull=True).values_list("total_score", flat=True))
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Chart 1: daily submissions last 30 days
    day_counts = Counter()
    for s in last30_qs.only("submitted_at"):
        day_counts[s.submitted_at.date()] += 1
    series_counts = [
        {"date": (last_30 + timedelta(days=i)).isoformat(), "count": day_counts.get(last_30 + timedelta(days=i), 0)}
        for i in range(31)
    ]

    # Chart 2: risk distribution (computed from total_score)
    dist = Counter()
    for s in qs.only("total_score"):
        if s.total_score is None:
            continue
        band = risk_level_from_total(int(s.total_score))
        dist[str(band)] += 1
    risk_dist = [{"label": k, "count": v} for k, v in dist.items()]

    # Chart 3: avg BMI by week (last 8 weeks)
    week_bmi = defaultdict(list)
    for s in qs.only("submitted_at", "bmi"):
        bmi = _to_float(s.bmi)
        if bmi is None:
            continue
        wk = s.submitted_at.date() - timedelta(days=s.submitted_at.date().weekday())
        week_bmi[wk].append(bmi)

    weeks_sorted = sorted(week_bmi.keys())[-8:]
    avg_bmi_series = [
        {"week": w.isoformat(), "avg_bmi": round(sum(week_bmi[w]) / len(week_bmi[w]), 2)}
        for w in weeks_sorted
    ]

    return render(request, "crm/dashboard.html", {
        "kpis": {
            "total": total,
            "this_month": this_month,
            "unique_people": unique_people,
            "avg_score": avg_score,
        },
        "series_counts": series_counts,
        "risk_dist": risk_dist,
        "avg_bmi_series": avg_bmi_series,
    })



