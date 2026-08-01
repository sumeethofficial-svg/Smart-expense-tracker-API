# AI Notes

I used Claude (Sonnet) to generate the initial implementation of this
project — the FastAPI app, the storage layer, the test suite, and this
documentation. Below is an honest breakdown of what came from the model,
what I checked or changed, and what I deliberately didn't use.

## 1. What was AI-generated vs. written by me

**AI-generated, largely as-is:**
- `src/models.py` — the Pydantic `ExpenseCreate`/`Expense`/`TotalResponse`
  models, including the `field_validator` that strips/rejects blank
  `title`/`category` values.
- `src/storage.py` — the `ExpenseStore` class (load/save to JSON,
  add/list/delete/total logic).
- `src/main.py` — the FastAPI route definitions wiring the store to
  HTTP endpoints.
- `tests/test_api.py` — the bulk of the test cases (happy paths, filter
  behavior, total/breakdown behavior, delete behavior).
- `tests/conftest.py` — the `client` fixture that re-imports the app per
  test against a fresh temp file.
- First drafts of `README.md` and this file.

**Where I intervened / directed the design:**
- I asked for the response shape of `GET /expenses/total` explicitly —
  the assignment says "calculate total expenses (overall and by
  category)", which is ambiguous about whether that's one endpoint or
  two. I decided on a single endpoint returning both `total` and
  `by_category`, with an optional `?category=` to scope `total` to one
  category while still returning the full breakdown for context. This
  is a product decision, not something I let the model just pick.
- I specified case-insensitive category filtering after noticing the
  first draft did an exact string match (see the "not used" example
  below).

## 2. What I validated, tested, or changed, and why

- **Ran the full test suite against a clean checkout** (`pip install -r
  requirements.txt && pytest tests/ -v`) — 20/20 passing. I didn't take
  "the tests pass" on faith from the model; I actually ran them myself
  in a fresh environment before writing this file.
- **Checked test isolation carefully.** The first version of
  `conftest.py` created the `ExpenseStore` once at module scope and
  reused it across tests, which meant expenses from one test leaked
  into the next (e.g. `test_ids_increment_across_expenses` would fail
  depending on run order). I changed the fixture to point
  `EXPENSES_DATA_FILE` at a fresh `tmp_path` file and re-import
  `src.main` fresh for every test, which fixed the leakage. This is the
  single biggest correctness fix I made to the AI's output.
- **Verified validation edge cases manually**, not just via generated
  tests: I hand-checked that `amount=0` and `amount=-5` are both
  rejected (`gt=0`, not `ge=0`), that a blank/whitespace-only `title`
  is rejected, and that an invalid `date` string returns `422` rather
  than being silently coerced.
- **Checked the persistence story.** I added
  `TestPersistence::test_data_survives_store_reload` myself (not
  originally generated) to confirm that data written by one
  `ExpenseStore` instance is actually readable by a second instance
  pointed at the same file — i.e., that a server restart doesn't lose
  data. This wasn't explicitly required by the assignment but felt
  like an important gap in the original test coverage, since "stored in
  a local JSON file" implies persistence across restarts.
- **Confirmed the README's commands actually work as written** by
  running them verbatim (`pip install -r requirements.txt`,
  `uvicorn src.main:app --reload`, `pytest tests/ -v`) on a clean
  checkout, since the assignment says these will be run exactly as
  given.

## 3. AI suggestions I decided not to use

- **In-memory-only storage with no file persistence.** The model's
  first pass defaulted to a plain Python list with no disk backing,
  which technically satisfies "in memory or a local JSON file" but
  loses all data on restart. I asked for JSON-file persistence instead,
  since it's more representative of what a real (if small) service
  would do and made the "does data survive a restart" test meaningful.
- **Exact-match (case-sensitive) category filtering.** The first draft
  of `list_all()` did `e.category == category`. I rejected this because
  a user typing `food` when data is stored as `Food` would get an
  empty, confusing result — case-insensitive matching is what a human
  would expect from a personal expense tracker.
- **Global exception handlers / custom error-response envelopes.** The
  model suggested adding a catch-all exception handler and a custom
  JSON error shape for all 4xx/5xx responses. I left this out —
  FastAPI's default validation error format is already clear and
  well-documented, and adding a custom envelope would be extra surface
  area with no real benefit for a project this size.
- **A `PUT /expenses/{id}` update endpoint.** The model suggested adding
  this "for completeness." I left it out because it isn't in the
  assignment's required feature list, and adding unrequested endpoints
  seemed more likely to introduce untested surface area than to earn
  credit.
