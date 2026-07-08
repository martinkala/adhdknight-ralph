package com.example.madhdtracker.data.remote

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class ApiClientTest {

    private fun buildClient(engine: MockEngine): ApiClient {
        val httpClient = HttpClient(engine) {
            install(ContentNegotiation) {
                json(Json { ignoreUnknownKeys = true })
            }
        }
        return ApiClient(httpClient)
    }

    @Test
    fun `login returns LoginResponse on 200`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"access_token":"tok123","token_type":"bearer"}""",
                status = HttpStatusCode.OK,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.login("http://localhost:8095", "test@example.com", "password")

        assertTrue(result.isSuccess)
        val resp = result.getOrThrow()
        assertEquals("tok123", resp.access_token)
        assertEquals("bearer", resp.token_type)
    }

    @Test
    fun `login returns ApiException on 401`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"detail":"Incorrect credentials"}""",
                status = HttpStatusCode.Unauthorized,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.login("http://localhost:8095", "bad@example.com", "wrong")

        assertTrue(result.isFailure)
        val ex = result.exceptionOrNull()
        assertTrue(ex is ApiException)
        assertEquals(401, (ex as ApiException).statusCode)
    }

    @Test
    fun `register returns RegisterResponse on 201`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"email":"new@example.com","created_at":"2024-01-01T00:00:00"}""",
                status = HttpStatusCode.Created,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.register("http://localhost:8095", "new@example.com", "password123")

        assertTrue(result.isSuccess)
        val resp = result.getOrThrow()
        assertEquals("new@example.com", resp.email)
    }

    @Test
    fun `register returns ApiException on 409 conflict`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"detail":"Email already registered"}""",
                status = HttpStatusCode.Conflict,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.register("http://localhost:8095", "exists@example.com", "password123")

        assertTrue(result.isFailure)
        val ex = result.exceptionOrNull()
        assertTrue(ex is ApiException)
        assertEquals(409, (ex as ApiException).statusCode)
    }

    @Test
    fun `getMe returns MeResponse on 200`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"email":"user@example.com","created_at":"2024-01-01T00:00:00","total_days":42}""",
                status = HttpStatusCode.OK,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.getMe("http://localhost:8095", "tok123")

        assertTrue(result.isSuccess)
        val resp = result.getOrThrow()
        assertEquals("user@example.com", resp.email)
        assertEquals(42, resp.total_days)
    }

    @Test
    fun `getMe returns ApiException on 401`() = runTest {
        val engine = MockEngine { _ ->
            respond(
                content = """{"detail":"Could not validate credentials"}""",
                status = HttpStatusCode.Unauthorized,
                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            )
        }
        val client = buildClient(engine)
        val result = client.getMe("http://localhost:8095", "expired_token")

        assertTrue(result.isFailure)
        val ex = result.exceptionOrNull()
        assertTrue(ex is ApiException)
        assertEquals(401, (ex as ApiException).statusCode)
    }

    @Test
    fun `login returns failure on server unavailable`() = runTest {
        val engine = MockEngine { _ ->
            throw IOException("Connection refused")
        }
        val client = buildClient(engine)
        val result = client.login("http://localhost:8095", "test@example.com", "password")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is IOException)
    }

    @Test
    fun `checkReachable returns false on server unavailable`() = runTest {
        val engine = MockEngine { _ ->
            throw IOException("Connection refused")
        }
        val client = buildClient(engine)
        val reachable = client.checkReachable("http://localhost:8095")

        assertFalse(reachable)
    }
}
