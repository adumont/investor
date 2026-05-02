from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


REQUIRED_RETURN_FIELDS = {
    1: "yearUno",
    3: "yearTres",
    5: "yearCinco",
}

VOLATILITY_FIELDS = {
    1: "volatilidadYearUno",
    3: "volatilidadYearTres",
    5: "volatilidadYearCinco",
}

# Heuristic correlation levels for covariance proxy.
# Higher correlation when assets share metadata.
CORR_SAME_CATEGORY = 0.85
CORR_SAME_ZONE = 0.60
CORR_SAME_ASSET_TYPE = 0.40
CORR_DEFAULT = 0.20


@dataclass
class Candidate:
    isin: str
    nombre: str
    expected_return: float
    ter: float
    volatility: float
    risk_score: float
    history_returns: list[float]
    categoria: str | None
    zona: str | None
    tipo_activo: str | None


class RecommendationError(ValueError):
    pass


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "").replace(",", ".")
        if cleaned in {"", ".", "N/A", "nan", "None"}:
            return default
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _non_empty_str(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or cleaned in {".", "N/A", "nan", "None"}:
        return None
    return cleaned


def _pct_points_to_decimal(value: float | None) -> float | None:
    if value is None:
        return None
    return value / 100.0


def _nearest_lower_horizon(horizon_years: int) -> int:
    if horizon_years >= 5:
        return 5
    if horizon_years >= 3:
        return 3
    return 1


def _extract_history_returns(producto: dict[str, Any]) -> list[float]:
    # Oldest to newest: year-5 .. year-1
    fields = [
        "rentabilidadPasadaCinco",
        "rentabilidadPasadaCuatro",
        "rentabilidadPasadaTres",
        "rentabilidadPasadaDos",
        "rentabilidadPasadaUno",
    ]
    history: list[float] = []
    for field in fields:
        parsed = _to_float(producto.get(field))
        if parsed is None:
            continue
        history.append(parsed / 100.0)
    return history


def _get_required_return(producto: dict[str, Any], horizon_bucket: int) -> float | None:
    field = REQUIRED_RETURN_FIELDS[horizon_bucket]
    raw = _to_float(producto.get(field))
    return _pct_points_to_decimal(raw)


def _get_volatility(producto: dict[str, Any], horizon_bucket: int) -> float | None:
    preferred = _to_float(producto.get(VOLATILITY_FIELDS[horizon_bucket]))
    if preferred is not None:
        return preferred / 100.0

    general = _to_float(producto.get("volatilidad"))
    if general is not None:
        return general / 100.0

    risk = _to_float(producto.get("indicadorRiesgo"))
    if risk is None:
        return None

    # Map risk indicator [1..7] to rough annualized volatility proxy.
    return max(0.03, min(0.35, (risk / 7.0) * 0.30))


def _build_correlation_matrix(candidates: list[Candidate]) -> list[list[float]]:
    n = len(candidates)
    corr = [[CORR_DEFAULT] * n for _ in range(n)]
    for i in range(n):
        corr[i][i] = 1.0
        for j in range(i + 1, n):
            ci, cj = candidates[i], candidates[j]
            c = CORR_DEFAULT
            if ci.categoria and ci.categoria == cj.categoria:
                c = CORR_SAME_CATEGORY
            elif ci.zona and ci.zona == cj.zona:
                c = CORR_SAME_ZONE
            elif ci.tipo_activo and ci.tipo_activo == cj.tipo_activo:
                c = CORR_SAME_ASSET_TYPE
            corr[i][j] = corr[j][i] = c
    return corr


def _portfolio_volatility(candidates: list[Candidate], weights: list[float]) -> float:
    corr = _build_correlation_matrix(candidates)
    n = len(candidates)
    var = 0.0
    for i in range(n):
        for j in range(n):
            var += weights[i] * weights[j] * corr[i][j] * candidates[i].volatility * candidates[j].volatility
    return sqrt(max(var, 0.0))


def _build_candidate(producto: dict[str, Any], horizon_bucket: int) -> tuple[Candidate | None, str | None]:
    isin = str(producto.get("codigoIsin") or "").strip()
    nombre = str(producto.get("nombre") or isin)

    expected_return = _get_required_return(producto, horizon_bucket)
    if expected_return is None:
        return None, f"Falta rentabilidad para horizonte {horizon_bucket}Y"

    ter = _pct_points_to_decimal(_to_float(producto.get("ter"), 0.0))
    if ter is None:
        ter = 0.0

    volatility = _get_volatility(producto, horizon_bucket)
    if volatility is None:
        return None, "Falta volatilidad o indicador de riesgo"

    risk_score = _to_float(producto.get("indicadorRiesgo"), 0.0) or 0.0
    history_returns = _extract_history_returns(producto)
    categoria = _non_empty_str(producto.get("categoriaMstar")) or _non_empty_str(producto.get("categoria"))
    zona = _non_empty_str(producto.get("zonaGeografica"))
    tipo_activo = _non_empty_str(producto.get("tipoActivo"))

    return (
        Candidate(
            isin=isin,
            nombre=nombre,
            expected_return=expected_return,
            ter=ter,
            volatility=volatility,
            risk_score=risk_score,
            history_returns=history_returns,
            categoria=categoria,
            zona=zona,
            tipo_activo=tipo_activo,
        ),
        None,
    )


def recommend_mix(
    productos: list[dict[str, Any]],
    selected_isins: list[str],
    horizon_years: int,
    min_weight: float = 0.05,
    risk_aversion: float = 0.35,
) -> dict[str, Any]:
    if not selected_isins:
        raise RecommendationError("Selecciona al menos un ISIN.")

    horizon_bucket = _nearest_lower_horizon(max(1, int(horizon_years)))
    selected_lookup = {isin: True for isin in selected_isins}
    by_isin = {
        str(p.get("codigoIsin") or "").strip(): p
        for p in productos
        if str(p.get("codigoIsin") or "").strip() in selected_lookup
    }

    missing_isins = [isin for isin in selected_isins if isin not in by_isin]
    exclusions: list[dict[str, str]] = [
        {"isin": isin, "reason": "ISIN no encontrado en dataset"}
        for isin in missing_isins
    ]

    candidates: list[Candidate] = []
    for isin in selected_isins:
        producto = by_isin.get(isin)
        if not producto:
            continue
        candidate, reason = _build_candidate(producto, horizon_bucket)
        if candidate is None:
            exclusions.append({"isin": isin, "reason": reason or "Datos incompletos"})
            continue
        candidates.append(candidate)

    if not candidates:
        raise RecommendationError("Ningun producto apto tras aplicar reglas de datos.")

    n_assets = len(candidates)
    if (n_assets * min_weight) > 1.0:
        raise RecommendationError(
            "Restriccion inviable: minimo por fondo supera 100%. Reduce seleccion o minimo."
        )

    raw_scores = [
        c.expected_return - c.ter - (risk_aversion * c.volatility) for c in candidates
    ]

    if max(raw_scores) <= 0:
        fallback = [max(0.0001, c.expected_return - c.ter) for c in candidates]
        score_base = fallback
    else:
        floor = min(raw_scores)
        shift = -floor + 0.0001 if floor <= 0 else 0.0
        score_base = [s + shift for s in raw_scores]

    score_sum = sum(score_base)
    if score_sum <= 0:
        score_base = [1.0 for _ in candidates]
        score_sum = float(n_assets)

    free_weight = 1.0 - (n_assets * min_weight)
    weights = [min_weight + free_weight * (s / score_sum) for s in score_base]

    allocations = []
    portfolio_expected_gross = 0.0
    portfolio_ter = 0.0
    portfolio_volatility = 0.0
    portfolio_objective = 0.0

    for candidate, weight, score in zip(candidates, weights, raw_scores):
        gross_contribution = weight * candidate.expected_return
        ter_contribution = weight * candidate.ter
        risk_contribution = weight * risk_aversion * candidate.volatility
        objective_contribution = gross_contribution - ter_contribution - risk_contribution

        portfolio_expected_gross += gross_contribution
        portfolio_ter += ter_contribution
        portfolio_objective += objective_contribution

        allocations.append(
            {
                "isin": candidate.isin,
                "nombre": candidate.nombre,
                "weight": weight,
                "expected_return": candidate.expected_return,
                "ter": candidate.ter,
                "volatility": candidate.volatility,
                "risk_score": candidate.risk_score,
                "raw_score": score,
                "gross_contribution": gross_contribution,
                "ter_contribution": ter_contribution,
                "risk_contribution": risk_contribution,
                "objective_contribution": objective_contribution,
                "history_returns": candidate.history_returns,
                "categoria": candidate.categoria,
                "zona": candidate.zona,
                "tipo_activo": candidate.tipo_activo,
            }
        )

    allocations.sort(key=lambda row: row["weight"], reverse=True)

    portfolio_volatility = _portfolio_volatility(candidates, weights)

    portfolio_net_expected = portfolio_expected_gross - portfolio_ter

    return {
        "horizon_years": int(horizon_years),
        "horizon_bucket": horizon_bucket,
        "risk_aversion": risk_aversion,
        "min_weight": min_weight,
        "allocations": allocations,
        "excluded": exclusions,
        "portfolio": {
            "expected_gross": portfolio_expected_gross,
            "ter_drag": portfolio_ter,
            "net_expected": portfolio_net_expected,
            "volatility_proxy": portfolio_volatility,
            "objective": portfolio_objective,
        },
    }
