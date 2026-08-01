import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path):
    """Fresh app + fresh empty JSON file for every test, fully isolated."""
    data_file = tmp_path / "expenses.json"
    os.environ["EXPENSES_DATA_FILE"] = str(data_file)

    # src.main creates its ExpenseStore at import time, so force a reimport
    # for every test to point it at this test's temp file.
    for mod in ["src.main", "src.storage", "src.models"]:
        sys.modules.pop(mod, None)

    main = importlib.import_module("src.main")
    with TestClient(main.app) as c:
        yield c

    os.environ.pop("EXPENSES_DATA_FILE", None)
