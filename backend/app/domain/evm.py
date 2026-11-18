"""Motor de Valor Ganado (EVM).

Python puro: no depende de FastAPI, SQLAlchemy ni la base de datos. Todas las cifras usan
``Decimal`` y se redondean una sola vez, al construir el resultado.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.domain.errors import InvalidActivityError
from app.domain.status import (
    CostStatus,
    PerformanceBand,
    ScheduleStatus,
    classify_band,
    classify_cost,
    classify_schedule,
)

PERCENT_BASE = Decimal(100)
MIN_PERCENT = Decimal(0)
MAX_PERCENT = Decimal(100)
MONEY_QUANTUM = Decimal("0.01")
INDEX_QUANTUM = Decimal("0.0001")
# Con menos del 10 % del trabajo hecho, el CPI todavía dice poco: una sola actividad que gastó
# sin avanzar dispara el EAC. Por debajo de ese avance, el EAC se marca como poco confiable.
MIN_PROGRESS_FOR_RELIABLE_ESTIMATE = Decimal("0.10")
_ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class ActivityProgress:
    """Datos que registra el líder de proyecto para una actividad a la fecha de corte."""

    budget_at_completion: Decimal
    planned_progress: Decimal
    actual_progress: Decimal
    actual_cost: Decimal

    def __post_init__(self) -> None:
        if self.budget_at_completion <= _ZERO:
            raise InvalidActivityError("El presupuesto (BAC) debe ser mayor que cero.")
        if self.actual_cost < _ZERO:
            raise InvalidActivityError("El costo real (AC) no puede ser negativo.")
        _require_percent(self.planned_progress, "planificado")
        _require_percent(self.actual_progress, "real")

    @property
    def planned_value(self) -> Decimal:
        return self.planned_progress / PERCENT_BASE * self.budget_at_completion

    @property
    def earned_value(self) -> Decimal:
        return self.actual_progress / PERCENT_BASE * self.budget_at_completion


@dataclass(frozen=True, slots=True)
class EvmIndicators:
    """Indicadores EVM. Un índice en ``None`` significa que no se puede calcular."""

    budget_at_completion: Decimal
    planned_value: Decimal
    earned_value: Decimal
    actual_cost: Decimal
    cost_variance: Decimal
    schedule_variance: Decimal
    cost_performance_index: Decimal | None
    schedule_performance_index: Decimal | None
    estimate_at_completion: Decimal | None
    variance_at_completion: Decimal | None
    estimate_is_reliable: bool | None
    cost_status: CostStatus
    schedule_status: ScheduleStatus
    cost_band: PerformanceBand
    schedule_band: PerformanceBand


def calculate_activity_indicators(activity: ActivityProgress) -> EvmIndicators:
    """Indicadores de una actividad."""
    return _build_indicators(
        budget_at_completion=activity.budget_at_completion,
        planned_value=activity.planned_value,
        earned_value=activity.earned_value,
        actual_cost=activity.actual_cost,
    )


def consolidate(activities: Iterable[ActivityProgress]) -> EvmIndicators:
    """Indicadores consolidados de un proyecto.

    Se suman BAC, PV, EV y AC y se recalculan los índices sobre las sumas. Promediar los CPI
    o SPI de las actividades daría el mismo peso a una actividad pequeña que a una grande.
    """
    items = list(activities)
    return _build_indicators(
        budget_at_completion=sum((item.budget_at_completion for item in items), _ZERO),
        planned_value=sum((item.planned_value for item in items), _ZERO),
        earned_value=sum((item.earned_value for item in items), _ZERO),
        actual_cost=sum((item.actual_cost for item in items), _ZERO),
    )


def _build_indicators(
    *,
    budget_at_completion: Decimal,
    planned_value: Decimal,
    earned_value: Decimal,
    actual_cost: Decimal,
) -> EvmIndicators:
    # Todo se deriva de las cifras base ya redondeadas a centavos, que son las que ve el
    # usuario. Así un estado "Atrasado" nunca aparece junto a una variación de 0,00.
    budget_at_completion = _round_money(budget_at_completion)
    planned_value = _round_money(planned_value)
    earned_value = _round_money(earned_value)
    actual_cost = _round_money(actual_cost)
    estimate_at_completion = _estimate_at_completion(
        budget_at_completion, earned_value, actual_cost
    )
    variance_at_completion = (
        None
        if estimate_at_completion is None
        else _round_money(budget_at_completion - estimate_at_completion)
    )
    cost_performance_index = _round_index(_safe_ratio(earned_value, actual_cost))
    schedule_performance_index = _round_index(_safe_ratio(earned_value, planned_value))
    return EvmIndicators(
        budget_at_completion=budget_at_completion,
        planned_value=planned_value,
        earned_value=earned_value,
        actual_cost=actual_cost,
        cost_variance=earned_value - actual_cost,
        schedule_variance=earned_value - planned_value,
        cost_performance_index=cost_performance_index,
        schedule_performance_index=schedule_performance_index,
        estimate_at_completion=(
            None if estimate_at_completion is None else _round_money(estimate_at_completion)
        ),
        variance_at_completion=variance_at_completion,
        estimate_is_reliable=(
            None
            if estimate_at_completion is None
            else earned_value / budget_at_completion >= MIN_PROGRESS_FOR_RELIABLE_ESTIMATE
        ),
        cost_status=classify_cost(earned_value, actual_cost),
        schedule_status=classify_schedule(earned_value, planned_value),
        cost_band=classify_band(cost_performance_index),
        schedule_band=classify_band(schedule_performance_index),
    )


def _estimate_at_completion(
    budget_at_completion: Decimal, earned_value: Decimal, actual_cost: Decimal
) -> Decimal | None:
    """EAC = BAC / CPI, calculado como BAC × AC / EV para no arrastrar el redondeo del CPI.

    No existe si AC = 0 (CPI indefinido) ni si EV = 0 (CPI = 0, división por cero).
    """
    if actual_cost == _ZERO or earned_value == _ZERO:
        return None
    return budget_at_completion * actual_cost / earned_value


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    return None if denominator == _ZERO else numerator / denominator


def _round_money(value: Decimal) -> Decimal:
    rounded = value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    return abs(rounded) if rounded == _ZERO else rounded


def _round_index(value: Decimal | None) -> Decimal | None:
    return None if value is None else value.quantize(INDEX_QUANTUM, rounding=ROUND_HALF_UP)


def _require_percent(value: Decimal, label: str) -> None:
    if not MIN_PERCENT <= value <= MAX_PERCENT:
        raise InvalidActivityError(f"El avance {label} debe estar entre 0 y 100.")
