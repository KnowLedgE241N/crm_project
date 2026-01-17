from __future__ import annotations
from decimal import Decimal
from datetime import date
from django.utils.dateparse import parse_date
from crm.models import DiabetesRiskAssessment, CoffeeMorning
from decimal import Decimal, InvalidOperation
from crm.utils_diabetes import (
    calculate_bmi,
    age_from_dob,
    age_score,
    bmi_score,
    waist_score,
)

def _int(v):
    try:
        if v in (None, "", "—"):
            return None
        return int(float(v))  # handles "12.0" etc
    except Exception:
        return None

def _dec(v):
    """
    Safe Decimal conversion.
    Returns None for blanks, NaN, Infinity, or any invalid value.
    """
    try:
        if v in (None, "", "—"):
            return None

        d = Decimal(str(v))

        # Guard against NaN / Infinity
        if not d.is_finite():
            return None

        return d
    except (InvalidOperation, ValueError, TypeError):
        return None

def _date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    return parse_date(str(v))

def sync_submission_to_diabetes_risk(submission):
    a = submission.answers or {}

    bmi_val = _dec(a.get("bmi"))
    if bmi_val is None:
        height_cm = _int(a.get("height_cm"))
        weight_kg = _dec(a.get("weight_kg"))
        if height_cm and weight_kg is not None:
            bmi_val = _dec(calculate_bmi(height_cm, float(weight_kg)))

    total_score_val = _int(a.get("total_score"))
    if total_score_val is None:
        dob = _date(a.get("date_of_birth"))
        age_pts = age_score(age_from_dob(dob)) if dob else 0
        gender_pts = {"F": 0, "M": 1}.get(str(a.get("gender", "")).strip(), 0)
        eth_pts = {"WHITE": 0, "OTHER": 6}.get(str(a.get("ethnicity", "")).strip(), 0)
        fam_pts = {"YES": 5, "NO": 0}.get(str(a.get("family_history", "")).strip(), 0)
        bp_pts = {"YES": 5, "NO": 0}.get(str(a.get("high_bp", "")).strip(), 0)
        bmi_pts = bmi_score(float(bmi_val)) if bmi_val is not None else 0
        waist_pts = waist_score(float(_dec(a.get("waist_cm")) or 0))
        total_score_val = int(age_pts + gender_pts + eth_pts + fam_pts + bp_pts + bmi_pts + waist_pts)

    return DiabetesRiskAssessment.objects.create(
        submitted_by=submission.submitted_by,
        submitted_at=submission.submitted_at,

        forename=str(a.get("forename", "") or ""),
        surname=str(a.get("surname", "") or ""),
        postcode=str(a.get("postcode", "") or ""),
        gp=str(a.get("gp", "") or ""),
        date_of_birth=_date(a.get("date_of_birth")),

        gender=str(a.get("gender", "") or ""),
        ethnicity=str(a.get("ethnicity", "") or ""),

        systolic=_int(a.get("systolic")),
        diastolic=_int(a.get("diastolic")),
        pulse=_int(a.get("pulse")),

        waist_cm=_dec(a.get("waist_cm")),
        height_cm=_int(a.get("height_cm")),
        weight_kg=_dec(a.get("weight_kg")),
        bmi=bmi_val,
        total_score=total_score_val,
    )


def sync_submission_to_coffee_morning(submission):
    a = submission.answers or {}

    return CoffeeMorning.objects.create(
        submitted_by=submission.submitted_by,
        submitted_at=submission.submitted_at,

        forename=str(a.get("forename", "") or ""),
        surname=str(a.get("surname", "") or ""),
        postcode=str(a.get("postcode", "") or ""),
        gp=str(a.get("gp", "") or ""),
        date_of_birth=_date(a.get("date_of_birth")),

        gender=str(a.get("gender", "") or ""),
        ethnicity=str(a.get("ethnicity", "") or ""),
    )
