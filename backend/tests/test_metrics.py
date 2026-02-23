def _register_and_login(client):
    """Helper to register the first user (admin) and return the auth token."""
    client.post(
        "/api/auth/register",
        json={
            "email": "admin@test.com",
            "password": "secret123",
            "full_name": "Admin User",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@test.com",
            "password": "secret123",
        },
    )
    return login_response.json()["access_token"]


def test_health(client):
    """The health endpoint should return 200 with status healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_overview_empty(client):
    """Overview on an empty database should return total_rounds=0."""
    token = _register_and_login(client)
    response = client.get(
        "/api/metrics/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rounds"] == 0
    assert data["active_clients"] == 0


def test_auc_history_empty(client):
    """AUC history on an empty database should return an empty list."""
    token = _register_and_login(client)
    response = client.get(
        "/api/metrics/auc-history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_privacy(client):
    """Privacy metrics should return the expected static values."""
    token = _register_and_login(client)
    response = client.get(
        "/api/metrics/privacy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dp_epsilon"] == 1.0
    assert data["dp_delta"] == 1e-5
    assert data["encryption_coverage_pct"] == 50.0
    assert data["avg_noise_magnitude"] == 0.01
