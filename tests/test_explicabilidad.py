"""Test explicabilidad.py - recommendation explanation generation."""

from src.explicabilidad import build_recommendation_explanation, _pct


class TestPct:
    def test_basic(self):
        assert _pct(0.1234) == "12.34%"

    def test_zero(self):
        assert _pct(0.0) == "0.00%"

    def test_negative(self):
        assert _pct(-0.0567) == "-5.67%"

    def test_rounding(self):
        assert _pct(0.999) == "99.90%"


class TestBuildRecommendationExplanation:
    def test_basic_recommendation(self):
        recommendation = {
            "horizon_years": 5,
            "horizon_bucket": 5,
            "risk_aversion": 0.35,
            "portfolio": {
                "expected_gross": 0.085,
                "ter_drag": 0.005,
                "net_expected": 0.08,
                "volatility_proxy": 0.12,
            },
            "allocations": [
                {"isin": "ES123", "weight": 0.6, "nombre": "Fund A"},
                {"isin": "ES456", "weight": 0.4, "nombre": "Fund B"},
            ],
            "excluded": [],
        }
        result = build_recommendation_explanation(recommendation)
        assert "5 años" in result
        assert "5Y" in result
        assert "0.35" in result
        assert "8.50%" in result  # expected_gross
        assert "0.50%" in result  # ter_drag
        assert "8.00%" in result  # net_expected
        assert "12.00%" in result  # volatility_proxy
        assert "ES123" in result
        assert "60.00%" in result  # weight

    def test_with_excluded(self):
        recommendation = {
            "horizon_years": 3,
            "horizon_bucket": 3,
            "risk_aversion": 0.35,
            "portfolio": {
                "expected_gross": 0.06,
                "ter_drag": 0.002,
                "net_expected": 0.058,
                "volatility_proxy": 0.10,
            },
            "allocations": [],
            "excluded": [
                {"isin": "ES999", "reason": "Falta rentabilidad"},
            ],
        }
        result = build_recommendation_explanation(recommendation)
        assert "3 años" in result
        assert "ES999" in result
        assert "Falta rentabilidad" in result

    def test_empty_allocations(self):
        recommendation = {
            "horizon_years": 1,
            "horizon_bucket": 1,
            "risk_aversion": 0.35,
            "portfolio": {},
            "allocations": [],
            "excluded": [],
        }
        result = build_recommendation_explanation(recommendation)
        assert "1 año" in result
        assert "Nota:" in result

    def test_multiple_excluded(self):
        recommendation = {
            "horizon_years": 10,
            "horizon_bucket": 5,
            "risk_aversion": 0.25,
            "portfolio": {
                "expected_gross": 0.07,
                "ter_drag": 0.01,
                "net_expected": 0.06,
                "volatility_proxy": 0.15,
            },
            "allocations": [
                {"isin": "ES111", "weight": 1.0, "nombre": "Only Fund"},
            ],
            "excluded": [
                {"isin": "ES222", "reason": "Missing volatility"},
                {"isin": "ES333", "reason": "ISIN not found"},
            ],
        }
        result = build_recommendation_explanation(recommendation)
        assert "ES222" in result
        assert "ES333" in result
        assert "Missing volatility" in result
        assert "ISIN not found" in result

    def test_top_allocations(self):
        recommendation = {
            "horizon_years": 5,
            "horizon_bucket": 5,
            "risk_aversion": 0.35,
            "portfolio": {
                "expected_gross": 0.09,
                "ter_drag": 0.005,
                "net_expected": 0.085,
                "volatility_proxy": 0.12,
            },
            "allocations": [
                {"isin": "ES111", "weight": 0.5, "nombre": "Fund A"},
                {"isin": "ES222", "weight": 0.3, "nombre": "Fund B"},
                {"isin": "ES333", "weight": 0.2, "nombre": "Fund C"},
            ],
            "excluded": [],
        }
        result = build_recommendation_explanation(recommendation)
        # Should show top 3 (or all if <= 3)
        assert "ES111" in result
        assert "ES222" in result
        assert "ES333" in result
