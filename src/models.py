"""Pydantic models for the Expense Tracker API."""
from __future__ import annotations

from datetime import date as date_type

from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    """Payload for creating a new expense. `id` is assigned by the server."""

    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0, description="Must be a positive number")
    category: str = Field(..., min_length=1, max_length=100)
    date: date_type

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class Expense(ExpenseCreate):
    """A stored expense, including its server-assigned id."""

    id: int


class TotalResponse(BaseModel):
    total: float
    by_category: dict[str, float]
