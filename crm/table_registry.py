from __future__ import annotations
from .table_config import TableConfig
from .models import DiabetesRiskAssessment

TABLES: dict[str, TableConfig] = {
    "diabetes_risk": TableConfig(
        key="diabetes_risk",
        label="Diabetes Risk Assessment (Form 8)",
        model=DiabetesRiskAssessment,
        form=None,  # analytics table is read-only
        search_fields=["forename", "surname", "postcode", "gp"],
        date_field="submitted_at",
    ),
}
