def _register_user(client, email="admin@test.com", password="secret123", full_name="Admin User"):
    """Helper to register a user via the API."""
    return client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )


def _login_user(client, email="admin@test.com", password="secret123"):
    """Helper to login a user via the API."""
    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_first_user(client):
    """The first registered user should succeed and become admin."""
    response = _register_user(client)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"
    assert "id" in data


def test_login(client):
    """A registered user should be able to login and receive a token."""
    _register_user(client)
    response = _login_user(client)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_me(client):
    """An authenticated user should be able to fetch their own profile."""
    _register_user(client)
    login_response = _login_user(client)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["full_name"] == "Admin User"
    assert data["role"] == "admin"


def test_login_wrong_password(client):
    """Login with an incorrect password should return 401."""
    _register_user(client)
    response = _login_user(client, password="wrongpassword")
    assert response.status_code == 401
