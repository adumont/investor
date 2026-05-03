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

Framework: pytest. Config in `pyproject.toml`.
Tests: `tests/`. Fixtures in `tests/conftest.py`.

| File | Tests |
|---|---|
| `tests/test_recommendador.py` | `_to_float`, `_nearest_lower_horizon`, `_build_candidate`, correlation, volatility, `recommend_mix` |
| `tests/test_queries.py` | SQL generation: filters, sectors, name search |
| `tests/test_productos.py` | JSON read, DataFrame build, option extraction, download mock |

Run: `uv run pytest tests/ -v`

### Adding tests
- Mock `get_productos()` to avoid API calls.
- Test `src/recommendador.py` logic: parser, feasibility, score fallback.
- Use `data/myinvestor.json` as fixture data.
- `ADVISOR.md` §Extension Path lists desired test coverage areas.
