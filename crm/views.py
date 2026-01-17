from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from accounts.utils import can_fill_forms
from .models import  DiabetesRiskAssessment
from .forms import  DiabetesRiskForm
from .utils_diabetes import calculate_bmi, bmi_score, waist_score, age_score, age_from_dob
from forms_builder.models import FormSubmission,  FormDefinition
from collections import Counter, defaultdict

RISK_FORM_NAME = "DiabetesRiskAssessment"  # change to your exact form name

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

def _person_key(ans: dict) -> str:
    # Prefer DOB + postcode (best)
    dob = (ans or {}).get("date_of_birth", "") or ""
    pc = (ans or {}).get("postcode", "") or ""
    fn = (ans or {}).get("forename", "") or ""
    sn = (ans or {}).get("surname", "") or ""
    return f"{dob}|{pc}|{fn.lower()}|{sn.lower()}"


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None

@login_required
def dashboard(request):
    form_def = FormDefinition.objects.filter(name=RISK_FORM_NAME).first()

    # If the form doesn't exist yet, show empty dashboard
    if not form_def:
        return render(request, "crm/dashboard.html", {
            "risk_form_missing": True,
            "kpis": {},
            "series_counts": [],
            "risk_dist": [],
            "avg_bmi_series": [],
        })

    qs = FormSubmission.objects.filter(form=form_def)

    today = timezone.localdate()
    month_start = date(today.year, today.month, 1)
    last_30 = today - timedelta(days=30)

    total = qs.count()
    this_month = qs.filter(submitted_at__date__gte=month_start).count()
    last30_qs = qs.filter(submitted_at__date__gte=last_30)

    # Unique people
    people = set()
    for s in qs.only("answers"):
        people.add(_person_key(s.answers))
    unique_people = len(people)

    # Avg risk score
    scores = []
    for s in qs.only("answers"):
        score = _to_float((s.answers or {}).get("total_score"))
        if score is not None:
            scores.append(score)
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Chart 1: daily submissions last 30 days
    day_counts = Counter()
    for s in last30_qs.only("submitted_at"):
        day_counts[s.submitted_at.date()] += 1
    series_counts = [
        {"date": (last_30 + timedelta(days=i)).isoformat(), "count": day_counts.get(last_30 + timedelta(days=i), 0)}
        for i in range(31)
    ]

    # Chart 2: risk distribution (if you store a category or compute from total_score)
    # If you store "risk_band" in answers, use it directly:
    dist = Counter()
    for s in qs.only("answers"):
        band = (s.answers or {}).get("risk_band")
        if band:
            dist[str(band)] += 1
    risk_dist = [{"label": k, "count": v} for k, v in dist.items()]

    # Chart 3: avg BMI by week (last 8 weeks)
    week_bmi = defaultdict(list)
    for s in qs.only("submitted_at", "answers"):
        bmi = _to_float((s.answers or {}).get("bmi"))
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
        "risk_form": form_def,
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



