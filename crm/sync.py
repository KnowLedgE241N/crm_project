from __future__ import annotations
from decimal import Decimal
from datetime import date
from django.utils.dateparse import parse_date
from crm.models import DiabetesRiskAssessment
from decimal import Decimal, InvalidOperation

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
        bmi=_dec(a.get("bmi")),
        total_score=_int(a.get("total_score")),
    )
