"""Contrato de cada endpoint contra PostgreSQL real."""

import uuid
from typing import Any

import pytest
from starlette.testclient import TestClient

pytestmark = pytest.mark.integration

API = "/api/v1"
MISSING_ID = uuid.UUID(int=0)
INDICATOR_KEYS = {
    "budget_at_completion",
    "planned_value",
    "earned_value",
    "actual_cost",
    "cost_variance",
    "schedule_variance",
    "cost_performance_index",
    "schedule_performance_index",
    "estimate_at_completion",
    "variance_at_completion",
    "estimate_is_reliable",
    "cost_status",
    "schedule_status",
    "cost_band",
    "schedule_band",
    "cost_interpretation",
    "schedule_interpretation",
}
DESIGN = {
    "name": "Diseño",
    "budget_at_completion": "10000000",
    "planned_progress": "100",
    "actual_progress": "100",
    "actual_cost": "9000000",
}
DEVELOPMENT = {
    "name": "Desarrollo",
    "budget_at_completion": "20000000",
    "planned_progress": "60",
    "actual_progress": "40",
    "actual_cost": "10000000",
}
TESTING = {
    "name": "Pruebas",
    "budget_at_completion": "5000000",
    "planned_progress": "20",
    "actual_progress": "0",
    "actual_cost": "0",
}


def create_project(client: TestClient, name: str = "Portal de clientes") -> dict[str, Any]:
    response = client.post(f"{API}/projects", json={"name": name, "cutoff_date": "2026-11-17"})
    assert response.status_code == 201
    return dict(response.json())


def create_activity(client: TestClient, project_id: str, body: dict[str, str]) -> dict[str, Any]:
    response = client.post(f"{API}/projects/{project_id}/activities", json=body)
    assert response.status_code == 201
    return dict(response.json())


def assert_error(response: Any, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


class TestProjects:
    def test_create_returns_project_with_empty_indicators(self, client: TestClient) -> None:
        body = create_project(client)

        assert body["name"] == "Portal de clientes"
        assert body["cutoff_date"] == "2026-11-17"
        assert body["activity_count"] == 0
        assert body["activities"] == []
        assert body["alerts"] == []
        assert set(body["indicators"]) == INDICATOR_KEYS
        assert body["indicators"]["cost_performance_index"] is None
        assert body["indicators"]["cost_status"] == "NOT_STARTED"

    def test_create_defaults_cutoff_date_to_today(self, client: TestClient) -> None:
        response = client.post(f"{API}/projects", json={"name": "Sin fecha"})

        assert response.status_code == 201
        assert response.json()["cutoff_date"]

    def test_create_rejects_end_before_start(self, client: TestClient) -> None:
        response = client.post(
            f"{API}/projects",
            json={"name": "X", "start_date": "2026-12-01", "end_date": "2026-11-01"},
        )

        assert_error(response, 422, "VALIDATION_ERROR")

    def test_create_rejects_blank_name(self, client: TestClient) -> None:
        response = client.post(f"{API}/projects", json={"name": "   "})

        assert_error(response, 422, "VALIDATION_ERROR")
        assert response.json()["error"]["details"][0]["field"] == "name"

    def test_list_is_paginated_and_searchable(self, client: TestClient) -> None:
        for name in ("Alfa", "Beta", "Gamma"):
            create_project(client, name)

        page = client.get(f"{API}/projects", params={"limit": 2}).json()
        found = client.get(f"{API}/projects", params={"search": "bet"}).json()

        assert page["total"] == 3
        assert len(page["items"]) == 2
        assert page["limit"] == 2
        assert set(page["items"][0]["indicators"]) == INDICATOR_KEYS
        assert [item["name"] for item in found["items"]] == ["Beta"]

    def test_list_rejects_page_size_over_limit(self, client: TestClient) -> None:
        assert_error(client.get(f"{API}/projects", params={"limit": 101}), 422, "VALIDATION_ERROR")

    def test_get_returns_consolidated_indicators_of_reference_project(
        self, client: TestClient
    ) -> None:
        project = create_project(client)
        for body in (DESIGN, DEVELOPMENT, TESTING):
            create_activity(client, project["id"], body)

        body = client.get(f"{API}/projects/{project['id']}").json()
        indicators = body["indicators"]

        assert body["activity_count"] == 3
        assert indicators["planned_value"] == "23000000.00"
        assert indicators["earned_value"] == "18000000.00"
        assert indicators["actual_cost"] == "19000000.00"
        assert indicators["cost_performance_index"] == "0.9474"
        assert indicators["schedule_performance_index"] == "0.7826"
        assert indicators["estimate_at_completion"] == "36944444.44"
        assert indicators["variance_at_completion"] == "-1944444.44"
        assert indicators["cost_status"] == "OVER_BUDGET"
        assert indicators["schedule_status"] == "BEHIND"
        assert "Sobre presupuesto" in indicators["cost_interpretation"]
        assert [item["name"] for item in body["activities"]] == ["Diseño", "Desarrollo", "Pruebas"]

    def test_get_returns_alerts_with_their_scope(self, client: TestClient) -> None:
        project = create_project(client)
        create_activity(client, project["id"], DESIGN)
        development = create_activity(client, project["id"], DEVELOPMENT)

        alerts = client.get(f"{API}/projects/{project['id']}").json()["alerts"]
        development_alerts = {
            alert["type"] for alert in alerts if alert["activity_id"] == development["id"]
        }

        assert {"COST_OVERRUN", "SCHEDULE_DELAY", "PROJECTED_OVERRUN"} <= development_alerts
        assert alerts[0]["severity"] == "HIGH"
        assert set(alerts[0]) == {
            "type",
            "severity",
            "indicator",
            "observed_value",
            "message",
            "activity_id",
            "scope_name",
        }

    def test_get_unknown_project(self, client: TestClient) -> None:
        assert_error(client.get(f"{API}/projects/{MISSING_ID}"), 404, "PROJECT_NOT_FOUND")

    def test_get_rejects_malformed_id(self, client: TestClient) -> None:
        assert_error(client.get(f"{API}/projects/no-es-uuid"), 422, "VALIDATION_ERROR")

    def test_update_replaces_fields(self, client: TestClient) -> None:
        project = create_project(client)

        response = client.put(
            f"{API}/projects/{project['id']}",
            json={"name": "Portal v2", "description": "Fase 2", "cutoff_date": "2026-12-01"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Portal v2"
        assert response.json()["description"] == "Fase 2"
        assert response.json()["cutoff_date"] == "2026-12-01"

    def test_update_unknown_project(self, client: TestClient) -> None:
        response = client.put(f"{API}/projects/{MISSING_ID}", json={"name": "X"})

        assert_error(response, 404, "PROJECT_NOT_FOUND")

    def test_delete_removes_project_and_its_activities(self, client: TestClient) -> None:
        project = create_project(client)
        activity = create_activity(client, project["id"], DESIGN)

        response = client.delete(f"{API}/projects/{project['id']}")

        assert response.status_code == 204
        assert client.get(f"{API}/projects/{project['id']}").status_code == 404
        assert client.get(f"{API}/activities/{activity['id']}").status_code == 404

    def test_delete_unknown_project(self, client: TestClient) -> None:
        assert_error(client.delete(f"{API}/projects/{MISSING_ID}"), 404, "PROJECT_NOT_FOUND")


class TestActivities:
    def test_create_returns_activity_with_indicators(self, client: TestClient) -> None:
        project = create_project(client)

        body = create_activity(client, project["id"], DEVELOPMENT)

        assert body["project_id"] == project["id"]
        assert body["budget_at_completion"] == "20000000.00"
        assert set(body["indicators"]) == INDICATOR_KEYS
        assert body["indicators"]["planned_value"] == "12000000.00"
        assert body["indicators"]["earned_value"] == "8000000.00"
        assert body["indicators"]["cost_variance"] == "-2000000.00"
        assert body["indicators"]["schedule_variance"] == "-4000000.00"
        assert body["indicators"]["cost_performance_index"] == "0.8000"
        assert body["indicators"]["schedule_performance_index"] == "0.6667"
        assert body["indicators"]["estimate_at_completion"] == "25000000.00"
        assert body["indicators"]["variance_at_completion"] == "-5000000.00"

    def test_activity_without_cost_returns_null_indices_not_zero(self, client: TestClient) -> None:
        project = create_project(client)

        indicators = create_activity(client, project["id"], TESTING)["indicators"]

        assert indicators["cost_performance_index"] is None
        assert indicators["estimate_at_completion"] is None
        assert indicators["cost_status"] == "NOT_STARTED"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("budget_at_completion", "0"),
            ("planned_progress", "100.5"),
            ("actual_progress", "-1"),
            ("actual_cost", "-10"),
            ("actual_cost", "1.001"),
            ("name", ""),
        ],
    )
    def test_create_rejects_invalid_values(
        self, client: TestClient, field: str, value: str
    ) -> None:
        project = create_project(client)

        response = client.post(
            f"{API}/projects/{project['id']}/activities", json=DESIGN | {field: value}
        )

        assert_error(response, 422, "VALIDATION_ERROR")
        assert response.json()["error"]["details"][0]["field"] == field

    def test_create_in_unknown_project(self, client: TestClient) -> None:
        response = client.post(f"{API}/projects/{MISSING_ID}/activities", json=DESIGN)

        assert_error(response, 404, "PROJECT_NOT_FOUND")

    def test_list_for_project(self, client: TestClient) -> None:
        project = create_project(client)
        create_activity(client, project["id"], DESIGN)
        create_activity(client, project["id"], TESTING)

        response = client.get(f"{API}/projects/{project['id']}/activities")

        assert response.status_code == 200
        assert [item["name"] for item in response.json()] == ["Diseño", "Pruebas"]

    def test_list_for_unknown_project(self, client: TestClient) -> None:
        response = client.get(f"{API}/projects/{MISSING_ID}/activities")

        assert_error(response, 404, "PROJECT_NOT_FOUND")

    def test_get_activity(self, client: TestClient) -> None:
        project = create_project(client)
        activity = create_activity(client, project["id"], DESIGN)

        response = client.get(f"{API}/activities/{activity['id']}")

        assert response.status_code == 200
        assert response.json()["indicators"]["cost_status"] == "UNDER_BUDGET"

    def test_get_unknown_activity(self, client: TestClient) -> None:
        assert_error(client.get(f"{API}/activities/{MISSING_ID}"), 404, "ACTIVITY_NOT_FOUND")

    def test_update_recalculates_activity_and_project(self, client: TestClient) -> None:
        project = create_project(client)
        activity = create_activity(client, project["id"], DEVELOPMENT)

        response = client.put(
            f"{API}/activities/{activity['id']}",
            json=DEVELOPMENT | {"actual_progress": "75", "actual_cost": "14000000"},
        )
        consolidated = client.get(f"{API}/projects/{project['id']}").json()["indicators"]

        assert response.status_code == 200
        assert response.json()["indicators"]["earned_value"] == "15000000.00"
        assert response.json()["indicators"]["schedule_status"] == "AHEAD"
        assert consolidated["earned_value"] == "15000000.00"
        assert consolidated["cost_performance_index"] == "1.0714"

    def test_update_unknown_activity(self, client: TestClient) -> None:
        response = client.put(f"{API}/activities/{MISSING_ID}", json=DESIGN)

        assert_error(response, 404, "ACTIVITY_NOT_FOUND")

    def test_update_rejects_invalid_progress(self, client: TestClient) -> None:
        project = create_project(client)
        activity = create_activity(client, project["id"], DESIGN)

        response = client.put(
            f"{API}/activities/{activity['id']}", json=DESIGN | {"actual_progress": "120"}
        )

        assert_error(response, 422, "VALIDATION_ERROR")

    def test_delete_activity(self, client: TestClient) -> None:
        project = create_project(client)
        activity = create_activity(client, project["id"], DESIGN)

        response = client.delete(f"{API}/activities/{activity['id']}")

        assert response.status_code == 204
        assert client.get(f"{API}/projects/{project['id']}").json()["activity_count"] == 0

    def test_delete_unknown_activity(self, client: TestClient) -> None:
        assert_error(client.delete(f"{API}/activities/{MISSING_ID}"), 404, "ACTIVITY_NOT_FOUND")


class TestSystem:
    def test_health_checks_database(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_swagger_is_served_at_api_docs(self, client: TestClient) -> None:
        assert client.get("/api-docs").status_code == 200

    def test_every_operation_documents_its_errors(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()
        operations = [
            (path, method, operation)
            for path, methods in spec["paths"].items()
            if path.startswith(API)
            for method, operation in methods.items()
        ]

        assert len(operations) == 10
        for path, method, operation in operations:
            assert operation.get("summary"), f"{method} {path} sin descripción"
            has_path_id = "{" in path
            if has_path_id:
                assert "404" in operation["responses"], f"{method} {path} sin 404"
            if method in {"post", "put"}:
                assert "422" in operation["responses"], f"{method} {path} sin 422"
