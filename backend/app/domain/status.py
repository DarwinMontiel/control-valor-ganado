"""Interpretación de los índices CPI y SPI."""

from decimal import Decimal
from enum import StrEnum


class CostStatus(StrEnum):
    UNDER_BUDGET = "UNDER_BUDGET"
    ON_BUDGET = "ON_BUDGET"
    OVER_BUDGET = "OVER_BUDGET"
    NOT_STARTED = "NOT_STARTED"
    NOT_CALCULABLE = "NOT_CALCULABLE"


class ScheduleStatus(StrEnum):
    AHEAD = "AHEAD"
    ON_SCHEDULE = "ON_SCHEDULE"
    BEHIND = "BEHIND"
    NOT_STARTED = "NOT_STARTED"


COST_STATUS_MESSAGES: dict[CostStatus, str] = {
    CostStatus.UNDER_BUDGET: "Bajo presupuesto: el trabajo hecho costó menos de lo planeado.",
    CostStatus.ON_BUDGET: "En presupuesto: el trabajo hecho costó lo planeado.",
    CostStatus.OVER_BUDGET: "Sobre presupuesto: se está gastando más de lo que se avanza.",
    CostStatus.NOT_STARTED: "Sin iniciar: no hay costo ni avance registrados.",
    CostStatus.NOT_CALCULABLE: (
        "No calculable: hay avance sin costo registrado. Revise si falta cargar el costo real."
    ),
}

SCHEDULE_STATUS_MESSAGES: dict[ScheduleStatus, str] = {
    ScheduleStatus.AHEAD: "Adelantado: se ha hecho más trabajo del planeado a la fecha.",
    ScheduleStatus.ON_SCHEDULE: "A tiempo: el avance coincide con el plan.",
    ScheduleStatus.BEHIND: "Atrasado: se ha hecho menos trabajo del planeado a la fecha.",
    ScheduleStatus.NOT_STARTED: "Sin iniciar: no había trabajo planeado ni avance a la fecha.",
}

_ZERO = Decimal(0)


def classify_cost(earned_value: Decimal, actual_cost: Decimal) -> CostStatus:
    """Clasifica el desempeño de costo.

    Se compara EV contra AC en lugar del CPI redondeado: con AC > 0, CPI > 1 equivale
    exactamente a EV > AC, y así el redondeo nunca cambia la interpretación.
    """
    if actual_cost == _ZERO:
        return CostStatus.NOT_STARTED if earned_value == _ZERO else CostStatus.NOT_CALCULABLE
    if earned_value > actual_cost:
        return CostStatus.UNDER_BUDGET
    if earned_value < actual_cost:
        return CostStatus.OVER_BUDGET
    return CostStatus.ON_BUDGET


def classify_schedule(earned_value: Decimal, planned_value: Decimal) -> ScheduleStatus:
    """Clasifica el desempeño de cronograma comparando EV contra PV.

    Con PV = 0 y EV > 0 el SPI no existe, pero el trabajo sí va adelantado respecto al plan.
    """
    if planned_value == _ZERO and earned_value == _ZERO:
        return ScheduleStatus.NOT_STARTED
    if earned_value > planned_value:
        return ScheduleStatus.AHEAD
    if earned_value < planned_value:
        return ScheduleStatus.BEHIND
    return ScheduleStatus.ON_SCHEDULE
