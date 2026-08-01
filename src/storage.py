"""Simple JSON-file backed storage for expenses.

Kept deliberately small: one class, an in-memory list as the working copy,
and the JSON file as the persistence layer. Not meant to scale past a
single-user personal expense tracker, which matches the assignment scope.
"""
from __future__ import annotations

import json
import threading
from datetime import date
from pathlib import Path
from typing import Optional

from .models import Expense, ExpenseCreate


class ExpenseStore:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._lock = threading.Lock()
        self._expenses: list[Expense] = []
        self._next_id = 1
        self._load()

    # -- persistence -----------------------------------------------------
    def _load(self) -> None:
        if not self.file_path.exists():
            self._expenses = []
            self._next_id = 1
            return

        raw = self.file_path.read_text().strip()
        if not raw:
            self._expenses = []
            self._next_id = 1
            return

        data = json.loads(raw)
        self._expenses = [Expense(**item) for item in data]
        self._next_id = (max((e.id for e in self._expenses), default=0)) + 1

    def _save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [json.loads(e.model_dump_json()) for e in self._expenses]
        self.file_path.write_text(json.dumps(payload, indent=2, default=str))

    # -- CRUD --------------------------------------------------------------
    def add(self, data: ExpenseCreate) -> Expense:
        with self._lock:
            expense = Expense(id=self._next_id, **data.model_dump())
            self._expenses.append(expense)
            self._next_id += 1
            self._save()
            return expense

    def list_all(self, category: Optional[str] = None) -> list[Expense]:
        if category is None:
            return list(self._expenses)
        return [
            e for e in self._expenses if e.category.lower() == category.lower()
        ]

    def delete(self, expense_id: int) -> bool:
        with self._lock:
            before = len(self._expenses)
            self._expenses = [e for e in self._expenses if e.id != expense_id]
            deleted = len(self._expenses) != before
            if deleted:
                self._save()
            return deleted

    def total(self, category: Optional[str] = None) -> float:
        return round(
            sum(e.amount for e in self.list_all(category=category)), 2
        )

    def totals_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for e in self._expenses:
            totals[e.category] = round(totals.get(e.category, 0) + e.amount, 2)
        return totals
