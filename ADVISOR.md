# MIX Advisor Engine Spec

## Scope
Backend recommendation engine for user-selected ISIN products.
No execution engine. No order routing. No true market time-series backtest.

## Product Goal
Given selected ISIN list and horizon n years:
1. Recommend allocation mix (weights).
2. Maximize risk-adjusted net return after TER.
3. Explain recommendation.
4. Simulate portfolio behavior using available historical aggregate stats.

## Source Modules
- app.py: UI wiring, input collection, output rendering.
- recommendador.py: candidate normalization, constraints, scoring, allocation.
- simulacion.py: scenario path generation, historical proxy path.
- explicabilidad.py: human-readable rationale.

## Inputs
## User Inputs
- selected_isins: list of ISIN strings.
- horizon_years: integer in [1, 30] from UI.
- min_weight_pct: integer percent slider, default 5.
- risk_aversion: float slider in [0.0, 1.0], default 0.35.

## Data Inputs per Product (myinvestor payload)
- codigoIsin
- nombre
- ter
- yearUno, yearTres, yearCinco
- volatilidadYearUno, volatilidadYearTres, volatilidadYearCinco
- volatilidad
- indicadorRiesgo
- rentabilidadPasadaUno..Cinco

## Decision Log (locked)
1. Universe restriction: only user-selected ISIN set.
2. Portfolio constraints: long-only, full investment, minimum 5% per selected fund (UI-configurable currently).
3. Objective type: risk-adjusted net return.
4. TER treatment: yearly TER deducted from expected return and from historical proxy yearly returns.
5. Horizon mapping: nearest lower from {1, 3, 5}.
6. Missing required data: exclude product, keep explicit exclusion reason.
7. Simulation mode: proxy simulation from available annual aggregates.

## Assumptions
1. yearUno/yearTres/yearCinco represent annualized expected return proxies in percentage points.
2. volatilidad* fields represent annualized volatility proxies in percentage points.
3. TER provided as annual percentage points.
4. Risk model uses independent weighted volatility proxy (no covariance matrix available).
5. Historical rentabilidadPasada series can proxy annual outcomes for scenario and historical path.
6. No transaction costs, taxes, slippage, currency hedging effects, or liquidity constraints modeled.

## Data Normalization
Implemented in recommendador.py.

1. Numeric parsing:
- Accept numeric or string values.
- Strip percent sign and convert comma decimal to dot.
- Invalid tokens (empty, dot, N/A, nan, None) treated as missing.

2. Percentage to decimal:
- Returns, TER, volatility converted from percentage points to decimal by dividing by 100.

3. Horizon bucketing:
- if n >= 5 -> use 5Y fields.
- else if n >= 3 -> use 3Y fields.
- else -> use 1Y fields.

4. Volatility fallback chain:
- first volatility for selected bucket.
- else generic volatilidad.
- else derive from indicadorRiesgo with mapping:
  volatility_proxy = clamp((risk/7)*0.30, min=0.03, max=0.35).

5. Historical returns extraction:
- order oldest to newest:
  rentabilidadPasadaCinco, Cuatro, Tres, Dos, Uno.
- each value stored as decimal.

## Candidate Eligibility
A selected product is candidate only if:
1. ISIN found in dataset.
2. Required return for bucket present.
3. Volatility proxy resolvable (direct or fallback).

If any fails: product excluded with reason.

## Optimization Algorithm
Implemented in recommendador.py::recommend_mix.

Given candidates i = 1..N:
- mu_i = expected return decimal.
- ter_i = TER decimal.
- vol_i = volatility proxy decimal.
- lambda = risk_aversion.
- min_w = minimum weight constraint.

### Raw score per asset
raw_i = mu_i - ter_i - lambda * vol_i

### Score stabilization
Case A: max(raw_i) <= 0
- fallback_i = max(0.0001, mu_i - ter_i)
- score_i = fallback_i

Case B: otherwise
- if min(raw_i) <= 0 shift all scores by (-min(raw_i) + 0.0001)
- else no shift
- score_i = shifted raw_i

If sum(score_i) <= 0 then uniform score_i = 1.

### Constraints
1. long-only: w_i >= 0.
2. minimum allocation: w_i >= min_w.
3. full investment: sum_i w_i = 1.
4. feasibility check: N * min_w <= 1; else explicit error.

### Weight construction
free_weight = 1 - N * min_w
w_i = min_w + free_weight * (score_i / sum(score))

### Portfolio diagnostics
Computed and returned:
- expected_gross = sum(w_i * mu_i)
- ter_drag = sum(w_i * ter_i)
- net_expected = expected_gross - ter_drag
- volatility_proxy = sum(w_i * vol_i)
- objective = sum(w_i * (mu_i - ter_i - lambda*vol_i))

Also per-asset contributions:
- gross_contribution
- ter_contribution
- risk_contribution
- objective_contribution

## Simulation Algorithms
Implemented in simulacion.py.

## Scenario annual rates
From allocation output:
- Base annual rate = portfolio net_expected.
- Optimistic annual rate = weighted max historical annual return per asset minus TER.
- Conservative annual rate = weighted min historical annual return per asset minus TER.

For each scenario s and year t in 1..n:
value_t = value_{t-1} * (1 + rate_s)

Outputs per point:
- scenario
- year
- annual_return
- portfolio_value
- cumulative_return

## Historical proxy path
Goal: show realized-style trajectory over available aggregate past annual values.

Method:
1. Determine max available history length across assets.
2. Effective years = min(requested years, max length), at least 1 when history exists.
3. Use only most recent effective window.
4. For each proxy year index:
- weighted_return = sum(w_i * (hist_i - ter_i)) across assets with value for that index.
- covered_weight = sum(w_i) for assets providing value.
- normalized_return = weighted_return / covered_weight.
- compound path with normalized_return.

Outputs per point:
- year_index (window-local 1..effective_years)
- coverage_weight
- annual_return
- portfolio_value
- cumulative_return

## Explainability Algorithm
Implemented in explicabilidad.py.

Narrative includes:
1. Requested horizon and effective bucket rule.
2. Objective formula in text.
3. Portfolio gross expected return.
4. TER aggregate drag.
5. Portfolio net expected return.
6. Portfolio volatility proxy.
7. Top allocations (up to 3 by weight).
8. Exclusion list with reasons.
9. Disclaimer: proxy simulation, not complete time-series backtest.

## Error Handling
recommendador.py raises RecommendationError when:
1. No selected ISIN.
2. No valid candidates after exclusion.
3. Infeasible minimum weight constraints.

app.py catches and renders user-facing error.

## Output Contract
recommend_mix returns dict with keys:
- horizon_years
- horizon_bucket
- risk_aversion
- min_weight
- allocations: list of asset diagnostics
- excluded: list of exclusion records
- portfolio: aggregate diagnostics

build_simulation returns dict with keys:
- scenarios
- paths
- historical_proxy

build_recommendation_explanation returns markdown bullet string.

## UI Integration (current)
Asesor MIX block in app.py:
1. ISIN multiselect from filtered table universe.
2. Inputs for horizon, min weight, risk aversion.
3. Metrics cards for net expected, TER drag, volatility proxy, bucket.
4. Allocation table with percent formatting.
5. Explanation markdown.
6. Scenario line chart.
7. Historical proxy line chart.
8. Exclusions table when present.

## Limitations
1. No covariance matrix; diversification effects approximated only through weighted volatility.
2. Scenario optimistic/conservative built from per-asset historical extrema, not joint distribution.
3. Historical proxy coverage can be below 100% when some assets miss years.
4. Horizon mapping currently discrete and lower-bound only.
5. Risk aversion calibration static slider, no automatic tuning.
6. No bootstrap/Monte Carlo distribution.

## Extension Path (non-breaking)
1. Add covariance proxy by category/region similarity and move to mean-variance optimization.
2. Add CVaR or downside-risk objective option.
3. Add robust handling for extreme TER or stale history dates.
4. Add stress scenarios (inflation shock, rate shock) as deterministic overlays.
5. Add export endpoints for weights and paths.
6. Add unit tests for parser, feasibility, score fallback, proxy coverage behavior.
