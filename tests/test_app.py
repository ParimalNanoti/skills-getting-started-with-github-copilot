import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app
import src.app as app_module


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before/after each test to avoid state bleed."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Basketball Club" in data


def test_signup_and_prevent_duplicate(client):
    activity = "Basketball Club"
    email = "tester@example.com"

    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in client.get("/activities").json()[activity]["participants"]

    # duplicate signup should fail
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp2.status_code == 400


def test_unregister_flow(client):
    activity = "Basketball Club"
    email = "to_remove@example.com"

    # sign up then unregister
    client.post(f"/activities/{activity}/signup", params={"email": email})
    assert email in client.get("/activities").json()[activity]["participants"]

    resp = client.post(f"/activities/{activity}/unregister", params={"email": email})
    assert resp.status_code == 200
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_not_registered_returns_400(client):
    activity = "Basketball Club"
    email = "not@registered.com"

    resp = client.post(f"/activities/{activity}/unregister", params={"email": email})
    assert resp.status_code == 400


def test_activity_not_found_returns_404(client):
    resp = client.post("/activities/NoSuchActivity/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404

    resp2 = client.post("/activities/NoSuchActivity/unregister", params={"email": "a@b.com"})
    assert resp2.status_code == 404
