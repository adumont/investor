# Code Review — Investor (Streamlit)

**Date:** 2026-05-02
**Scope:** All Python source files, data layer, MIX advisor engine, simulation, UI.
**Severity scale:** P0 (must fix — security/correctness), P1 (should fix — robustness/maintainability), P2 (nice to have — style/nit).

---

## 1. Security

### 1.1 Hardcoded API token — P0

**File:** `productos.py:26`

```python
productos=download_json_from_url("https://api.myinvestor.es/...?token=a2e8e18ad26a079c576038f0ad4fa18ce0d9e415f5bf6f43f89cf3831a0e4685__")
```

The API token is committed in source and exposed to anyone who can read the deployed app (visible in network calls if the endpoint is intercepted). `.env` has `PRODUCT_JSON_URL` but is ignored.

**Remediation:**
- Move token to env var (reuse `PRODUCT_JSON_URL` or add `MYINVESTOR_API_TOKEN`).
- Read from `os.environ` in `productos.py`.
- Add `.env` to `.gitignore` (already done), ensure token never committed.
- If token is meant to be public, document that explicitly.

### 1.2 SQL injection via user input — P0

**File:** `app.py:78-86, 105-119, 122-131, 134-144`

User-supplied search terms, filter options, and sector names are interpolated directly into SQL strings. Single-quote escaping (`replace("'", "''")`) is applied but this is manual defense, not parameterized queries. DuckDB supports parameterized queries via `?` placeholders.

Attack surface:
- Search terms: escaped, acceptable but fragile.
- Quick filters (`FILTROS_RAPIDOS`): hardcoded, safe.
- `get_filtro_sql`: options from dropdown, safe in current flow.
- `get_filtro_sector_sql`: sector names from dropdown, `threshold` is numeric from slider, safe in current flow.
- `get_sector_columns_sql`: sector names from dropdown, safe in current flow.

Risk is low because options originate from controlled dropdown lists, but the pattern is dangerous if inputs ever become user-editable.

**Remediation:**
- Use DuckDB parameterized queries (`duckdb.query(...).to_df(params=[...])`) where possible.
- For dynamic column/UNNEST queries that cannot be parameterized, add an allowlist validation step.

### 1.3 Morningstar URL construction — P2

**File:** `app.py:440`

```python
f"https://www.morningstar.es/es/funds/snapshot/snapshot.aspx?id={producto.get('secIdFondoMorningstar')}"
```

`secIdFondoMorningstar` comes from the API payload. Not a direct user input, but if API data is compromised, this becomes an open redirect. Low risk.

**Remediation:** Validate the value is alphanumeric before interpolation.

---

## 2. Correctness

### 2.1 `get_listas_opciones` mutates cached DataFrame — P1

**File:** `productos.py:46-71`

The function calls `.apply()` and `.unique()` on `_df_productos`. Since the DataFrame is passed by reference and the function is cached, repeated calls with the same DataFrame object are safe. However, the function does `ZONAS.remove("nan")` — if `"nan"` is not in the list, this raises `KeyError` and crashes the app on startup. Same pattern for `TIPO_ACTIVO`, `CATEGORIAS`, etc.

**Remediation:**
- Use `ZONAS = [z for z in ZONAS if z != "nan"]` or `ZONAS.discard("nan")` pattern.
- Better: filter at source — `dropna()` before `str()` conversion.

### 2.2 `FILTROS_RAPIDOS` has typo — P2 ✅ Won't Fix

**File:** `app.py:46`

```python
"World": "categoria = 'Global Equity Large Cap' or categoria = 'Global Equity Lage Cap' ..."
```

`"Lage Cap"` should be `"Large Cap"`. The filter may miss products if the API returns the misspelled category.

**Remediation:** Fix typo to `"Large Cap"`.

**Status:** Won't fix. `"Lage Cap"` is the raw category value as stored by the API. Both spellings are matched so the filter works correctly. Comment added to prevent future "fix".

### 2.3 `get_general_info_markdown` is dead code — P2 ✅ Fixed

**File:** `app.py:379-381`

Function defined but never called. Returns nothing (implicit `None`) for non-empty case.

**Status:** Deleted.

### 2.4 `format_bool` is dead code — P2 ✅ Fixed

**File:** `app.py:384-389`

Defined but never called anywhere.

**Status:** Deleted.

### 2.5 `nombre_producto` assigned but never used — P2 ✅ Fixed

**File:** `app.py:585`

```python
nombre_producto = producto["nombre"]
```

Variable assigned but not referenced.

**Status:** Deleted.

### 2.6 `getenv` imported but never used — P2 ✅ Fixed

**File:** `app.py:7`

**Status:** Deleted.

### 2.7 `json` imported but never used — P2 ✅ Fixed

**File:** `app.py:4`

**Status:** Deleted.

### 2.8 `datetime` imported as module, but only `date` needed — P2 ✅ Fixed

**File:** `app.py:8`

```python
import datetime
```
Used only as `datetime.date.today().year`.

**Status:** Changed to `from datetime import date`, call is now `date.today().year`.

### 2.9 `threshold_sector` slider value is `int`, passed to SQL as float — P2

**File:** `app.py:187-193, 130`

The slider returns `int` (step=5, no value format). Interpolated into SQL as `{threshold}`. Works fine for integers but type mismatch is confusing.

**Remediation:** Cast explicitly or document.

### 2.10 `ZONAS.remove("nan")` will crash if list is empty — P1 ✅ Fixed

**File:** `productos.py:49`

If `ZONAS` is empty after `unique()`, `.remove()` raises `ValueError`. Defensive code is inconsistent: `TIPO_ACTIVO` uses `if "nan" in TIPO_ACTIVO: TIPO_ACTIVO.remove("nan")` (safe), but `ZONAS` does not.

**Status:** Fixed in 4.2 — replaced with `dropna()` which is inherently safe.

### 2.11 `DIVISAS` not cleaned of NaN — P1 ✅ Fixed

**File:** `productos.py:46`

```python
DIVISAS = _df_productos["divisasDto"].apply(lambda x: x["codigo"]).unique()
```

If `divisasDto` is `None` for any row, the lambda raises `TypeError: 'NoneType' object is not subscriptable`. Other fields use `str(x)` conversion before filtering.

**Remediation:** Guard with `.apply(lambda x: x.get("codigo") if isinstance(x, dict) else None).dropna().unique()`.

**Status:** Fixed in 4.2 — lambda now uses `x.get("codigo")` with `isinstance` guard + `dropna()`.

### 2.12 `@cache_data` ignores stale data after refresh — P1 ✅ Fixed

**Files:** `productos.py:42-43`, `app.py:147-149, 287-289`

Three cached functions depend on product data but exclude it from cache keys:
- `get_listas_opciones(_df_productos)` — `_` prefix excludes DataFrame from hash. Cache key is constant.
- `run_query(_df_productos, query)` — DataFrame excluded. `query` is hashed, but same SQL on fresh data returns stale result.
- `get_producto_by_isin(isin)` — closes over `productos_lista` from module scope, not passed as argument.

When `get_productos()` refreshes after 6h TTL: new data arrives, new `df_productos` is built, but all three functions return cached stale values until their own 6h TTL independently expires.

**Remediation:**
- Pass `timestamp_products` (from `get_productos()`) as non-underscore `data_version` argument to all cached functions.
- Cache key now includes data version. When data refreshes, all downstream caches miss immediately.

**Status:** Fixed. All 3 cached functions now accept `data_version: str` (non-underscore). Call sites pass `timestamp_products`. Cache keys invalidate on data refresh. `get_producto_by_isin` no longer closes over module-scoped `productos_lista`.

### 2.13 Filter option lists unsorted and whitespace pollution in sort — P2 ✅ Fixed

**File:** `productos.py:46-91`

Filter dropdowns appeared in arbitrary API order. Additionally, `" PARETO ASSET MANAGEMENT AS"` (leading space) sorted before `"A&G"` because `sorted()` uses byte-order comparison.

**Remediation:**
- Sort all returned lists with `sorted(x, key=lambda s: str(s).strip().casefold())`.
- Strip applied only to sort key, not to stored values — exact-match SQL filters still find `" PARETO ..."` correctly.
- `map()` applies sort to entire tuple in one pass.

**Status:** Fixed. All 9 filter option lists sorted case-insensitively. Raw values preserved for SQL exact matching.

---

## 3. Architecture

### 3.1 `app.py` is a monolith (801 lines) — P1 ✅ Fixed

All UI rendering, SQL generation, and business logic lived in one file.

**Remediation:**
- Moved SQL generation helpers to `queries.py` (`get_filtro_sql`, `get_filtro_sector_sql`, `get_sector_columns_sql`).
- Moved all `render_*` functions and helpers (`to_float`, `format_text`, `has_value`, `format_percent_from_decimal`) to `renderers.py`.
- `app.py` now serves as orchestration only (~290 lines).

**Status:** Fixed. `app.py` reduced from 797 to ~290 lines. `queries.py` and `renderers.py` created.

### 3.2 Module-level side effects in `app.py` — P1 ✅ Fixed

**File:** `app.py:54-68`

Data fetching (`get_productos()`), DataFrame construction, and option list generation happened at module level. Every Streamlit rerun re-executed top-level code.

**Remediation:**
- Wrapped initialization in `@st.cache_resource` function `init_app_data()`.
- On rerun, Streamlit reruns the script but `@st.cache_resource` returns cached result without re-executing the init logic.

**Status:** Fixed. Module-level side effects eliminated. `init_app_data()` uses `@st.cache_resource` to run once per session.

### 3.3 No separation between data layer and presentation — P1

`productos.py` returns raw dicts from the API. Every consumer (`app.py`, `recommendador.py`) reaches into dict keys directly. No schema validation or typed models.

**Remediation:**
- Introduce a `Product` dataclass or TypedDict.
- Centralize field access in one place so schema changes are isolated.

### 3.4 MIX advisor has no covariance modeling — P2 ✅ Fixed

**File:** `recommendador.py`, `ADVISOR.md` §Limitations

Volatility is computed as weighted sum. No correlation between assets. Two highly correlated funds will appear diversified when they are not. Documented in ADVISOR.md as known limitation, but worth flagging for users who might trust the output more than they should.

**Remediation:** Already documented. Future: add correlation proxy by category overlap (ADVISOR.md §Extension Path).

**Status:** Fixed. Added `_build_correlation_matrix()` with heuristic correlation levels:
- Same `categoriaMstar`/`categoria`: 0.85
- Same `zonaGeografica`: 0.60
- Same `tipoActivo`: 0.40
- Default: 0.20

Portfolio volatility now uses `sqrt(w^T * Σ * w)` where `Σ[i][j] = corr[i][j] * vol_i * vol_j`.
When all corr=1.0, reduces to original weighted sum. Diversification credit shown when assets differ.
Correlation levels are heuristics — not real market data. Updated ADVISOR.md limitation note.

---

## 4. Performance

### 4.1 SQL query rebuilt on every rerun — P1 ✅ Fixed

**File:** `app.py:204-245`

The entire SQL string is reconstructed on every interaction (filter change, selection, etc.). For ~1000 products this is fast, but DuckDB query execution on every rerun is unnecessary when filters haven't changed.

**Remediation:**
- Cache query results keyed by filter state using `@st.cache_data`.
- Or use `st.session_state` to track last query and skip re-execution.

**Status:** Fixed. Added `@st.cache_data` wrapper `run_query(_df_productos, query)` keyed on the SQL string. Same filters → cache hit. Different filters → fresh execution.

### 4.2 `get_listas_opciones` iterates full DataFrame multiple times — P2 ✅ Fixed

**File:** `productos.py:46-80`

Nine separate passes over the DataFrame to extract unique values. Each `apply(lambda x: str(x)).unique().tolist()` is a full scan.

**Remediation:**
- Single pass with `agg` or vectorized operations.
- Or convert once: `_df_productos[["zonaGeografica", "categoria", ...]].agg(lambda col: col.dropna().unique().tolist())`.

**Status:** Fixed. Replaced 6 repeated `apply(...).unique().tolist()` + `.remove("nan")` passes with single `.agg()` on string columns. Also fixed `DIVISAS` crash on null `divisasDto` and `SECTORES` dedup via `set()`.

### 4.3 `render_comisiones`, `render_sectores`, `render_regiones` build markdown strings in loops — P2

String concatenation in Python loops is O(n²). For small lists (sectors, regions) this is fine, but the pattern is fragile.

**Remediation:** Use `"\n".join(...)` with a generator expression.

---

## 5. Error Handling & Resilience

### 5.1 `download_json_from_url` has no timeout — P1

**File:** `productos.py:8-11`

```python
response = requests.get(url)
```

No `timeout` parameter. If the API hangs, the app blocks indefinitely.

**Remediation:** Add `timeout=30` or similar.

### 5.2 `download_json_from_url` does not check HTTP status — P1

**File:** `productos.py:10`

`response.json()` will raise `JSONDecodeError` on non-200 responses (e.g., 500, 403) instead of falling through to the fallback. The bare `except Exception` in `get_productos()` catches it, but the error message is unhelpful.

**Remediation:** Call `response.raise_for_status()` before `.json()`.

### 5.3 `read_json_from_file` has no error handling — P1

**File:** `productos.py:14-16`

If `myinvestor.json` is missing or corrupted, this raises `FileNotFoundError` or `json.JSONDecodeError`. The caller (`get_productos`) will propagate the exception to the user as a raw traceback.

**Remediation:** Wrap in try/except with user-friendly fallback message.

### 5.4 `duckdb.query(query).df()` has no error handling — P1

**File:** `app.py:264`

If the dynamically generated SQL is malformed (e.g., from edge-case filter combinations), DuckDB raises an exception that crashes the app.

**Remediation:** Wrap in try/except, show `st.error` with SQL for debugging.

### 5.5 `productos.py:29` bare `except Exception` swallows errors — P2

**File:** `productos.py:29`

Catches everything including `KeyboardInterrupt`, `SystemExit`, and programming errors. At minimum, catch specific exceptions.

**Remediation:** `except (requests.RequestException, json.JSONDecodeError) as e:`

---

## 6. Code Quality & Style

### 6.1 No type hints on public functions — P2

**Files:** `productos.py`, `app.py` (most functions)

`get_productos`, `get_df_productos`, `get_listas_opciones`, all `render_*` functions, `to_float`, `format_text`, `has_value`, `format_percent_from_decimal` — all lack type annotations.

**Remediation:** Add type hints. Especially valuable for `render_*` functions which take complex dict structures.

### 6.2 Inconsistent import placement — P2

**File:** `productos.py`

Imports inside functions (`import requests` at line 8, `import pandas as pd` at lines 37, 44, `from vars import ...` at line 32). This is sometimes done for Streamlit caching, but it's inconsistent.

**Remediation:** If imports are for cache isolation, add comments explaining why. Otherwise, move to top of file.

### 6.3 Commented-out code blocks — P2

**Files:** `app.py:32-42, 247-259, 607-617`

Multiple blocks of commented-out code remain. Clutters the file and confuses readers about what the current logic is.

**Remediation:** Delete. Git has the history.

### 6.4 `_filter_terms` and `_filter_name_sql` use leading underscore inconsistently — P2

**File:** `app.py:78-86`

Private naming suggests internal use, but these variables are in module scope and used only once below.

**Remediation:** Either use consistently or drop underscore convention.

### 6.5 `get_filtro_sql` does not handle `"Cualquiera"` in multiselect — P2

**File:** `app.py:105-119`

The function checks `"Cualquiera" in options`, but multiselect widgets don't include "Cualquiera" as an option — that's only for the quick filter selectbox. The check is dead logic.

**Remediation:** Remove the `"Cualquiera"` check from `get_filtro_sql`.

### 6.6 Magic numbers — P2

**Files:** `recommendador.py:101, 186, 190, 195`

- `0.03`, `0.35`, `0.30` in volatility derivation — documented in ADVISOR.md but not as constants.
- `0.0001` in score stabilization — no explanation in code.
- `1.0` in feasibility check — clear but could be `TOTAL_WEIGHT = 1.0`.

**Remediation:** Extract to named constants in `recommendador.py` or `vars.py`.

### 6.7 `simulacion.py` `_weighted_extreme` mode string is unchecked — P2

**File:** `simulacion.py:22-33`

`mode` parameter accepts any string. If called with something other than `"max"` or `"min"`, it silently uses `base` return, which may be unexpected.

**Remediation:** Use `Literal["max", "min"]` type hint and validate.

### 6.8 `explicabilidad.py` uses `anos`/`mas` without accent — P2

**File:** `explicabilidad.py:19`

```
"Horizonte solicitado: {horizon} anos. Regla aplicada: horizonte inferior mas cercano"
```

Missing accents (`años`, `más`). Minor, but inconsistent with the rest of the Spanish UI.

**Remediation:** Fix to `años`, `más`.

---

## 7. Testing Gaps

### 7.1 No test suite — P1 ✅ Fixed

No test framework configured. The MIX advisor logic (`recommendador.py`) has non-trivial scoring, constraint, and fallback behavior that is error-prone to verify manually.

**Status:** Fixed. Test suite implemented:
- `pyproject.toml`: added `pytest` to `[project.optional-dependencies] dev`, configured `pythonpath = ["src"]`.
- `tests/conftest.py`: fixtures for `myinvestor.json`, `sample_product`, `mock_get_productos`.
- `tests/test_recommendador.py`: 20 tests covering `_to_float`, `_nearest_lower_horizon`, `_build_candidate`, `_get_volatility`, correlation matrix, portfolio volatility, `recommend_mix` (feasibility, weights, exclusions, score stabilization).
- `tests/test_queries.py`: 15 tests covering SQL generation (`get_filtro_sql`, `build_name_filter_sql`, `get_filtro_sector_sql`, `get_sector_columns_sql`, `build_product_query`).
- `tests/test_productos.py`: 9 tests covering `read_json_from_file`, `get_df_productos`, `_extract_options` (null handling, sorting), `download_json_from_url` (mocked).
- Total: **54 tests**, all passing.

Run: `uv run pytest tests/ -v`

### 7.2 No CI pipeline — P2

No `.github/workflows/` or equivalent. Changes to the app are not validated before deployment.

**Remediation:** Add a minimal GitHub Actions workflow: `pip install -r requirements.txt && python -m streamlit run app.py --headless --server.headless true` (or just lint/typecheck if tests are added later).

---

## 8. Data & Streamlit Quirks

### 8.1 `st.session_state` used for only one variable — P2

**File:** `app.py:28-29`

Only `threshold_sector` is stored in session state. All other filter selections are lost on rerun (but that's fine for Streamlit's model).

**Remediation:** No action needed unless filter persistence is desired.

### 8.2 Auto-open detail on single result — P1 (UX quirk, not bug)

**File:** `app.py:572-578`

```python
if selected_row_index is not None and 0 <= selected_row_index < len(df):
    selected_isin = df.iloc[selected_row_index]["codigoIsin"]
elif df.shape[0] == 1:
    selected_isin = df.iloc[0]["codigoIsin"]
```

When only one result exists, detail auto-opens. But after the user clicks away (clears selection), the single result still auto-opens on every rerun. No way to dismiss the detail view for single-result queries.

**Remediation:** Track whether user explicitly dismissed the auto-open in `st.session_state`.

### 8.3 `FILTROS_RAPIDOS` SQL fragments are hardcoded strings — P2

**File:** `app.py:44-52`

SQL is embedded in Python dict. Not parameterized. Safe because values are hardcoded, but any future maintainer adding a filter might not realize this is SQL.

**Remediation:** Add a comment: `# WARNING: values are SQL fragments, not user input.`

---

## Summary by Priority

| # | Issue | Severity | File(s) |
|---|---|---|---|
| 1 | Hardcoded API token in source | P0 | `productos.py:26` |
| 2 | SQL injection pattern (manual escaping, not parameterized) | P0 | `app.py:78-144` |
| 3 | `ZONAS.remove("nan")` crashes if absent ✅ Fixed | P1 | `productos.py:49` |
| 4 | `DIVISAS` extraction crashes on null `divisasDto` ✅ Fixed | P1 | `productos.py:46` |
| 5 | No timeout on API request | P1 | `productos.py:10` |
| 6 | No HTTP status check before `.json()` | P1 | `productos.py:10` |
| 7 | `read_json_from_file` no error handling | P1 | `productos.py:14-16` |
| 8 | `duckdb.query()` no error handling | P1 | `app.py:264` |
| 9 | Module-level side effects on every rerun ✅ Fixed | P1 | `app.py` → `@st.cache_resource` |
| 10 | No test suite for non-trivial advisor logic ✅ Fixed | P1 | `tests/` |
| 11 | `app.py` monolith (801 lines) ✅ Fixed | P1 | `app.py` → `queries.py`, `renderers.py` |
| 12 | SQL rebuilt on every rerun ✅ Fixed | P1 | `app.py:204-245` |
| 13 | Auto-open detail can't be dismissed for single result | P1 | `app.py:572-578` |
| 14 | `@cache_data` ignores stale data after refresh ✅ Fixed | P1 | `productos.py:42, app.py:147,287` |
| 15 | Dead code: `get_general_info_markdown`, `format_bool`, `nombre_producto` ✅ Fixed | P2 | `app.py` |
| 16 | Unused imports: `getenv`, `json` ✅ Fixed | P2 | `app.py` |
| 17 | Commented-out code blocks | P2 | `app.py` |
| 18 | Typo in `FILTROS_RAPIDOS` ("Lage Cap") ✅ Won't Fix | P2 | `app.py:46` |
| 19 | No type hints on public functions | P2 | `productos.py`, `app.py` |
| 20 | Inconsistent import placement | P2 | `productos.py` |
| 21 | Magic numbers in recommendador | P2 | `recommendador.py` |
| 22 | Missing Spanish accents in explicabilidad | P2 | `explicabilidad.py:19` |
| 23 | No CI pipeline | P2 | repo root |
| 24 | Filter option lists unsorted, whitespace pollutes sort ✅ Fixed | P2 | `productos.py:46-91` |
| 25 | `datetime` imported as module, only `date` needed ✅ Fixed | P2 | `app.py:8` |
| 26 | `ZONAS.remove("nan")` crashes if absent ✅ Fixed | P1 | `productos.py:49` |
| 27 | MIX advisor has no covariance modeling ✅ Fixed | P2 | `recommendador.py` |
