from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Lang = Literal["en", "de", "es"]


class PostRequest(BaseModel):
    product_id: str = Field(examples=["LL-002"])
    languages: list[Lang] = Field(min_length=1, examples=[["en", "de", "es"]])
    notes: str | None = Field(
        default=None, max_length=500,
        description="Optional free-text hints for the writer (e.g. a theme). Screened against the brand guide.",
        examples=["cosy autumn mood"],
    )

    @field_validator("languages", mode="before")
    @classmethod
    def _lower_dedupe(cls, v: Any) -> Any:
        if isinstance(v, list):
            seen: list[Any] = []
            for x in v:
                x = x.strip().lower() if isinstance(x, str) else x
                if x not in seen:
                    seen.append(x)
            return seen
        return v


class CheckRequest(BaseModel):
    caption: str = Field(min_length=1, max_length=3000,
                         examples=["Your sofa deserves a calm companion. #LumoLiving"])
    language: Lang = "en"
    product_id: str | None = Field(default=None, description="Optional; enables product-name, feature and sustainability checks.")

    @field_validator("language", mode="before")
    @classmethod
    def _lower(cls, v: Any) -> Any:
        return v.strip().lower() if isinstance(v, str) else v
