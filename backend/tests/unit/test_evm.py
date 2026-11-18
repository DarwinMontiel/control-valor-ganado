"""Pruebas del motor EVM.

Los valores esperados se calcularon a mano (ver docs/EVM_METHODOLOGY.md), no con el código bajo
prueba.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.errors import InvalidActivityError
from app.domain.evm import ActivityProgress, calculate_activity_indicators, consolidate
from app.domain.status import CostStatus, PerformanceBand, ScheduleStatus, classify_band


def activity(bac: str, planned: str, actual: str, cost: str) -> ActivityProgress:
    return ActivityProgress(
        budget_at_completion=Decimal(bac),
        planned_progress=Decimal(planned),
        actual_progress=Decimal(actual),
        actual_cost=Decimal(cost),
    )


DESIGN = activity("10000000", "100", "100", "9000000")
DEVELOPMENT = activity("20000000", "60", "40", "10000000")
TESTING = activity("5000000", "20", "0", "0")


class TestActivityIndicators:
    def test_finished_activity_under_budget(self) -> None:
        result = calculate_activity_indicators(DESIGN)

        assert result.planned_value == Decimal("10000000.00")
        assert result.earned_value == Decimal("10000000.00")
        assert result.cost_variance == Decimal("1000000.00")
        assert result.schedule_variance == Decimal("0.00")
        assert result.cost_performance_index == Decimal("1.1111")
        assert result.schedule_performance_index == Decimal("1.0000")
        assert result.estimate_at_completion == Decimal("9000000.00")
        assert result.variance_at_completion == Decimal("1000000.00")
        assert result.cost_status is CostStatus.UNDER_BUDGET
        assert result.schedule_status is ScheduleStatus.ON_SCHEDULE

    def test_activity_over_budget_and_behind(self) -> None:
        result = calculate_activity_indicators(DEVELOPMENT)

        assert result.planned_value == Decimal("12000000.00")
        assert result.earned_value == Decimal("8000000.00")
        assert result.cost_variance == Decimal("-2000000.00")
        assert result.schedule_variance == Decimal("-4000000.00")
        assert result.cost_performance_index == Decimal("0.8000")
        assert result.schedule_performance_index == Decimal("0.6667")
        assert result.estimate_at_completion == Decimal("25000000.00")
        assert result.variance_at_completion == Decimal("-5000000.00")
        assert result.cost_status is CostStatus.OVER_BUDGET
        assert result.schedule_status is ScheduleStatus.BEHIND

    def test_trycore_example_spent_60_percent_with_40_percent_done(self) -> None:
        result = calculate_activity_indicators(activity("100", "40", "40", "60"))

        assert result.cost_performance_index == Decimal("0.6667")
        assert result.estimate_at_completion == Decimal("150.00")
        assert result.cost_status is CostStatus.OVER_BUDGET

    def test_exactly_on_budget_and_on_schedule(self) -> None:
        result = calculate_activity_indicators(activity("1000", "50", "50", "500"))

        assert result.cost_performance_index == Decimal("1.0000")
        assert result.cost_status is CostStatus.ON_BUDGET
        assert result.schedule_status is ScheduleStatus.ON_SCHEDULE
        assert result.variance_at_completion == Decimal("0.00")


class TestEdgeCases:
    def test_not_started_activity_has_no_cost_indices(self) -> None:
        result = calculate_activity_indicators(TESTING)

        assert result.cost_performance_index is None
        assert result.estimate_at_completion is None
        assert result.variance_at_completion is None
        assert result.schedule_performance_index == Decimal("0.0000")
        assert result.cost_status is CostStatus.NOT_STARTED
        assert result.schedule_status is ScheduleStatus.BEHIND

    def test_progress_without_cost_is_not_calculable_instead_of_infinite(self) -> None:
        result = calculate_activity_indicators(activity("1000", "50", "30", "0"))

        assert result.cost_performance_index is None
        assert result.estimate_at_completion is None
        assert result.cost_variance == Decimal("300.00")
        assert result.cost_status is CostStatus.NOT_CALCULABLE

    def test_cost_without_progress_gives_zero_cpi_but_no_estimate(self) -> None:
        result = calculate_activity_indicators(activity("1000", "50", "0", "200"))

        assert result.cost_performance_index == Decimal("0.0000")
        assert result.estimate_at_completion is None
        assert result.variance_at_completion is None
        assert result.cost_status is CostStatus.OVER_BUDGET

    def test_nothing_planned_nor_done_yet(self) -> None:
        result = calculate_activity_indicators(activity("1000", "0", "0", "0"))

        assert result.schedule_performance_index is None
        assert result.schedule_status is ScheduleStatus.NOT_STARTED

    def test_work_done_before_it_was_planned_is_ahead_without_spi(self) -> None:
        result = calculate_activity_indicators(activity("1000", "0", "10", "100"))

        assert result.schedule_performance_index is None
        assert result.schedule_variance == Decimal("100.00")
        assert result.schedule_status is ScheduleStatus.AHEAD

    def test_status_follows_the_rounded_figures_the_user_sees(self) -> None:
        # Caso encontrado por Hypothesis: PV = 0,000001 se mostraba como 0,00 pero el
        # estado decía "Atrasado" y la variación salía como -0.00.
        result = calculate_activity_indicators(activity("0.01", "0.01", "0", "0"))

        assert result.schedule_variance == Decimal("0.00")
        assert not result.schedule_variance.is_signed()
        assert result.schedule_status is ScheduleStatus.NOT_STARTED

    def test_actual_cost_above_budget_is_valid_overrun(self) -> None:
        result = calculate_activity_indicators(activity("1000", "100", "80", "1500"))

        assert result.cost_performance_index == Decimal("0.5333")
        assert result.estimate_at_completion == Decimal("1875.00")
        assert result.variance_at_completion == Decimal("-875.00")

    @pytest.mark.parametrize(
        ("bac", "planned", "actual", "cost"),
        [
            ("0", "10", "10", "10"),
            ("-1", "10", "10", "10"),
            ("1000", "-0.01", "10", "10"),
            ("1000", "100.01", "10", "10"),
            ("1000", "10", "101", "10"),
            ("1000", "10", "10", "-5"),
        ],
    )
    def test_rejects_invalid_activity_data(
        self, bac: str, planned: str, actual: str, cost: str
    ) -> None:
        with pytest.raises(InvalidActivityError):
            activity(bac, planned, actual, cost)


class TestConsolidation:
    def test_reference_project_matches_hand_calculation(self) -> None:
        result = consolidate([DESIGN, DEVELOPMENT, TESTING])

        assert result.budget_at_completion == Decimal("35000000.00")
        assert result.planned_value == Decimal("23000000.00")
        assert result.earned_value == Decimal("18000000.00")
        assert result.actual_cost == Decimal("19000000.00")
        assert result.cost_variance == Decimal("-1000000.00")
        assert result.schedule_variance == Decimal("-5000000.00")
        assert result.cost_performance_index == Decimal("0.9474")
        assert result.schedule_performance_index == Decimal("0.7826")
        assert result.estimate_at_completion == Decimal("36944444.44")
        assert result.variance_at_completion == Decimal("-1944444.44")
        assert result.cost_status is CostStatus.OVER_BUDGET
        assert result.schedule_status is ScheduleStatus.BEHIND

    def test_project_cpi_is_weighted_not_simple_average(self) -> None:
        simple_average = (Decimal("1.1111") + Decimal("0.8000")) / 2

        result = consolidate([DESIGN, DEVELOPMENT, TESTING])

        assert result.cost_performance_index != simple_average.quantize(Decimal("0.0001"))

    def test_project_without_activities(self) -> None:
        result = consolidate([])

        assert result.budget_at_completion == Decimal("0.00")
        assert result.cost_performance_index is None
        assert result.schedule_performance_index is None
        assert result.estimate_at_completion is None
        assert result.cost_status is CostStatus.NOT_STARTED
        assert result.schedule_status is ScheduleStatus.NOT_STARTED

    def test_single_activity_project_equals_activity(self) -> None:
        assert consolidate([DEVELOPMENT]) == calculate_activity_indicators(DEVELOPMENT)


money = st.decimals(min_value="0.01", max_value="1000000000", places=2)
percent = st.decimals(min_value="0", max_value="100", places=2)
cost = st.decimals(min_value="0", max_value="1000000000", places=2)
activities = st.builds(ActivityProgress, money, percent, percent, cost)


class TestProperties:
    @given(st.lists(activities, max_size=8))
    def test_consolidated_bases_are_sums_of_activities(self, items: list[ActivityProgress]) -> None:
        project = consolidate(items)
        per_activity = [calculate_activity_indicators(item) for item in items]
        tolerance = Decimal("0.01") * len(items)

        assert abs(project.earned_value - sum(a.earned_value for a in per_activity)) <= tolerance
        assert abs(project.actual_cost - sum(a.actual_cost for a in per_activity)) <= tolerance

    @given(activities)
    def test_variances_and_status_are_consistent(self, item: ActivityProgress) -> None:
        result = calculate_activity_indicators(item)

        assert result.cost_variance == result.earned_value - result.actual_cost
        if result.cost_status is CostStatus.OVER_BUDGET:
            assert result.cost_variance < 0
        if result.schedule_status is ScheduleStatus.BEHIND:
            assert result.schedule_variance < 0

    @given(activities)
    def test_estimate_at_completion_is_budget_over_cpi(self, item: ActivityProgress) -> None:
        result = calculate_activity_indicators(item)

        if result.estimate_at_completion is not None:
            exact = result.budget_at_completion * result.actual_cost / result.earned_value
            assert abs(result.estimate_at_completion - exact) <= Decimal("0.005")


class TestPerformanceBand:
    """Mi decisión: una desviación desfavorable de hasta el 5 % se ve como "en línea"."""

    @pytest.mark.parametrize(
        ("index", "band"),
        [
            (None, PerformanceBand.NOT_AVAILABLE),
            ("0.9499", PerformanceBand.UNFAVORABLE),
            ("0.95", PerformanceBand.WITHIN_TOLERANCE),
            ("0.99", PerformanceBand.WITHIN_TOLERANCE),
            ("1.0000", PerformanceBand.FAVORABLE),
            ("1.03", PerformanceBand.FAVORABLE),
        ],
    )
    def test_band_limits(self, index: str | None, band: PerformanceBand) -> None:
        assert classify_band(None if index is None else Decimal(index)) is band

    def test_small_overrun_is_within_tolerance_but_still_over_budget(self) -> None:
        result = calculate_activity_indicators(activity("1000", "50", "50", "505"))

        assert result.cost_performance_index == Decimal("0.9901")
        assert result.cost_status is CostStatus.OVER_BUDGET
        assert result.cost_band is PerformanceBand.WITHIN_TOLERANCE

    def test_reference_project_bands(self) -> None:
        result = consolidate([DESIGN, DEVELOPMENT, TESTING])

        # |0,9474 − 1| = 0,0526: queda justo fuera del 5 %.
        assert result.cost_band is PerformanceBand.UNFAVORABLE
        assert result.schedule_band is PerformanceBand.UNFAVORABLE
