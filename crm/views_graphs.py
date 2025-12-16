from datetime import date
from typing import Any, Dict, List, Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.db.models import Count

from accounts.utils import can_view_all, can_access_tables
from crm.models import HealthCheck


NUMERIC_FIELDS = [
    ("systolic", "Systolic"),
    ("diastolic", "Diastolic"),
    ("pulse", "Pulse"),
    ("bmi", "BMI"),
    ("age", "Age"),
    ("risk", "Risk"),
]

PERSON_FIELDS = [
    ("forename", "Forename"),
    ("surname", "Surname"),
    ("postcode", "PostCode"),
]


def _base_qs(user):
    qs = HealthCheck.objects.all()

    # Staff see only their records; Manager/Admin see all
    if not can_view_all(user):
        # if your model doesn't have created_by, remove this
        if hasattr(HealthCheck, "created_by_id"):
            qs = qs.filter(created_by=user)

    return qs


@login_required
def graphs_page(request):
    if not can_access_tables(request.user):
        raise Http404()

    qs = _base_qs(request.user)

    # Build person list (simple: unique combinations)
    # If you have a Patient model later, swap this out for patient ids.
    people = (
        qs.values("forename", "surname", "postcode")
        .order_by("forename", "surname", "postcode")
        .distinct()
    )

    people_choices = []
    for p in people:
        label = f"{p.get('forename','') or ''} {p.get('surname','') or ''} ({p.get('postcode','') or ''})".strip()
        key = f"{p.get('forename','') or ''}|||{p.get('surname','') or ''}|||{p.get('postcode','') or ''}"
        people_choices.append((key, label))

    return render(request, "crm/graphs.html", {
        "numeric_fields": NUMERIC_FIELDS,
        "people_choices": people_choices,
    })


@login_required
def graphs_data(request):
    """
    Returns JSON for chart rendering.
    mode:
      - correlation: scatter X vs Y
      - progression: line chart for one person over time (metric vs date/index)
      - bmi_improvement: BMI change distribution for people with >=3 checks
    """
    if not can_access_tables(request.user):
        raise Http404()

    mode = request.GET.get("mode", "correlation").strip()
    qs = _base_qs(request.user)

    def parse_person_key(k: str):
        parts = (k or "").split("|||")
        if len(parts) != 3:
            return None
        return parts[0], parts[1], parts[2]

    if mode == "correlation":
        x = request.GET.get("x")
        y = request.GET.get("y")

        allowed = {f[0] for f in NUMERIC_FIELDS}
        if x not in allowed or y not in allowed:
            return JsonResponse({"ok": False, "error": "Invalid x/y"}, status=400)

        # Pull points (ignore nulls)
        rows = qs.values(x, y)
        points = []
        for r in rows:
            xv, yv = r.get(x), r.get(y)
            if xv is None or yv is None:
                continue
            try:
                points.append({"x": float(xv), "y": float(yv)})
            except (TypeError, ValueError):
                continue

        return JsonResponse({
            "ok": True,
            "mode": "correlation",
            "series": [{"label": f"{y} vs {x}", "points": points}],
        })

    if mode == "progression":
        metric = request.GET.get("metric")
        person_key = request.GET.get("person")

        allowed = {f[0] for f in NUMERIC_FIELDS}
        if metric not in allowed:
            return JsonResponse({"ok": False, "error": "Invalid metric"}, status=400)

        parsed = parse_person_key(person_key or "")
        if not parsed:
            return JsonResponse({"ok": False, "error": "Invalid person"}, status=400)
        fn, sn, pc = parsed

        person_qs = qs.filter(forename=fn, surname=sn, postcode=pc)

        # Prefer created_at if you have it; else fall back to id
        if hasattr(HealthCheck, "created_at"):
            person_qs = person_qs.order_by("created_at", "id")
            xlabels = []
            data = []
            for obj in person_qs:
                val = getattr(obj, metric, None)
                if val is None:
                    continue
                xlabels.append(obj.created_at.strftime("%Y-%m-%d"))
                data.append(float(val))
        else:
            person_qs = person_qs.order_by("id")
            xlabels = []
            data = []
            i = 1
            for obj in person_qs:
                val = getattr(obj, metric, None)
                if val is None:
                    continue
                xlabels.append(f"Check {i}")
                data.append(float(val))
                i += 1

        return JsonResponse({
            "ok": True,
            "mode": "progression",
            "labels": xlabels,
            "series": [{"label": metric, "data": data}],
        })

    if mode == "bmi_improvement":
        # People with >=3 checks
        # We'll define person by (forename, surname, postcode).
        # BMI improvement = last_bmi - first_bmi (negative = improvement if BMI drops).
        people = (
            qs.values("forename", "surname", "postcode")
            .annotate(n=Count("id"))
            .filter(n__gte=3)
        )

        deltas = []
        for p in people:
            fn, sn, pc = p["forename"], p["surname"], p["postcode"]
            person_qs = qs.filter(forename=fn, surname=sn, postcode=pc)

            if hasattr(HealthCheck, "created_at"):
                person_qs = person_qs.order_by("created_at", "id")
            else:
                person_qs = person_qs.order_by("id")

            checks = list(person_qs)
            if len(checks) < 3:
                continue

            first = getattr(checks[0], "bmi", None)
            last = getattr(checks[-1], "bmi", None)
            if first is None or last is None:
                continue

            try:
                delta = float(last) - float(first)
            except (TypeError, ValueError):
                continue

            deltas.append({
                "person": f"{fn} {sn} ({pc})",
                "delta": delta,
                "count": len(checks),
            })

        return JsonResponse({
            "ok": True,
            "mode": "bmi_improvement",
            "series": [{"label": "BMI change (last - first)", "points": deltas}],
        })

    return JsonResponse({"ok": False, "error": "Unknown mode"}, status=400)
