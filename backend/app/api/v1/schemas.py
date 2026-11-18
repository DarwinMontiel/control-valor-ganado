"""Contrato HTTP (request y response). Los montos viajan como texto decimal para no perder
precisión en JSON."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.application.services import (
    ActivityAnalysis,
    ActivityFields,
    ProjectAnalysis,
    ProjectFields,
    ScopedAlert,
)
from app.domain.alerts import AlertSeverity, AlertType
from app.domain.status import (
    COST_STATUS_MESSAGES,
    SCHEDULE_STATUS_MESSAGES,
    CostStatus,
    PerformanceBand,
    ScheduleStatus,
)
from app.infrastructure.models import NAME_MAX_LENGTH

DESCRIPTION_MAX_LENGTH = 2000
MONEY_MAX_DIGITS = 18
MONEY_DECIMALS = 2
PERCENT_MAX_DIGITS = 5

Name = Annotated[str, Field(min_length=1, max_length=NAME_MAX_LENGTH, examples=["Diseño"])]
Money = Annotated[
    Decimal, Field(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMALS, examples=["1000.00"])
]
Percent = Annotated[
    Decimal,
    Field(ge=0, le=100, max_digits=PERCENT_MAX_DIGITS, decimal_places=2, examples=["40.00"]),
]


class ProjectIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Name
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    start_date: date | None = None
    end_date: date | None = None
    cutoff_date: date | None = Field(
        default=None,
        description="Fecha de corte a la que se reporta el avance. Si se omite, es hoy.",
    )

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
        return self

    def to_fields(self) -> ProjectFields:
        return ProjectFields(**self.model_dump())


class ActivityIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Name
    budget_at_completion: Annotated[
        Money, Field(gt=0, description="BAC: presupuesto total planificado de la actividad.")
    ]
    planned_progress: Annotated[
        Percent, Field(description="Porcentaje de avance planificado a la fecha de corte.")
    ]
    actual_progress: Annotated[Percent, Field(description="Porcentaje de avance real completado.")]
    actual_cost: Annotated[
        Money, Field(ge=0, description="AC: costo real incurrido hasta la fecha de corte.")
    ]

    def to_fields(self) -> ActivityFields:
        return ActivityFields(**self.model_dump())


class IndicatorsOut(BaseModel):
    """Indicadores EVM. Un índice en ``null`` no se puede calcular (ver el estado)."""

    model_config = ConfigDict(from_attributes=True)

    budget_at_completion: Decimal = Field(description="BAC")
    planned_value: Decimal = Field(description="PV = % planificado × BAC")
    earned_value: Decimal = Field(description="EV = % real × BAC")
    actual_cost: Decimal = Field(description="AC")
    cost_variance: Decimal = Field(description="CV = EV − AC")
    schedule_variance: Decimal = Field(description="SV = EV − PV")
    cost_performance_index: Decimal | None = Field(description="CPI = EV / AC")
    schedule_performance_index: Decimal | None = Field(description="SPI = EV / PV")
    estimate_at_completion: Decimal | None = Field(description="EAC = BAC / CPI")
    variance_at_completion: Decimal | None = Field(description="VAC = BAC − EAC")
    estimate_is_reliable: bool | None = Field(
        description="false si el avance real (EV / BAC) es menor al 10 %: el EAC es poco confiable."
        " null si no hay EAC."
    )
    cost_status: CostStatus
    schedule_status: ScheduleStatus
    cost_band: PerformanceBand = Field(
        description="Semáforo del CPI: ≥ 1 favorable; 0,95 a 1 en tolerancia; < 0,95 desfavorable."
    )
    schedule_band: PerformanceBand = Field(
        description="Semáforo del SPI: ≥ 1 favorable; 0,95 a 1 en tolerancia; < 0,95 desfavorable."
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_interpretation(self) -> str:
        return COST_STATUS_MESSAGES[self.cost_status]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def schedule_interpretation(self) -> str:
        return SCHEDULE_STATUS_MESSAGES[self.schedule_status]


class ActivityOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    budget_at_completion: Decimal
    planned_progress: Decimal
    actual_progress: Decimal
    actual_cost: Decimal
    created_at: datetime
    updated_at: datetime
    indicators: IndicatorsOut

    @classmethod
    def from_analysis(cls, analysis: ActivityAnalysis) -> Self:
        activity = analysis.activity
        return cls(
            id=activity.id,
            project_id=activity.project_id,
            name=activity.name,
            budget_at_completion=activity.budget_at_completion,
            planned_progress=activity.planned_progress,
            actual_progress=activity.actual_progress,
            actual_cost=activity.actual_cost,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
            indicators=IndicatorsOut.model_validate(analysis.indicators),
        )


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    cutoff_date: date
    created_at: datetime
    updated_at: datetime
    activity_count: int
    indicators: IndicatorsOut = Field(description="Indicadores consolidados del proyecto.")

    @classmethod
    def from_analysis(cls, analysis: ProjectAnalysis) -> Self:
        project = analysis.project
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            start_date=project.start_date,
            end_date=project.end_date,
            cutoff_date=project.cutoff_date,
            created_at=project.created_at,
            updated_at=project.updated_at,
            activity_count=len(analysis.activities),
            indicators=IndicatorsOut.model_validate(analysis.indicators),
        )


class AlertOut(BaseModel):
    """Alerta determinista: indica qué indicador la disparó y con qué valor."""

    type: AlertType
    severity: AlertSeverity
    indicator: str = Field(examples=["CPI"])
    observed_value: Decimal
    message: str
    activity_id: uuid.UUID | None = Field(description="null si la alerta es del proyecto.")
    scope_name: str = Field(description="Nombre del proyecto o de la actividad.")

    @classmethod
    def from_scoped(cls, scoped: ScopedAlert) -> Self:
        alert = scoped.alert
        return cls(
            type=alert.type,
            severity=alert.severity,
            indicator=alert.indicator,
            observed_value=alert.observed_value,
            message=alert.message,
            activity_id=scoped.activity_id,
            scope_name=scoped.scope_name,
        )


class ProjectDetailOut(ProjectOut):
    activities: list[ActivityOut]
    alerts: list[AlertOut]

    @classmethod
    def from_analysis(cls, analysis: ProjectAnalysis) -> Self:
        summary = ProjectOut.from_analysis(analysis)
        return cls(
            **summary.model_dump(exclude={"indicators"}),
            indicators=summary.indicators,
            activities=[ActivityOut.from_analysis(item) for item in analysis.activities],
            alerts=[AlertOut.from_scoped(item) for item in analysis.alerts],
        )


class ProjectPageOut(BaseModel):
    items: list[ProjectOut]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    code: str = Field(examples=["PROJECT_NOT_FOUND"])
    message: str
    details: list[dict[str, object]] | None = None


class ErrorOut(BaseModel):
    error: ErrorDetail
