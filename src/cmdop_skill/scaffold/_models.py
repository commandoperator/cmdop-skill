"""ScaffoldConfig — Pydantic 2 model for the ``init`` wizard."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator


class ScaffoldConfig(BaseModel):
    """All data needed to scaffold a new CMDOP skill."""

    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=300)
    author_name: str = Field(default="CMDOP Team", max_length=100)
    author_email: str = Field(default="team@cmdop.com", max_length=100)
    package_name: str = ""

    @field_validator("name")
    @classmethod
    def _kebab_case(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", v):
            raise ValueError(
                f"Name must be kebab-case (lowercase letters, digits, hyphens): {v!r}"
            )
        return v

    @model_validator(mode="after")
    def _derive_package_name(self) -> ScaffoldConfig:
        if not self.package_name:
            self.package_name = self.name.replace("-", "_")
        return self
