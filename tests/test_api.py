def make_expense(client, title="Coffee", amount=4.5, category="Food", date="2026-07-01"):
    return client.post(
        "/expenses",
        json={"title": title, "amount": amount, "category": category, "date": date},
    )


class TestAddExpense:
    def test_add_expense_returns_201_and_assigned_id(self, client):
        resp = make_expense(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["title"] == "Coffee"
        assert body["amount"] == 4.5
        assert body["category"] == "Food"
        assert body["date"] == "2026-07-01"

    def test_ids_increment_across_expenses(self, client):
        first = make_expense(client).json()
        second = make_expense(client, title="Lunch").json()
        assert second["id"] == first["id"] + 1

    def test_negative_amount_rejected(self, client):
        resp = make_expense(client, amount=-5)
        assert resp.status_code == 422

    def test_zero_amount_rejected(self, client):
        resp = make_expense(client, amount=0)
        assert resp.status_code == 422

    def test_blank_title_rejected(self, client):
        resp = make_expense(client, title="   ")
        assert resp.status_code == 422

    def test_invalid_date_rejected(self, client):
        resp = client.post(
            "/expenses",
            json={"title": "X", "amount": 1, "category": "Food", "date": "not-a-date"},
        )
        assert resp.status_code == 422

    def test_missing_field_rejected(self, client):
        resp = client.post("/expenses", json={"title": "X", "amount": 1})
        assert resp.status_code == 422


class TestListExpenses:
    def test_list_empty_initially(self, client):
        resp = client.get("/expenses")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_all_expenses(self, client):
        make_expense(client, title="Coffee", category="Food")
        make_expense(client, title="Bus ticket", category="Transport")
        resp = client.get("/expenses")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_filter_by_category(self, client):
        make_expense(client, title="Coffee", category="Food")
        make_expense(client, title="Bus ticket", category="Transport")
        make_expense(client, title="Lunch", category="Food")

        resp = client.get("/expenses", params={"category": "Food"})
        assert resp.status_code == 200
        titles = {e["title"] for e in resp.json()}
        assert titles == {"Coffee", "Lunch"}

    def test_filter_by_category_case_insensitive(self, client):
        make_expense(client, title="Coffee", category="Food")
        resp = client.get("/expenses", params={"category": "food"})
        assert len(resp.json()) == 1

    def test_filter_by_unknown_category_returns_empty(self, client):
        make_expense(client, category="Food")
        resp = client.get("/expenses", params={"category": "Nonexistent"})
        assert resp.json() == []


class TestTotals:
    def test_total_with_no_expenses_is_zero(self, client):
        resp = client.get("/expenses/total")
        assert resp.status_code == 200
        assert resp.json() == {"total": 0, "by_category": {}}

    def test_overall_total_sums_all_expenses(self, client):
        make_expense(client, amount=10, category="Food")
        make_expense(client, amount=5.5, category="Transport")
        resp = client.get("/expenses/total")
        assert resp.json()["total"] == 15.5

    def test_by_category_breakdown(self, client):
        make_expense(client, amount=10, category="Food")
        make_expense(client, amount=5, category="Food")
        make_expense(client, amount=20, category="Transport")
        resp = client.get("/expenses/total")
        assert resp.json()["by_category"] == {"Food": 15, "Transport": 20}

    def test_total_scoped_to_category(self, client):
        make_expense(client, amount=10, category="Food")
        make_expense(client, amount=20, category="Transport")
        resp = client.get("/expenses/total", params={"category": "Food"})
        assert resp.json()["total"] == 10


class TestDeleteExpense:
    def test_delete_existing_expense(self, client):
        created = make_expense(client).json()
        resp = client.delete(f"/expenses/{created['id']}")
        assert resp.status_code == 204

        remaining = client.get("/expenses").json()
        assert remaining == []

    def test_delete_nonexistent_expense_returns_404(self, client):
        resp = client.delete("/expenses/999")
        assert resp.status_code == 404

    def test_delete_then_total_updates(self, client):
        first = make_expense(client, amount=10).json()
        make_expense(client, amount=5)
        client.delete(f"/expenses/{first['id']}")
        resp = client.get("/expenses/total")
        assert resp.json()["total"] == 5


class TestPersistence:
    def test_data_survives_store_reload(self, client, tmp_path):
        from src.storage import ExpenseStore

        make_expense(client, title="Coffee", amount=4.5)

        # Simulate a server restart: read the same file with a new store.
        data_file = tmp_path / "expenses.json"
        reloaded = ExpenseStore(data_file)
        assert len(reloaded.list_all()) == 1
        assert reloaded.list_all()[0].title == "Coffee"
