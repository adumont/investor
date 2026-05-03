import pytest
from src.recommendador import (
    Candidate,
    RecommendationError,
    _build_candidate,
    _build_correlation_matrix,
    _nearest_lower_horizon,
    _non_empty_str,
    _get_required_return,
    _get_volatility,
    _portfolio_volatility,
    _to_float,
    recommend_mix,
)


class TestToFloat:
    def test_none_returns_default(self):
        assert _to_float(None, 0.0) == 0.0
        assert _to_float(None) is None

    def test_valid_float(self):
        assert _to_float(3.14) == 3.14

    def test_string_percent(self):
        assert _to_float("3.14%") == 3.14

    def test_string_comma_decimal(self):
        assert _to_float("3,14") == 3.14

    def test_na_values(self):
        assert _to_float("N/A") is None
        assert _to_float("nan") is None
        assert _to_float("None") is None
        assert _to_float("") is None
        assert _to_float(".") is None

    def test_valid_string(self):
        assert _to_float("3.14") == 3.14


class TestNearestLowerHorizon:
    def test_less_than_1(self):
        assert _nearest_lower_horizon(0) == 1
        assert _nearest_lower_horizon(-1) == 1

    def test_1_to_2(self):
        assert _nearest_lower_horizon(1) == 1
        assert _nearest_lower_horizon(2) == 1

    def test_3_to_4(self):
        assert _nearest_lower_horizon(3) == 3
        assert _nearest_lower_horizon(4) == 3

    def test_5_and_above(self):
        assert _nearest_lower_horizon(5) == 5
        assert _nearest_lower_horizon(10) == 5


class TestBuildCandidate:
    def test_valid_product(self, sample_product):
        candidate, reason = _build_candidate(sample_product, 1)
        assert candidate is not None
        assert reason is None
        assert candidate.isin == "ES0123456789"
        assert candidate.expected_return == 0.105
        assert candidate.ter == 0.005
        assert candidate.volatility == 0.12
        assert candidate.risk_score == 4.0

    def test_missing_return(self):
        product = {"codigoIsin": "ESX", "nombre": "X", "ter": 0.5}
        candidate, reason = _build_candidate(product, 1)
        assert candidate is None
        assert "rentabilidad" in reason

    def test_missing_volatility_falls_back_to_risk(self):
        product = {
            "codigoIsin": "ESX",
            "nombre": "X",
            "yearUno": 5.0,
            "ter": 0.5,
            "indicadorRiesgo": 3,
        }
        candidate, reason = _build_candidate(product, 1)
        assert candidate is not None
        assert candidate.volatility is not None
        assert candidate.volatility > 0

    def test_missing_volatility_and_risk(self):
        product = {"codigoIsin": "ESX", "nombre": "X", "yearUno": 5.0, "ter": 0.5}
        candidate, reason = _build_candidate(product, 1)
        assert candidate is None
        assert "volatilidad" in reason


class TestCorrelationMatrix:
    def test_diagonal_is_one(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.1, 3, [], "Cat", "Zone", "Type")
        corr = _build_correlation_matrix([c1])
        assert corr[0][0] == 1.0

    def test_same_category(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.1, 3, [], "Cat", "Zone", "Type")
        c2 = Candidate("ES2", "B", 0.1, 0.01, 0.1, 3, [], "Cat", "Zone2", "Type2")
        corr = _build_correlation_matrix([c1, c2])
        assert corr[0][1] == 0.85
        assert corr[1][0] == 0.85

    def test_same_zone_different_category(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.1, 3, [], "Cat1", "Zone", "Type")
        c2 = Candidate("ES2", "B", 0.1, 0.01, 0.1, 3, [], "Cat2", "Zone", "Type")
        corr = _build_correlation_matrix([c1, c2])
        assert corr[0][1] == 0.60

    def test_same_asset_type_only(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.1, 3, [], "Cat1", "Zone1", "Type")
        c2 = Candidate("ES2", "B", 0.1, 0.01, 0.1, 3, [], "Cat2", "Zone2", "Type")
        corr = _build_correlation_matrix([c1, c2])
        assert corr[0][1] == 0.40

    def test_default_correlation(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.1, 3, [], "Cat1", "Zone1", "Type1")
        c2 = Candidate("ES2", "B", 0.1, 0.01, 0.1, 3, [], "Cat2", "Zone2", "Type2")
        corr = _build_correlation_matrix([c1, c2])
        assert corr[0][1] == 0.20


class TestPortfolioVolatility:
    def test_single_asset(self):
        c = Candidate("ES1", "A", 0.1, 0.01, 0.12, 3, [], None, None, None)
        vol = _portfolio_volatility([c], [1.0])
        assert abs(vol - 0.12) < 1e-9

    def test_two_uncorrelated_assets(self):
        c1 = Candidate("ES1", "A", 0.1, 0.01, 0.10, 3, [], "C1", "Z1", "T1")
        c2 = Candidate("ES2", "B", 0.1, 0.01, 0.20, 3, [], "C2", "Z2", "T2")
        vol = _portfolio_volatility([c1, c2], [0.5, 0.5])
        assert vol < 0.15


class TestRecommendMix:
    def test_empty_isins(self):
        with pytest.raises(RecommendationError, match="al menos un ISIN"):
            recommend_mix([], [], horizon_years=1)

    def test_missing_isin(self, sample_products):
        with pytest.raises(RecommendationError, match="Ningun producto apto"):
            recommend_mix(sample_products, ["ES_DOES_NOT_EXIST"], horizon_years=1)

    def test_feasibility_violation(self, sample_products):
        p2 = dict(sample_products[0])
        p2["codigoIsin"] = "ES0987654321"
        products = sample_products + [p2]
        with pytest.raises(RecommendationError, match="inviable"):
            recommend_mix(
                products,
                ["ES0123456789", "ES0987654321"],
                horizon_years=1,
                min_weight=0.6,
            )

    def test_valid_recommendation(self, sample_products):
        result = recommend_mix(sample_products, ["ES0123456789"], horizon_years=1)
        assert result["allocations"][0]["weight"] == 1.0
        assert result["portfolio"]["expected_gross"] > 0

    def test_score_stabilization_all_negative(self, sample_products):
        p = sample_products[0]
        p["yearUno"] = -5.0
        p["ter"] = 0.0
        p["volatilidadYearUno"] = 1.0
        result = recommend_mix(sample_products, ["ES0123456789"], horizon_years=1)
        assert result["allocations"][0]["weight"] > 0

    def test_weights_sum_to_one(self, sample_products):
        result = recommend_mix(sample_products, ["ES0123456789"], horizon_years=1)
        total = sum(a["weight"] for a in result["allocations"])
        assert abs(total - 1.0) < 1e-9

    def test_excluded_isins(self, sample_products):
        result = recommend_mix(
            sample_products, ["ES0123456789", "ES_DOES_NOT_EXIST"], horizon_years=1
        )
        assert len(result["excluded"]) == 1
        assert result["excluded"][0]["isin"] == "ES_DOES_NOT_EXIST"


class TestEdgeCases:
    def test_to_float_type_error(self):
        # Passing a list should raise TypeError, caught by except clause
        result = _to_float(["not", "a", "number"], default=99.9)
        assert result == 99.9

    def test_to_float_value_error(self):
        # Invalid string that can't be parsed
        result = _to_float("totally_invalid_!!!", default=42.0)
        assert result == 42.0

    def test_non_empty_str_invalid_input(self):
        assert _non_empty_str(123) is None
        assert _non_empty_str(None) is None
        assert _non_empty_str("") is None
        assert _non_empty_str(".") is None

    def test_get_required_return_missing(self):
        product = {"codigoIsin": "X", "nombre": "X"}
        result = _get_required_return(product, 1)
        assert result is None

    def test_get_volatility_all_none(self):
        product = {"codigoIsin": "X", "nombre": "X", "indicadorRiesgo": None}
        result = _get_volatility(product, 1)
        assert result is None

    def test_build_candidate_missing_both(self):
        product = {"codigoIsin": "X", "nombre": "X"}
        candidate, reason = _build_candidate(product, 1)
        assert candidate is None
        assert reason is not None

    def test_recommend_mix_zero_scores(self):
        # All expected returns zero, should trigger score_sum <= 0 fallback
        products = [
            {
                "codigoIsin": "ES1",
                "nombre": "A",
                "yearUno": 0.0,
                "ter": 0.0,
                "indicadorRiesgo": 1,
            },
            {
                "codigoIsin": "ES2",
                "nombre": "B",
                "yearUno": 0.0,
                "ter": 0.0,
                "indicadorRiesgo": 1,
            },
        ]
        result = recommend_mix(
            products, ["ES1", "ES2"], horizon_years=1, min_weight=0.1
        )
        # Should still produce valid allocation
        assert len(result["allocations"]) == 2
        total = sum(a["weight"] for a in result["allocations"])
        assert abs(total - 1.0) < 1e-9
