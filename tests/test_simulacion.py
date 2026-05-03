"""Test simulacion.py logic."""

from src.simulacion import (
    _compound_path,
    _weighted_extreme,
    _historical_proxy_path,
    build_simulation,
)


class TestCompoundPath:
    def test_basic_growth(self):
        path = _compound_path(0.10, 3, start_capital=100.0)
        assert len(path) == 3
        assert path[0]["year"] == 1
        assert path[0]["annual_return"] == 0.10
        assert abs(path[0]["portfolio_value"] - 110.0) < 0.01
        assert abs(path[2]["portfolio_value"] - 133.1) < 0.01

    def test_zero_growth(self):
        path = _compound_path(0.0, 2)
        assert len(path) == 2
        assert all(p["portfolio_value"] == 1.0 for p in path)

    def test_negative_growth(self):
        path = _compound_path(-0.05, 2, start_capital=100.0)
        assert len(path) == 2
        assert path[1]["portfolio_value"] < 100.0


class TestWeightedExtreme:
    def test_max_mode(self):
        allocations = [
            {
                "history_returns": [0.10, 0.15, 0.20],
                "expected_return": 0.12,
                "ter": 0.01,
                "weight": 0.5,
            },
            {
                "history_returns": [0.05, 0.08, 0.12],
                "expected_return": 0.06,
                "ter": 0.01,
                "weight": 0.5,
            },
        ]
        result = _weighted_extreme(allocations, "max")
        assert result == 0.5 * (0.20 - 0.01) + 0.5 * (0.12 - 0.01)

    def test_min_mode(self):
        allocations = [
            {
                "history_returns": [0.10, 0.15, 0.20],
                "expected_return": 0.12,
                "ter": 0.01,
                "weight": 0.5,
            },
            {
                "history_returns": [0.05, 0.08, 0.12],
                "expected_return": 0.06,
                "ter": 0.01,
                "weight": 0.5,
            },
        ]
        result = _weighted_extreme(allocations, "min")
        assert result == 0.5 * (0.10 - 0.01) + 0.5 * (0.05 - 0.01)

    def test_no_history_falls_back_to_base(self):
        allocations = [
            {
                "history_returns": [],
                "expected_return": 0.12,
                "ter": 0.01,
                "weight": 1.0,
            },
        ]
        result = _weighted_extreme(allocations, "max")
        assert result == 0.12 - 0.01

    def test_invalid_mode_falls_back_to_base(self):
        allocations = [
            {
                "history_returns": [],
                "expected_return": 0.12,
                "ter": 0.01,
                "weight": 1.0,
            },
        ]
        result = _weighted_extreme(allocations, "invalid")
        assert result == 0.12 - 0.01


class TestHistoricalProxyPath:
    def test_basic(self):
        allocations = [
            {
                "history_returns": [0.10, 0.15, 0.20, 0.18, 0.12],
                "ter": 0.01,
                "weight": 1.0,
            },
        ]
        path = _historical_proxy_path(allocations, 3)
        assert len(path) == 3
        assert path[0]["year_index"] == 1
        assert "cumulative_return" in path[0]

    def test_multiple_assets(self):
        allocations = [
            {"history_returns": [0.10, 0.15, 0.20], "ter": 0.01, "weight": 0.5},
            {"history_returns": [0.05, 0.08, 0.12], "ter": 0.01, "weight": 0.5},
        ]
        path = _historical_proxy_path(allocations, 3)
        assert len(path) == 3

    def test_no_history(self):
        allocations = [
            {"history_returns": [], "ter": 0.01, "weight": 1.0},
        ]
        path = _historical_proxy_path(allocations, 3)
        assert len(path) == 0

    def test_years_exceeds_history(self):
        allocations = [
            {"history_returns": [0.10, 0.15], "ter": 0.01, "weight": 1.0},
        ]
        path = _historical_proxy_path(allocations, 5)
        assert len(path) == 2  # Only 2 years of history


class TestBuildSimulation:
    def test_empty_allocations(self):
        recommendation = {"allocations": []}
        result = build_simulation(recommendation, 5)
        assert result["scenarios"] == []
        assert result["paths"] == []
        assert result["historical_proxy"] == []

    def test_with_allocations(self):
        recommendation = {
            "allocations": [
                {
                    "history_returns": [0.10, 0.15, 0.20, 0.18, 0.12],
                    "expected_return": 0.12,
                    "ter": 0.01,
                    "weight": 1.0,
                },
            ],
            "portfolio": {"net_expected": 0.11},
        }
        result = build_simulation(recommendation, 3)
        assert len(result["scenarios"]) == 3
        assert len(result["paths"]) > 0
        assert len(result["historical_proxy"]) > 0

    def test_scenario_values(self):
        recommendation = {
            "allocations": [
                {
                    "history_returns": [0.10, 0.15, 0.20],
                    "expected_return": 0.12,
                    "ter": 0.01,
                    "weight": 1.0,
                },
            ],
            "portfolio": {"net_expected": 0.11},
        }
        result = build_simulation(recommendation, 2)
        scenarios = result["scenarios"]
        assert scenarios[0]["name"] == "Conservador"
        assert scenarios[1]["name"] == "Base"
        assert scenarios[2]["name"] == "Optimista"
        assert (
            scenarios[0]["annual_rate"]
            <= scenarios[1]["annual_rate"]
            <= scenarios[2]["annual_rate"]
        )
