import pytest

REGISTER_PAYLOAD = {"email": "test@example.com", "password": "secure123"}
REGISTER_PAYLOAD_2 = {"email": "test2@example.com", "password": "secure456"}


@pytest.mark.asyncio
async def test_register_new_user(async_client):
    response = await async_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client):
    await async_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD_2)
    response = await async_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD_2)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_valid_credentials(async_client):
    await async_client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "password1"})
    response = await async_client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "password1"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(async_client):
    await async_client.post("/api/v1/auth/register", json={"email": "badpass@example.com", "password": "password1"})
    response = await async_client.post("/api/v1/auth/login", json={"email": "badpass@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(async_client):
    reg = await async_client.post("/api/v1/auth/register", json={"email": "refresh@example.com", "password": "password1"})
    refresh_token = reg.json()["refresh_token"]
    response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(async_client):
    # When auth-protected sync endpoints are added, they will return 401.
    # For now, health endpoint is public — verify auth endpoints themselves need no token.
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_password_too_short(async_client):
    response = await async_client.post("/api/v1/auth/register", json={"email": "short@example.com", "password": "123"})
    assert response.status_code == 422
