from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from .models import Expense, ExpenseCreate, TotalResponse
from .storage import ExpenseStore

DATA_FILE = os.environ.get("EXPENSES_DATA_FILE", "expenses.json")

app = FastAPI(
    title="Smart Expense Tracker API",
    description="A small REST API for tracking personal expenses.",
    version="1.0.0",
)

store = ExpenseStore(DATA_FILE)


@app.post("/expenses", response_model=Expense, status_code=201)
def add_expense(expense: ExpenseCreate) -> Expense:
    """Add a new expense."""
    return store.add(expense)


@app.get("/expenses", response_model=list[Expense])
def list_expenses(
    category: Optional[str] = Query(
        default=None, description="Filter results to this category (case-insensitive)"
    )
) -> list[Expense]:
    return store.list_all(category=category)


@app.get("/expenses/total", response_model=TotalResponse)
def get_total(
    category: Optional[str] = Query(
        default=None,
        description="If provided, only totals for this category are included",
    )
) -> TotalResponse:
    return TotalResponse(
        total=store.total(category=category),
        by_category=store.totals_by_category(),
    )


@app.delete("/expenses/{expense_id}", status_code=204, response_model=None)
def delete_expense(expense_id: int) -> None:
    """Delete an expense by id. 404s if it doesn't exist."""
    deleted = store.delete(expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")
