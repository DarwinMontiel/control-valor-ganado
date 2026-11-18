"""Alertas deterministas a partir de los indicadores EVM.

Son reglas fijas sobre cifras ya calculadas, no predicciones: cada alerta dice qué indicador
la disparó y con qué valor, para que el líder pueda comprobarla.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.evm import EvmIndicators
from app.domain.status import CostStatus

# Umbral a partir del cual una desviación pasa de "media" a "alta". Muchas oficinas de proyectos
# usan 0,90 como límite de tolerancia; es un supuesto de negocio, no parte de la fórmula EVM.
CRITICAL_INDEX_THRESHOLD = Decimal("0.90")
TARGET_INDEX = Decimal(1)
_ZERO = Decimal(0)


class AlertSeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class AlertType(StrEnum):
    COST_OVERRUN = "COST_OVERRUN"
    SCHEDULE_DELAY = "SCHEDULE_DELAY"
    COST_WITHOUT_PROGRESS = "COST_WITHOUT_PROGRESS"
    MISSING_ACTUAL_COST = "MISSING_ACTUAL_COST"
    PROJECTED_OVERRUN = "PROJECTED_OVERRUN"


@dataclass(frozen=True, slots=True)
class Alert:
    type: AlertType
    severity: AlertSeverity
    indicator: str
    observed_value: Decimal
    message: str


def evaluate_alerts(indicators: EvmIndicators) -> list[Alert]:
    """Alertas de un conjunto de indicadores (de una actividad o del proyecto)."""
    candidates = (
        _cost_overrun(indicators),
        _schedule_delay(indicators),
        _cost_without_progress(indicators),
        _missing_actual_cost(indicators),
        _projected_overrun(indicators),
    )
    return [alert for alert in candidates if alert is not None]


def _decimal_text(value: Decimal) -> str:
    """Dos decimales con coma, como se leen las cifras en español."""
    return f"{value:.2f}".replace(".", ",")


def _severity(index: Decimal) -> AlertSeverity:
    return AlertSeverity.HIGH if index < CRITICAL_INDEX_THRESHOLD else AlertSeverity.MEDIUM


def _cost_overrun(indicators: EvmIndicators) -> Alert | None:
    cpi = indicators.cost_performance_index
    if cpi is None or cpi == _ZERO or cpi >= TARGET_INDEX:
        return None
    return Alert(
        type=AlertType.COST_OVERRUN,
        severity=_severity(cpi),
        indicator="CPI",
        observed_value=cpi,
        message=f"Por cada peso gastado se obtienen {_decimal_text(cpi)} pesos de trabajo.",
    )


def _schedule_delay(indicators: EvmIndicators) -> Alert | None:
    spi = indicators.schedule_performance_index
    if spi is None or spi >= TARGET_INDEX:
        return None
    return Alert(
        type=AlertType.SCHEDULE_DELAY,
        severity=_severity(spi),
        indicator="SPI",
        observed_value=spi,
        message=f"Se ha completado el {spi * 100:.0f} % del trabajo que debía estar hecho.",
    )


def _cost_without_progress(indicators: EvmIndicators) -> Alert | None:
    if indicators.actual_cost == _ZERO or indicators.earned_value != _ZERO:
        return None
    return Alert(
        type=AlertType.COST_WITHOUT_PROGRESS,
        severity=AlertSeverity.HIGH,
        indicator="AC",
        observed_value=indicators.actual_cost,
        message="Hay costo registrado sin ningún avance. No se puede estimar el costo final.",
    )


def _missing_actual_cost(indicators: EvmIndicators) -> Alert | None:
    if indicators.cost_status is not CostStatus.NOT_CALCULABLE:
        return None
    return Alert(
        type=AlertType.MISSING_ACTUAL_COST,
        severity=AlertSeverity.MEDIUM,
        indicator="EV",
        observed_value=indicators.earned_value,
        message="Hay avance sin costo real registrado. Revise si falta cargarlo.",
    )


def _projected_overrun(indicators: EvmIndicators) -> Alert | None:
    vac = indicators.variance_at_completion
    if vac is None or vac >= _ZERO:
        return None
    return Alert(
        type=AlertType.PROJECTED_OVERRUN,
        severity=AlertSeverity.MEDIUM,
        indicator="VAC",
        observed_value=vac,
        message="Si se mantiene la eficiencia actual, el costo final superaría el presupuesto. "
        "Es una proyección, no un resultado.",
    )
