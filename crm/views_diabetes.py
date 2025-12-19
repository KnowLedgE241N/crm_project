from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from forms_builder.models import FormDefinition, FormField
from .forms import DiabetesRiskForm
from .models import DiabetesRiskAssessment

from .utils_diabetes import calculate_bmi, bmi_score, waist_score, age_score


@login_required
def diabetes_risk_form(request, pk: int):
    form_def = get_object_or_404(FormDefinition, pk=pk)

    form = DiabetesRiskForm(request.POST or None)

    # Apply drag & drop ordering
    ordered_keys = list(
        FormField.objects.filter(form=form_def)
        .order_by("order", "id")
        .values_list("key", flat=True)
    )
    form.order_fields([k for k in ordered_keys if k in form.fields])

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data

        # --- Calculations ---
        bmi = calculate_bmi(cd["height"], cd["weight"])
        age_pts = age_score(cd["age"])
        gender_pts = {"F": 0, "M": 1}[cd["gender"]]
        eth_pts = {"WHITE": 0, "OTHER": 6}[cd["ethnicity"]]
        fam_pts = {"YES": 5, "NO": 0}[cd["family"]]

        waist_pts = waist_score(cd["waist"])
        bmi_pts = bmi_score(bmi)

        # If you add BP later, set bp_pts properly
        bp_pts = 0

        total = age_pts + gender_pts + eth_pts + fam_pts + waist_pts + bmi_pts + bp_pts

        # --- Save (NO risk_level) ---
        DiabetesRiskAssessment.objects.create(
            submitted_by=request.user,

            age_score=age_pts,
            gender_score=gender_pts,
            ethnicity_score=eth_pts,
            family_history_score=fam_pts,
            waist_score=waist_pts,
            bmi_score=bmi_pts,
            bp_score=bp_pts,
            total_score=total,

            # If your model has raw values, store them too:
            # age=cd["age"],
            # gender=cd["gender"],
            # ethnicity=cd["ethnicity"],
            # waist_cm=cd["waist"],
            # height_cm=cd["height"],
            # weight_kg=cd["weight"],
            # bmi=bmi,
            # family_history=cd["family"],
        )

        return render(request, "crm/diabetes_result.html", {
            "total": total,
            "bmi": bmi,
            "waist_score": waist_pts,
        })

    return render(request, "crm/diabetes_form.html", {
        "form": form,
        "form_def": form_def,
    })
