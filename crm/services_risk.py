from .models import DiabetesRiskAssessment

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.dateparse import parse_date

from .models import RiskAssessmentRecord
from .utils_diabetes import calculate_bmi, age_score, bmi_score, waist_category


def _to_int(v):
    try:
        if v is None or v == "":
            return None
        return int(v)
    except (ValueError, TypeError):
        return None


def _to_decimal(v):
    try:
        if v is None or v == "":
            return None
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _to_date(v):
    # submissions store ISO strings like "2001-05-04"
    if not v:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return parse_date(v)
    return None


@transaction.atomic
def sync_form8_submission_to_risk_record(submission):
    """
    Create/update RiskAssessmentRecord from a FormSubmission (form_id=8).
    Assumes answers keys match your form fields (adjust mapping if needed).
    """
    a = submission.answers or {}

    # ---- Map answers ----
    forename = (a.get("forename") or "").strip()
    surname = (a.get("surname") or "").strip()
    postcode = (a.get("postcode") or "").strip()
    gp = (a.get("gp") or "").strip()

    dob = _to_date(a.get("date_of_birth"))
    gender = (a.get("gender") or "").strip()
    ethnicity = (a.get("ethnicity") or "").strip()

    systolic = _to_int(a.get("systolic"))
    diastolic = _to_int(a.get("diastolic"))
    pulse = _to_int(a.get("pulse"))

    waist_cm = _to_decimal(a.get("waist_cm"))
    height_cm = _to_int(a.get("height_cm"))
    weight_kg = _to_decimal(a.get("weight_kg"))

    # ---- Compute BMI + score (same logic as your form live calc, but server-side truth) ----
    bmi = None
    if height_cm and weight_kg is not None:
        bmi_val = calculate_bmi(height_cm, float(weight_kg))
        bmi = Decimal(str(bmi_val)).quantize(Decimal("0.01"))

    # Age score based on DOB (if you want age from DOB)
    # If you currently store an "age" field, swap this logic.
    age_pts = 0
    if dob:
        # approximate age in years
        from django.utils import timezone
        today = timezone.localdate()
        age_years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        age_pts = age_score(age_years)

    # waist_category returns points in your latest version (0/4/6/9)
    waist_pts = None
    if waist_cm is not None:
        waist_pts = waist_category(float(waist_cm))

    bmi_pts = 0
    if bmi is not None:
        bmi_pts = bmi_score(float(bmi))

    # other points (adjust to your exact keys)
    gender_pts = {"F": 0, "M": 1}.get(gender, 0)
    eth_pts = {"WHITE": 0, "OTHER": 6}.get(ethnicity, 0)
    fam_pts = {"YES": 5, "NO": 0}.get((a.get("family_history") or "").strip(), 0)
    bp_pts = {"YES": 5, "NO": 0}.get((a.get("high_bp") or "").strip(), 0)

    total = age_pts + gender_pts + eth_pts + fam_pts + bp_pts + bmi_pts + (waist_pts or 0)

    # ---- Upsert record (one per submission) ----
    obj, _ = DiabetesRiskAssessment.objects.update_or_create(
        submission=submission,
        defaults={
            "submitted_by": submission.submitted_by,
            "submitted_at": submission.submitted_at,
            "forename": forename,
            "surname": surname,
            "postcode": postcode,
            "gp": gp,
            "date_of_birth": dob,
            "gender": gender,
            "ethnicity": ethnicity,
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "waist_cm": waist_cm,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": bmi,
            "total_score": int(total),
        },
    )

    return obj
