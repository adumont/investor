from __future__ import annotations

from typing import Any


def _compound_path(annual_rate: float, years: int, start_capital: float = 1.0) -> list[dict[str, float]]:
    value = float(start_capital)
    path = []
    for year in range(1, years + 1):
        value *= 1.0 + annual_rate
        path.append(
            {
                "year": year,
                "annual_return": annual_rate,
                "portfolio_value": value,
                "cumulative_return": value - 1.0,
            }
        )
    return path


def _weighted_extreme(allocations: list[dict[str, Any]], mode: str) -> float:
    total = 0.0
    for row in allocations:
        history = row.get("history_returns") or []
        base = row.get("expected_return", 0.0)
        ter = row.get("ter", 0.0)
        if history:
            sampled = max(history) if mode == "max" else min(history)
        else:
            sampled = base
        total += row["weight"] * (sampled - ter)
    return total


def _historical_proxy_path(
    allocations: list[dict[str, Any]], years: int
) -> list[dict[str, float]]:
    # Build weighted annual returns from oldest to newest using available history.
    max_len = max((len(row.get("history_returns") or []) for row in allocations), default=0)
    if max_len <= 0:
        return []

    value = 1.0
    rows: list[dict[str, float]] = []
    effective_years = max(1, min(int(years), max_len))
    start_index = max_len - effective_years

    for index in range(start_index, max_len):
        weighted_return = 0.0
        covered_weight = 0.0
        for row in allocations:
            history = row.get("history_returns") or []
            if index >= len(history):
                continue
            weighted_return += row["weight"] * (history[index] - row.get("ter", 0.0))
            covered_weight += row["weight"]

        if covered_weight <= 0:
            continue

        normalized_return = weighted_return / covered_weight
        value *= 1.0 + normalized_return
        rows.append(
            {
                "year_index": (index - start_index) + 1,
                "coverage_weight": covered_weight,
                "annual_return": normalized_return,
                "portfolio_value": value,
                "cumulative_return": value - 1.0,
            }
        )

    return rows


def build_simulation(recommendation: dict[str, Any], years: int) -> dict[str, Any]:
    allocations = recommendation.get("allocations") or []
    if not allocations:
        return {
            "scenarios": [],
            "paths": [],
            "historical_proxy": [],
        }

    portfolio = recommendation.get("portfolio", {})
    base_rate = float(portfolio.get("net_expected", 0.0))
    optimistic_rate = _weighted_extreme(allocations, "max")
    conservative_rate = _weighted_extreme(allocations, "min")

    scenarios = [
        {"name": "Conservador", "annual_rate": conservative_rate},
        {"name": "Base", "annual_rate": base_rate},
        {"name": "Optimista", "annual_rate": optimistic_rate},
    ]

    scenario_paths = []
    for scenario in scenarios:
        path = _compound_path(scenario["annual_rate"], years)
        for row in path:
            scenario_paths.append(
                {
                    "scenario": scenario["name"],
                    "year": row["year"],
                    "annual_return": row["annual_return"],
                    "portfolio_value": row["portfolio_value"],
                    "cumulative_return": row["cumulative_return"],
                }
            )

    historical_proxy = _historical_proxy_path(allocations, years)

    return {
        "scenarios": scenarios,
        "paths": scenario_paths,
        "historical_proxy": historical_proxy,
    }
