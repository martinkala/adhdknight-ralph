import pytest

REQUIRED_PATHS = [
    "/api/v1/compute/daily",
    "/api/v1/compute/range",
    "/api/v1/compute/android-integration",
    "/api/v1/health",
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
