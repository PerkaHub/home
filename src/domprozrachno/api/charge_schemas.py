from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NonBlank = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]


class ChargeLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: NonBlank
    basis: NonBlank
    amount_minor: int = Field(strict=True)


class ChargeDraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: str
    amount_minor: int = Field(strict=True)
    lines: list[ChargeLineInput] = Field(min_length=1)


class ChargeLineResponse(ChargeLineInput):
    id: UUID


class ChargeResponse(BaseModel):
    id: UUID
    account_id: UUID
    period: str
    amount_minor: int
    currency: Literal["RUB"] = "RUB"
    status: Literal["draft", "published"]
    lines: list[ChargeLineResponse]
    created_at: datetime
    published_at: datetime | None = None
