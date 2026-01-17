from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from accounts.utils import can_access_tables, can_view_all
from forms_builder.models import FormSubmission


def _norm(s: str) -> str:
    return (s or "").strip().lower()


@login_required
def global_search(request):
    if not can_access_tables(request.user):
        raise Http404()

    q = _norm(request.GET.get("q", ""))
    results = []

    if q:
        qs = FormSubmission.objects.all()

        # if you want staff to only see submissions they submitted, uncomment:
        # if not can_view_all(request.user):
        #     qs = qs.filter(submitted_by=request.user)

        qs = qs.filter(
            Q(forename__icontains=q) |
            Q(surname__icontains=q) |
            Q(postcode__icontains=q) |
            Q(answers__icontains=q)  # works well on Postgres; OK-ish on SQLite
        ).select_related("form").order_by("-submitted_at")[:200]

        # group by person (identity cols)
        seen = {}
        for s in qs:
            key = (s.forename, s.surname, s.postcode, str(s.date_of_birth or ""))
            if key not in seen:
                seen[key] = {
                    "forename": s.forename,
                    "surname": s.surname,
                    "postcode": s.postcode,
                    "dob": str(s.date_of_birth or ""),
                    "count": 0,
                }
            seen[key]["count"] += 1

        results = sorted(seen.values(), key=lambda r: r["count"], reverse=True)

    return render(request, "crm/global_search.html", {"q": request.GET.get("q", ""), "results": results})


@login_required
def person_activity(request):
    if not can_access_tables(request.user):
        raise Http404()

    forename = _norm(request.GET.get("forename", ""))
    surname = _norm(request.GET.get("surname", ""))
    postcode = _norm(request.GET.get("postcode", ""))
    dob = request.GET.get("dob", "").strip()

    if not forename or not surname:
        raise Http404()

    qs = FormSubmission.objects.filter(
        forename=forename,
        surname=surname,
    ).select_related("form").order_by("-submitted_at")

    if postcode:
        qs = qs.filter(postcode=postcode)
    if dob:
        qs = qs.filter(date_of_birth=dob)

    # staff restriction optional:
    # if not can_view_all(request.user):
    #     qs = qs.filter(submitted_by=request.user)

    items = []
    for s in qs[:800]:
        items.append({
            "when": s.submitted_at,
            "form_name": s.form.name,
            "submission_id": s.id,
            "submitted_by": str(s.submitted_by),
        })

    label = f"{forename.title()} {surname.title()}"
    if postcode:
        label += f" • {postcode.upper()}"
    if dob:
        label += f" • {dob}"

    return render(request, "crm/person_activity.html", {"person_label": label, "items": items})
