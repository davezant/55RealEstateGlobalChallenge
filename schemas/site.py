import re
from typing import Dict
from pydantic import BaseModel, field_validator

FIELD_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")

class SiteTextSchema(BaseModel):
    campos: Dict[str, str]

    @field_validator("campos")
    @classmethod
    def validate_fields(cls, fields: Dict[str, str]) -> Dict[str, str]:
        if not fields:
            raise ValueError("vazio")
        for name, value in fields.items():
            if not FIELD_PATTERN.match(name):
                raise ValueError("campo_invalido")
            if not value.strip():
                raise ValueError("vazio")
            if len(value) > 2000:
                raise ValueError("muito_longo")
        return fields
