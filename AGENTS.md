Terse like caveman. Technical substance exact. Only fluff die.
Drop: articles, filler (just/really/basically), pleasantries, hedging.
Fragments OK. Short synonyms. Code unchanged.
Pattern: [thing] [action] [reason]. [next step].
ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift.
Code/commits/PRs: normal. Off: "stop caveman" / "normal mode".

## Project

Streamlit app. Explores MyInvestor investment products. Filters, compares, detail view. Beta MIX advisor engine for portfolio allocation.

Deployed: https://investor26.streamlit.app/

## Files

| File | Role |
|---|---|
| `src/app.py` | Single entrypoint. Streamlit UI + all rendering. |
| `src/productos.py` | Data fetch: API first, fallback to `data/myinvestor.json`. |
| `src/recommendador.py` | MIX advisor: scoring, constraints, weight allocation. |
| `src/simulacion.py` | Scenario simulation + historical proxy paths. |
| `src/explicabilidad.py` | Human-readable recommendation rationale. |
| `src/vars.py` | Constants: CACHE_TTL (6h), local file path/timestamp. |
| `src/queries.py` | SQL query builder for DuckDB filtering. |
| `src/renderers.py` | UI rendering helpers for product detail views. |
| `data/myinvestor.json` | Local product snapshot. Fallback when API unreachable. |
| `ADVISOR.md` | Full MIX engine spec. Authoritative for optimizer logic. |

## Commands

```
uv run streamlit run src/app.py
```

**NEVER** launch streamlit to test (`.venv\Scripts\streamlit run app.py ...`). Hangs terminal, never exits.
Lint: `uv run ruff check --fix .`
Format: `uv run ruff format .`
Test: `uv run pytest tests/ -v`
Run lint + test before commits. No obvious errors pushed.

## Dependencies

`pyproject.toml`: streamlit, pandas, duckdb, dotenv. Dev: ruff.

Manage with `uv`: `uv sync`, `uv add <pkg>`, `uv run <cmd>`.

## Data flow

1. `get_productos()` tries MyInvestor API. Falls back to `data/myinvestor.json`.
2. `data/myinvestor.json` snapshot date tracked in `src/vars.py::LOCAL_FILE_TIMESTAMP`.
3. Results cached 6 hours (`CACHE_TTL`).
4. `duckdb` queries DataFrame for filtering/sorting. SQL built dynamically in `src/app.py`.

## MIX advisor rules

- Universe: only user-selected ISINs.
- Horizon bucketing: nearest lower of {1, 3, 5} years.
- Objective: `return - TER - risk_aversion * volatility`.
- Constraints: long-only, sum=100%, min weight per fund (default 5%).
- Volatility fallback: bucket field → generic `volatilidad` → derived from `indicadorRiesgo` (1-7 scale mapped to 3%-35%).
- Simulation: proxy from aggregate historical stats. NOT a real backtest.
- See `ADVISOR.md` for full spec, assumptions, limitations.

## Quirks

- `.env` has `PRODUCT_JSON_URL` but code hardcodes API URL. Env var unused.
- Default filters: EUR divisa, FONDOS_INDEXADOS product type.
- Only `status = 'OPEN'` products shown.
- Table sorted: risk ASC, TER ASC, ISIN ASC.
- Single row selection opens detail. Auto-open if only one result.
- Search terms comma-separated → OR on ISIN + name (SQL ILIKE).
- Sector filter uses DuckDB UNNEST on nested JSON arrays.
- Spanish locale strings in UI and data.

## Testing

Framework: pytest + pytest-cov. Config in `pyproject.toml`.
Tests: `tests/`. Fixtures in `tests/conftest.py`.

### Test structure

| File | Tests | Coverage |
|---|---|---|
| `tests/test_recommendador.py` | `_to_float`, `_nearest_lower_horizon`, `_build_candidate`, correlation, volatility, `recommend_mix` | 96% |
| `tests/test_queries.py` | SQL generation: filters, sectors, name search | 100% |
| `tests/test_productos.py` | JSON read, DataFrame build, option extraction, download mock | 100% |
| `tests/test_app.py` | Streamlit UI: AppTest, mocks, session state | 63% |
| `tests/test_simulacion.py` | Scenario simulation, historical proxy paths | 97% |
| `tests/test_explicabilidad.py` | Human-readable rationale output | 100% |

### Running tests

```bash
uv run pytest tests/ -v                    # run all tests
uv run pytest tests/test_app.py -v         # run specific file
uv run pytest tests/ --cov=src --cov-report=term-missing  # with coverage
```

### Coverage config (pyproject.toml)

```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=60"
```

Current coverage: **73%** (96 tests, 627 statements, 168 missed).

### Streamlit UI tests (AppTest)

Use `streamlit.testing` AppTest for UI testing:

```python
from streamlit.testing.v1 import AppTest

def test_something():
    at = AppTest.from_file("src/app.py")
    at.run()
    assert at.session_state["key"] == "value"
    at.button[0].click().run()
    assert at.markdown[0].value == "Expected"
```

Key patterns:
- `at.run()` - simulate script rerun
- `at.session_state` - access session state
- `at.button[i].click()` - simulate widget interaction
- `at.markdown[i].value` - assert rendered output
- `at.error` / `at.warning` / `at.success` - check messages

### Mocking

Mock external dependencies to avoid API calls:

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    mock_data = [...]  # fixture data
    with patch("src.app.get_productos") as mock:
        mock.return_value = ("timestamp", mock_data)
        # run test
```

Common mocks:
- `get_productos()` → return `(timestamp, data)` from `data/myinvestor.json`
- `requests.get()` → return mock Response
- `streamlit.cache_data` → disable or mock return

### Fixtures (conftest.py)

```python
import json
import pytest

@pytest.fixture
def productos_json():
    with open("data/myinvestor.json", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def productos_df(productos_json):
    return pd.DataFrame(productos_json)
```

### Adding tests for new code

1. **Pure functions** (`recommendador.py`, `queries.py`, `simulacion.py`):
   - Test inputs → expected outputs directly
   - No mocks needed
   - Use `data/myinvestor.json` as fixture

2. **Streamlit UI** (`app.py`):
   - Use AppTest
   - Mock data sources (`get_productos`)
   - Simulate widget interactions
   - Assert rendered output

3. **API calls** (`productos.py`):
   - Mock `requests.get()` with `unittest.mock.patch`
   - Test both success and failure paths
   - Verify fallback to local file

4. **Coverage gaps** (see `ADVISOR.md` §Extension Path):
   - `app.py` (63%) - add more AppTest scenarios
   - `renderers.py` (12%) - hard to unit test, consider integration tests
