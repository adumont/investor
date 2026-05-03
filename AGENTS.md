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
| `app.py` | Single entrypoint. Streamlit UI + all rendering. |
| `productos.py` | Data fetch: API first, fallback to `myinvestor.json`. |
| `recommendador.py` | MIX advisor: scoring, constraints, weight allocation. |
| `simulacion.py` | Scenario simulation + historical proxy paths. |
| `explicabilidad.py` | Human-readable recommendation rationale. |
| `vars.py` | Constants: CACHE_TTL (6h), local file path/timestamp. |
| `myinvestor.json` | Local product snapshot. Fallback when API unreachable. |
| `ADVISOR.md` | Full MIX engine spec. Authoritative for optimizer logic. |

## Commands

```
python -m streamlit run app.py
```

**NEVER** launch streamlit to test (`.venv\Scripts\streamlit run app.py ...`). Hangs terminal, never exits.
Use `.venv\Scripts\python -m py_compile <file>.py` for syntax checks.

No tests. No lint. No typecheck. No formatter configured.

`.venv/` exists. Activate before running.

## Dependencies

`requirements.txt`: streamlit, pandas, duckdb, dotenv, pip-tools.

`pip-tools` present but no `requirements.in`. Ignore pip-compile workflow.

## Data flow

1. `get_productos()` tries MyInvestor API. Falls back to `myinvestor.json`.
2. `myinvestor.json` snapshot date tracked in `vars.py::LOCAL_FILE_TIMESTAMP`.
3. Results cached 6 hours (`CACHE_TTL`).
4. `duckdb` queries DataFrame for filtering/sorting. SQL built dynamically in `app.py`.

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

## Adding tests (future)

No test framework configured. If adding tests:
- Mock `get_productos()` to avoid API calls.
- Test `recommendador.py` logic: parser, feasibility, score fallback.
- Use `myinvestor.json` as fixture data.
- `ADVISOR.md` §Extension Path lists desired test coverage areas.
