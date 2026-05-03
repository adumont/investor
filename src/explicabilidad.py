from __future__ import annotations

from typing import Any


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_recommendation_explanation(recommendation: dict[str, Any]) -> str:
    horizon = recommendation.get("horizon_years")
    bucket = recommendation.get("horizon_bucket")
    risk_aversion = recommendation.get("risk_aversion")
    portfolio = recommendation.get("portfolio", {})
    allocations = recommendation.get("allocations") or []
    excluded = recommendation.get("excluded") or []

    lines = [
        f"Horizonte solicitado: {horizon} anos. Regla aplicada: horizonte inferior mas cercano ({bucket}Y).",
        f"Objetivo: maximizar rentabilidad neta ajustada por riesgo = retorno esperado - TER - {risk_aversion:.2f} x volatilidad.",
        f"Rentabilidad esperada bruta cartera: {_pct(float(portfolio.get('expected_gross', 0.0)))}.",
        f"Impacto TER agregado: -{_pct(float(portfolio.get('ter_drag', 0.0)))}.",
        f"Rentabilidad esperada neta cartera: {_pct(float(portfolio.get('net_expected', 0.0)))}.",
        f"Volatilidad proxy cartera: {_pct(float(portfolio.get('volatility_proxy', 0.0)))}.",
    ]

    if allocations:
        top = allocations[: min(3, len(allocations))]
        top_text = ", ".join(f"{a['isin']} ({_pct(a['weight'])})" for a in top)
        lines.append(f"Mayor peso asignado a: {top_text}.")

    if excluded:
        exclusion_text = "; ".join(
            f"{row['isin']}: {row['reason']}" for row in excluded
        )
        lines.append(f"Productos excluidos por datos incompletos: {exclusion_text}.")

    lines.append(
        "Nota: simulacion usa estadisticas historicas agregadas disponibles (proxy), no backtest con serie temporal completa."
    )

    return "\n".join(f"- {line}" for line in lines)
