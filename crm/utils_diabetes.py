def calculate_bmi(height_cm: int, weight_kg: float) -> float:
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 1)


def waist_score(waist_cm: float) -> str:
    if waist_cm < 90:
        return 0
    if waist_cm < 99.9:
        return 4
    if waist_cm < 109.9:
        return 6
    else:
        return 9


def bmi_score(bmi: float) -> int:
    if bmi < 25:
        return 0
    if bmi < 29.9:
        return 3
    if bmi < 34.9:
        return 5
    else:
        return 8




def risk_level_from_total(total: int) -> str:
    if total <= 6:
        return "Low"
    if total <= 15:
        return "Increased"
    if total <= 24:
        return "Moderate"
    return "High"

def age_score(age: int) -> int:
    if age <= 49:
        return 0
    elif age <= 59:
        return 5
    elif age <= 69:
        return 9
    else:
        return 13

