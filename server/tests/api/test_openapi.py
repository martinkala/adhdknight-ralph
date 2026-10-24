import pytest

REQUIRED_PATHS = [
    "/api/v1/compute/daily",
    "/api/v1/compute/range",
    "/api/v1/compute/android-integration",
    "/api/v1/health",
    "/api/v1/auth/register",
    "/api/v1/auth/change-password",
    "/api/v1/user/me",
    "/api/v1/user/settings",
]


@pytest.mark.asyncio
async def test_openapi_contains_required_endpoints(async_client):
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    paths = openapi.get("paths", {})
    for path in REQUIRED_PATHS:
        assert path in paths, f"Missing endpoint in OpenAPI spec: {path}"


@pytest.mark.asyncio
async def test_openapi_has_schema_version_example(async_client):
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    spec_text = response.text
    assert "schema_version" in spec_text


@pytest.mark.asyncio
async def test_openapi_title_and_version(async_client):
    response = await async_client.get("/openapi.json")
    info = response.json().get("info", {})
    assert info.get("title") == "ADHD Weight Vector Server"
    assert info.get("version") == "0.1.0"


@pytest.mark.asyncio
async def test_openapi_account_methods(async_client):
    paths = (await async_client.get("/openapi.json")).json()["paths"]
    assert "post" in paths["/api/v1/auth/change-password"]
    assert "delete" in paths["/api/v1/user/me"]
    assert {"get", "patch"} <= set(paths["/api/v1/user/settings"])
    register_schema = (await async_client.get("/openapi.json")).json()["components"]["schemas"]["RegisterRequest"]
    assert "invite_token" in register_schema["properties"]
