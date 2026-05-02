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

### 2.2 `FILTROS_RAPIDOS` has typo — P2

**File:** `app.py:46`

```python
"World": "categoria = 'Global Equity Large Cap' or categoria = 'Global Equity Lage Cap' ..."
```

`"Lage Cap"` should be `"Large Cap"`. The filter may miss products if the API returns the misspelled category.

**Remediation:** Fix typo to `"Large Cap"`.

### 2.3 `get_general_info_markdown` is dead code — P2

**File:** `app.py:379-381`

Function defined but never called. Returns nothing (implicit `None`) for non-empty case.

**Remediation:** Delete.

### 2.4 `format_bool` is dead code — P2

**File:** `app.py:384-389`

Defined but never called anywhere.

**Remediation:** Delete.

### 2.5 `nombre_producto` assigned but never used — P2

**File:** `app.py:585`

```python
nombre_producto = producto["nombre"]
```

Variable assigned but not referenced.

**Remediation:** Delete or use in expander title.

### 2.6 `getenv` imported but never used — P2

**File:** `app.py:7`

```python
from os import getenv
```

**Remediation:** Delete.

### 2.7 `json` imported but never used — P2

**File:** `app.py:4`

**Remediation:** Delete.

### 2.8 `datetime` imported as module, but only `date` needed — P2

**File:** `app.py:8`

```python
import datetime
```
Used only as `datetime.date.today().year`.

**Remediation:** `from datetime import date` or `import datetime; year = datetime.datetime.now().year`.

### 2.9 `threshold_sector` slider value is `int`, passed to SQL as float — P2

**File:** `app.py:187-193, 130`

The slider returns `int` (step=5, no value format). Interpolated into SQL as `{threshold}`. Works fine for integers but type mismatch is confusing.

**Remediation:** Cast explicitly or document.

### 2.10 `ZONAS.remove("nan")` will crash if list is empty — P1

**File:** `productos.py:49`

If `ZONAS` is empty after `unique()`, `.remove()` raises `ValueError`. Defensive code is inconsistent: `TIPO_ACTIVO` uses `if "nan" in TIPO_ACTIVO: TIPO_ACTIVO.remove("nan")` (safe), but `ZONAS` does not.

**Remediation:** Use consistent guard: `if "nan" in ZONAS: ZONAS.remove("nan")`.

### 2.11 `DIVISAS` not cleaned of NaN — P1

**File:** `productos.py:46`

```python
DIVISAS = _df_productos["divisasDto"].apply(lambda x: x["codigo"]).unique()
```

If `divisasDto` is `None` for any row, the lambda raises `TypeError: 'NoneType' object is not subscriptable`. Other fields use `str(x)` conversion before filtering.

**Remediation:** Guard with `.apply(lambda x: x.get("codigo") if isinstance(x, dict) else None).dropna().unique()`.

---

## 3. Architecture

### 3.1 `app.py` is a monolith (801 lines) — P1

All UI rendering, SQL generation, data fetching, and business logic live in one file. This makes the app hard to test and navigate.

**Remediation:**
- Move SQL generation helpers to a separate module (e.g., `queries.py`).
- Move render functions (`render_*`) to a `views/` package or `renderers.py`.
- Keep `app.py` as orchestration only.

### 3.2 Module-level side effects in `app.py` — P1

**File:** `app.py:54-68`

Data fetching (`get_productos()`), DataFrame construction, and option list generation happen at module level. Every Streamlit rerun re-executes top-level code. Caching in `get_productos()` prevents repeated API calls, but the entire filter setup runs on every rerun regardless.

**Remediation:**
- Wrap initialization in `@st.cache_resource` or use `st.session_state` for one-time setup.
- Consider `if "df_productos" not in st.session_state:` guard.

### 3.3 No separation between data layer and presentation — P1

`productos.py` returns raw dicts from the API. Every consumer (`app.py`, `recommendador.py`) reaches into dict keys directly. No schema validation or typed models.

**Remediation:**
- Introduce a `Product` dataclass or TypedDict.
- Centralize field access in one place so schema changes are isolated.

### 3.4 MIX advisor has no covariance modeling — P2

**File:** `recommendador.py`, `ADVISOR.md` §Limitations

Volatility is computed as weighted sum. No correlation between assets. Two highly correlated funds will appear diversified when they are not. Documented in ADVISOR.md as known limitation, but worth flagging for users who might trust the output more than they should.

**Remediation:** Already documented. Future: add correlation proxy by category overlap (ADVISOR.md §Extension Path).

---

## 4. Performance

### 4.1 SQL query rebuilt on every rerun — P1

**File:** `app.py:204-245`

The entire SQL string is reconstructed on every interaction (filter change, selection, etc.). For ~1000 products this is fast, but DuckDB query execution on every rerun is unnecessary when filters haven't changed.

**Remediation:**
- Cache query results keyed by filter state using `@st.cache_data`.
- Or use `st.session_state` to track last query and skip re-execution.

### 4.2 `get_listas_opciones` iterates full DataFrame multiple times — P2

**File:** `productos.py:46-80`

Nine separate passes over the DataFrame to extract unique values. Each `apply(lambda x: str(x)).unique().tolist()` is a full scan.

**Remediation:**
- Single pass with `agg` or vectorized operations.
- Or convert once: `_df_productos[["zonaGeografica", "categoria", ...]].agg(lambda col: col.dropna().unique().tolist())`.

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

### 7.1 No test suite — P1

No test framework configured. The MIX advisor logic (`recommendador.py`) has non-trivial scoring, constraint, and fallback behavior that is error-prone to verify manually.

**Remediation:**
- Add `pytest` to `requirements.txt`.
- Create `tests/` directory.
- Prioritize: `_to_float`, `_nearest_lower_horizon`, `_build_candidate`, `recommend_mix` feasibility check, score stabilization cases.
- Use `myinvestor.json` as fixture data.
- Mock `get_productos()` for any integration tests.

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
| 3 | `ZONAS.remove("nan")` crashes if absent | P1 | `productos.py:49` |
| 4 | `DIVISAS` extraction crashes on null `divisasDto` | P1 | `productos.py:46` |
| 5 | No timeout on API request | P1 | `productos.py:10` |
| 6 | No HTTP status check before `.json()` | P1 | `productos.py:10` |
| 7 | `read_json_from_file` no error handling | P1 | `productos.py:14-16` |
| 8 | `duckdb.query()` no error handling | P1 | `app.py:264` |
| 9 | Module-level side effects on every rerun | P1 | `app.py:54-68` |
| 10 | No test suite for non-trivial advisor logic | P1 | `recommendador.py` |
| 11 | `app.py` monolith (801 lines) | P1 | `app.py` |
| 12 | SQL rebuilt on every rerun | P1 | `app.py:204-245` |
| 13 | Auto-open detail can't be dismissed for single result | P1 | `app.py:572-578` |
| 14 | Dead code: `get_general_info_markdown`, `format_bool`, `nombre_producto` | P2 | `app.py` |
| 15 | Unused imports: `getenv`, `json` | P2 | `app.py` |
| 16 | Commented-out code blocks | P2 | `app.py` |
| 17 | Typo in `FILTROS_RAPIDOS` ("Lage Cap") | P2 | `app.py:46` |
| 18 | No type hints on public functions | P2 | `productos.py`, `app.py` |
| 19 | Inconsistent import placement | P2 | `productos.py` |
| 20 | Magic numbers in recommendador | P2 | `recommendador.py` |
| 21 | Missing Spanish accents in explicabilidad | P2 | `explicabilidad.py:19` |
| 22 | No CI pipeline | P2 | repo root |
