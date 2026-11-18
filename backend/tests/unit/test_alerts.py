from decimal import Decimal

from app.domain.alerts import AlertSeverity, AlertType, evaluate_alerts
from app.domain.evm import ActivityProgress, calculate_activity_indicators, consolidate


def alerts_for(bac: str, planned: str, actual: str, cost: str) -> dict[AlertType, AlertSeverity]:
    progress = ActivityProgress(Decimal(bac), Decimal(planned), Decimal(actual), Decimal(cost))
    return {
        alert.type: alert.severity
        for alert in evaluate_alerts(calculate_activity_indicators(progress))
    }


def test_healthy_activity_has_no_alerts() -> None:
    assert alerts_for("1000", "50", "60", "500") == {}


def test_exactly_on_plan_has_no_alerts() -> None:
    assert alerts_for("1000", "50", "50", "500") == {}


def test_severe_overrun_and_delay_are_high() -> None:
    assert alerts_for("20000000", "60", "40", "10000000") == {
        AlertType.COST_OVERRUN: AlertSeverity.HIGH,
        AlertType.SCHEDULE_DELAY: AlertSeverity.HIGH,
        AlertType.PROJECTED_OVERRUN: AlertSeverity.MEDIUM,
    }


def test_small_deviation_is_medium() -> None:
    alerts = alerts_for("1000", "50", "48", "500")

    assert alerts[AlertType.COST_OVERRUN] is AlertSeverity.MEDIUM
    assert alerts[AlertType.SCHEDULE_DELAY] is AlertSeverity.MEDIUM


def test_threshold_is_inclusive_for_medium() -> None:
    assert alerts_for("1000", "50", "45", "500")[AlertType.SCHEDULE_DELAY] is AlertSeverity.MEDIUM
    assert alerts_for("1000", "50", "44.99", "500")[AlertType.SCHEDULE_DELAY] is AlertSeverity.HIGH


def test_cost_without_progress_replaces_cost_overrun() -> None:
    alerts = alerts_for("1000", "20", "0", "250")

    assert AlertType.COST_WITHOUT_PROGRESS in alerts
    assert AlertType.COST_OVERRUN not in alerts


def test_progress_without_cost_asks_to_check_data() -> None:
    assert alerts_for("1000", "30", "30", "0") == {
        AlertType.MISSING_ACTUAL_COST: AlertSeverity.MEDIUM
    }


def test_not_started_activity_with_nothing_planned_has_no_alerts() -> None:
    assert alerts_for("1000", "0", "0", "0") == {}


def test_alert_explains_observed_value() -> None:
    progress = ActivityProgress(Decimal("100"), Decimal("40"), Decimal("40"), Decimal("60"))

    alert = evaluate_alerts(calculate_activity_indicators(progress))[0]

    assert alert.indicator == "CPI"
    assert alert.observed_value == Decimal("0.6667")
    assert "0,67" in alert.message


def test_empty_project_has_no_alerts() -> None:
    assert evaluate_alerts(consolidate([])) == []
