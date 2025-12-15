from dataclasses import dataclass
from typing import Type
from .models import HealthCheck
from .forms import HealthCheckForm


@dataclass(frozen=True)
class TableConfig:
    key: str
    label: str
    model: Type
    form: Type
    search_fields: list[str]   # NEW
    date_field: str | None     # NEW (for time filters)


TABLES: dict[str, TableConfig] = {
    "healthchecks": TableConfig(
        key="healthchecks",
        label="Health Checks",
        model=HealthCheck,
        form=HealthCheckForm,
        search_fields=["forename", "surname", "postcode", "gp", "risk"],  # customise
        date_field="check_date",  # or "check_date" if you prefer
    ),
}
