from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Type
from django.db import models

@dataclass(frozen=True)
class TableConfig:
    key: str
    label: str
    model: Type[models.Model]
    form: Optional[Type] = None
    search_fields: list[str] | None = None
    date_field: str | None = None
