## IDEAS.md — Future Feature Backlog

### Data Source Note

Many features below (correlation heatmap, drawdown analysis, benchmark comparison, factor exposure, currency risk) require historical price/return data that the MyInvestor API does not provide. Use **investpy** (`pip install investpy`) for real financial data fetching:

- **Historical prices:** Daily OHLCV for stocks, ETFs, funds, indices, bonds, currencies
- **Benchmarks:** MSCI World, S&P 500, Euribor, EONIA, FTSE All-World data
- **Currency pairs:** EUR/USD, EUR/GBP, EUR/JPY for FX exposure analysis
- **Bond yields:** Government/corporate yields for fixed income benchmarks
- **Economic indicators:** Inflation, rates for macro scenario context

**Caveats:** investpy scrapes Investing.com — rate-limit requests, handle errors gracefully, cache aggressively. Consider it a complementary source to MyInvestor API, not a replacement. For production, evaluate paid APIs (Morningstar, Bloomberg, Refinitiv) for reliability.

### High Priority

#### 1. Drawdown Analysis

**What:** Compute and visualize maximum drawdown (peak-to-trough decline), average recovery time, underwater charts (current drawdown over time), and stress-test portfolios against historical crisis scenarios (2008 GFC, 2020 COVID crash, 2022 rate hike cycle). Show worst N-year rolling returns per asset so users can see what the "bad case" actually looked like historically.

**Value:** Investors live through drawdowns, not averages. A portfolio with 12% expected return but 45% max drawdown may be psychologically impossible to hold. Showing drawdown profiles helps users:
- Set realistic expectations for downside risk beyond volatility alone
- Understand how long capital might be underwater before recovery
- Test if their portfolio would have survived past crises
- Compare funds not just on return but on pain tolerance required
- Avoid selling at the bottom by knowing drawdowns are normal

Drawdown analysis converts abstract risk numbers into concrete "what's the worst I'd face" scenarios — the single most important risk metric for real investors.

---

#### 2. Goal-Based Planning

**What:** Let users input a financial goal (target amount, time horizon, initial capital, monthly contribution). The app computes the required allocation to reach the goal, the probability of success given historical returns, and how much to increase/decrease contributions if the target is off track. Visual tracker shows projected wealth path with confidence bands.

**Value:** Most investors don't want "optimal portfolios" — they want to reach a goal (retirement, house, education). Goal-based planning:
- Translates abstract returns into "will I have enough?"
- Shows the gap between current plan and target in euros, not percentages
- Answers the actionable question: "how much more should I save monthly?"
- Reduces anxiety by showing probability ranges, not single-point predictions
- Prevents over/under-saving with concrete numbers
- Creates emotional commitment to the plan (behavioral finance benefit)

This shifts the app from "interesting analysis tool" to "financial planning companion."

---

#### 3. Benchmark Comparison

**What:** Compare any portfolio or fund against relevant benchmarks — MSCI World for global equity, Euribor for fixed income, 60/40 balanced index, or custom benchmark compositions. Track alpha (excess return), beta (sensitivity to benchmark), Sharpe ratio differential, and information ratio. Visualize periods of outperformance/underperformance with attribution.

**Value:** A fund returning 8% sounds good until you learn its benchmark returned 11%. Benchmarking provides:
- Context for performance — is the fund actually adding value?
- Detection of closet indexers (charging active fees for passive returns)
- Understanding of market vs manager contribution to returns
- Confidence that chosen funds earn their fees
- Awareness of when to stay the course vs reconsider

Without benchmarking, investors cannot distinguish skill from luck or market beta from alpha.

---

#### 4. Correlation Heatmap

**What:** Compute and display pairwise correlation matrix for selected assets using historical returns data. Visual heatmap with color intensity showing correlation strength. Auto-cluster similar assets and highlight positions where the portfolio is accidentally concentrated (correlated bets masquerading as diversification).

**Value:** The covariance proxy we added uses heuristics. Real correlation data reveals:
- Whether "diversified" portfolios actually hold correlated assets
- Hidden concentration risk (e.g., two funds with different names but same holdings)
- True diversification benefit from combining specific assets
- Which pairs provide genuine offsetting behavior
- When correlation spikes during crises (diversification disappears when needed most)

A heatmap makes correlation intuitive — investors see at a glance if their portfolio is genuinely diversified or just seems that way.

---

#### 5. Cost Impact Visualization

**What:** Show how TER compounds over 10/20/30 years on a given investment. Include entry/exit fees, performance fees, and hidden costs. Side-by-side chart: gross wealth vs net wealth over time. Compare cost impact of two similar funds with different fee structures. Show the "cost in lost euros" not just percentage points.

**Value:** Costs are the single most predictable factor in future returns. A 0.20% difference in TER becomes €15,000+ over 30 years on a €50,000 investment. Cost visualization:
- Makes invisible costs visible and emotionally salient
- Helps investors justify choosing cheaper index funds over expensive active funds
- Shows that small fee differences compound to large absolute amounts
- Exposes when entry/exit fees destroy expected alpha
- Encourages fee negotiation or share class selection (institutional vs retail)

Investors who see cost impact in euros, not basis points, make dramatically different fund choices.

---

### Medium Priority

#### 6. Portfolio Performance Attribution

**What:** Break down portfolio returns by asset class (equity vs fixed income vs alternatives), region (Europe, US, Emerging Markets), sector (tech, healthcare, financials), and style (value vs growth). Show each holding's contribution to total return and total risk. Identify which positions are driving performance and which are drag.

**Value:** Attribution answers "why did my portfolio go up or down?" — essential for:
- Understanding if returns come from smart allocation or one lucky bet
- Identifying underperforming positions that should be replaced
- Confirming that the portfolio matches intended exposure
- Detecting unintended concentrations (e.g., 40% tech without knowing it)
- Communicating portfolio drivers to partners or advisors
- Learning which allocation decisions added vs destroyed value

Without attribution, investors are flying blind on what actually moves their portfolio.

---

#### 7. Currency Risk Analysis

**What:** Break down portfolio exposure by underlying currency (EUR, USD, GBP, JPY, etc.). Compare hedged vs unhedged share classes for the same fund. Show historical currency drag/contribution — how much of a fund's return came from FX moves vs underlying asset performance. Alert when currency concentration exceeds thresholds.

**Value:** Many European investors buy USD-denominated funds without realizing they're making an implicit FX bet. Currency analysis:
- Reveals hidden currency exposure that can erase asset gains
- Helps decide whether hedged or unhedged share class is appropriate
- Shows that a "European" fund can have 60% USD revenue exposure
- Quantifies how much EUR/USD moves contributed to returns
- Prevents unpleasant surprises when currency reverses

For non-US investors, currency risk can be 30-50% of total portfolio volatility — yet most never measure it.

---

#### 8. ESG/SRI Scoring

**What:** Integrate Morningstar Sustainability Ratings and other ESG data. Show portfolio-weighted ESG score. Allow filtering to exclude specific categories (fossil fuels, weapons, tobacco, gambling). Compare ESG score of user's portfolio vs benchmark. Show carbon footprint estimation.

**Value:** Growing segment of investors (especially younger demographics) want their money aligned with values. ESG features:
- Enable values-based investing without sacrificing analytical rigor
- Show that ESG funds may have comparable returns (dispelling the myth)
- Allow exclusion of controversial industries per user preference
- Provide transparency on what their money actually funds
- Meet regulatory requirements (SFDR, EU taxonomy disclosure)
- Differentiate the app from generic portfolio tools

ESG is not just ethical — it's increasingly a regulatory and risk management requirement.

---

#### 9. Rebalancing Alerts

**What:** Monitor portfolio allocation drift from target weights. Alert when any position exceeds its target band by a configurable threshold (e.g., ±5%). Suggest specific trades to rebalance — which positions to trim and which to add. Consider tax impact: prefer selling positions with losses or longest holding periods to minimize capital gains tax.

**Value:** Portfolios drift naturally — winning positions grow, losing ones shrink. Without rebalancing:
- Risk profile silently shifts (becomes more aggressive after rallies)
- Diversification erodes (largest position dominates)
- Investors chase past performance instead of maintaining discipline
- Tax inefficiency accumulates from ad-hoc selling

Rebalancing alerts enforce discipline, reduce emotional decision-making, and can improve risk-adjusted returns by forcing "buy low, sell high" systematically. Tax-aware suggestions save real money.

---

#### 10. Factor Exposure Analysis

**What:** Map portfolio holdings to recognized investment factors: value (low P/E, P/B), growth (high revenue growth), quality (high ROE, low debt), momentum (price trend), low volatility (stable returns), size (market cap). Display Morningstar-style style box. Show which factors the portfolio is tilted toward and how much each factor contributes to expected returns.

**Value:** Modern portfolio theory has evolved beyond asset class to factor diversification. Factor analysis:
- Reveals that two "different" funds may share the same factor exposure
- Shows whether expected returns come from factor premia or manager skill
- Helps construct truly diversified portfolios across factors, not just assets
- Identifies factor concentration (e.g., heavy growth tilt disguised as diversification)
- Enables tilting toward factors with strong long-term evidence
- Educates investors on what actually drives returns beyond "stocks vs bonds"

Factor-aware investors build more robust portfolios because they diversify across return drivers, not just labels.

---

### Low Priority / Nice to Have

#### 11. Liquidity Analysis

**What:** Show redemption settlement periods per fund (T+2, T+5, etc.). Flag funds with lock-up periods, gates, or suspension clauses. Recommend appropriate cash buffer based on portfolio liquidity profile and investor's potential near-term cash needs. Alert when portfolio includes illiquid assets that cannot be sold quickly in emergencies.

**Value:** Liquidity risk is invisible until you need money. Investors discover too late that:
- Some funds take weeks to redeem
- Certain assets can suspend redemptions during stress
- Their "emergency fund" is locked in monthly contributions to illiquid products
- Cash needs don't align with fund liquidity profiles

Liquidity analysis ensures investors can actually access their money when needed.

---

#### 12. What-If Scenarios

**What:** Interactive sliders to adjust expected return (±2%), TER (±0.5%), risk aversion, time horizon, and contribution amount. Instantly recompute optimal portfolio mix, projected wealth, and goal probability. Display sensitivity analysis as tornado charts showing which inputs matter most to outcomes.

**Value:** Investors learn by playing with assumptions. What-if tools:
- Build intuition about which variables drive outcomes most
- Show that small return assumptions have outsized impact over long horizons
- Demonstrate that cost sensitivity increases with time
- Allow stress-testing plans against pessimistic scenarios
- Reduce overconfidence in single-point projections
- Create engagement and deeper understanding of the tool

Interactive exploration is more educational than any static report.

---

#### 13. Tax Efficiency

**What:** Model Spanish capital gains tax rules (19%-28% progressive brackets). Estimate after-tax returns for different holding periods. Suggest tax-loss harvesting opportunities — identify losing positions where selling realizes a tax deduction. Optimize withdrawal order in decumulation phase to minimize tax burden. Show net-of-tax wealth vs gross wealth.

**Value:** In Spain, capital gains tax can reduce returns by 2-6 percentage points annually. Tax efficiency:
- Preserves wealth that would otherwise go to taxes
- Makes fund transfers between MyInvestor products tax-advantageous (traspasos)
- Identifies optimal timing for realizing gains (income year vs low-income year)
- Shows the value of tax-deferred compounding
- Provides concrete "save €X by doing Y" recommendations

After-tax returns are what investors actually keep — optimizing them is high-value.

---

#### 14. Watchlist

**What:** Allow users to save favorite ISINs for ongoing tracking. Set price/performance alerts (e.g., "alert me when Fund X drops 5% this month"). Quick-add watched funds to active portfolio comparison. Track watchlist performance over time. Export watchlist for sharing or review.

**Value:** Investors research more funds than they invest in. A watchlist:
- Captures research effort instead of losing it between sessions
- Enables monitoring without committing capital
- Creates a pipeline of replacement candidates for underperforming holdings
- Allows tracking of funds that are temporarily unavailable or too expensive
- Builds user engagement through ongoing interaction with the app
- Provides context when a watched fund later becomes attractive

The watchlist turns one-time research into ongoing relationship with the platform.

---

#### 15. Export / Reporting

**What:** Generate PDF portfolio summary with allocations, expected returns, risk metrics, and simulation charts. Download allocation details as CSV. Create shareable read-only portfolio link for discussing with advisors, partners, or family. Schedule periodic email reports (monthly/quarterly portfolio review).

**Value:** Investors need to communicate their plans and track decisions over time. Export features:
- Enable advisor review without exposing account credentials
- Create documentation for financial planning meetings
- Allow partners/spouses to review investment strategy
- Provide audit trail of allocation decisions and rationale
- Make the app useful as a planning document, not just a screen tool
- Support regulatory compliance (documenting investment rationale)

Reports turn analysis into actionable, shareable documents.

---

### Technical Debt / Infrastructure

#### Test Suite
- **What:** Unit tests for `recommendador.py` (scoring, feasibility, weight allocation), `productos.py` (data parsing, filtering), `simulacion.py` (path generation). Mock `get_productos()` to avoid API calls in tests.
- **Value:** Catch regressions when modifying optimizer logic. Document expected behavior through test cases. Enable confident refactoring. Required before any production-grade deployment.

#### Type Hints
- **What:** Add complete type annotations to all functions in all modules. Use `mypy` or `pyright` for static type checking.
- **Value:** Catch type errors before runtime. Improve IDE autocomplete and documentation. Make code self-documenting. Reduce onboarding time for new contributors.

#### CI Pipeline
- **What:** GitHub Actions workflow: lint (ruff/flake8), typecheck (mypy), run tests on every push and PR. Block merges that fail checks.
- **Value:** Enforce code quality automatically. Catch errors before they reach main. Standardize development workflow. Enable confident collaboration.

#### Docker Deployment
- **What:** Dockerfile and docker-compose for one-command deployment. Health checks, resource limits, production-ready config.
- **Value:** Eliminate "works on my machine" problems. Enable deployment to any cloud provider. Standardize environment across dev/staging/production. Simplify onboarding.

#### Database Caching Layer
- **What:** Replace in-memory caching with SQLite for persistent cache across restarts. Cache API responses with TTL management. Support cache warmup on startup.
- **Value:** App survives restarts without refetching all data. Reduce API load and rate limit risk. Faster startup time. Enable offline mode with cached data.
