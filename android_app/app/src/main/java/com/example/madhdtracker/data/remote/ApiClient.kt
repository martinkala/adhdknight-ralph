package com.example.madhdtracker.data.remote

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.android.Android
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.timeout
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class LoginResponse(val access_token: String, val token_type: String, val refresh_token: String = "", val expires_in: Int = 900)

@Serializable
data class RefreshRequest(val refresh_token: String)

@Serializable
data class RegisterRequest(val email: String, val password: String)

@Serializable
data class RegisterResponse(val email: String, val created_at: String)

@Serializable
data class MeResponse(val email: String, val created_at: String, val total_days: Int)

@Serializable
data class SyncValueItem(
    val element_key: String,
    val value_binary: Int,
    val value_scale: Int?,
    val updated_at: String,
    val note: String? = null,
)

@Serializable
data class SyncDayItem(
    val date: String,
    val is_complete: Boolean = false,
    val updated_at: String,
    val values: List<SyncValueItem>,
)

@Serializable
data class EntityNodeSyncItem(
    val weight: Double,
    val impact: Int? = null,
    val parent: String? = null,
    val scale: Boolean = false,
    val scale_min: Int? = null,
    val scale_max: Int? = null,
)

@Serializable
data class BatchSyncRequest(
    val schema_version: String = "1.0",
    val app_id: String = APP_ID,
    val device_id: String? = null,
    // Active-only entity tree (leaves + their ancestor chain) so the server can recompute
    // and persist a DailyIndex per day (see IndexCalculator.computeDailyIndexGrouped for
    // the matching Android-side algorithm). Omit to sync without server-side computation.
    val entity_config: Map<String, EntityNodeSyncItem>? = null,
    val days: List<SyncDayItem>,
)

// Identifies which app is talking to the server, so one account (login) can be shared
// across multiple apps (e.g. "adhd_tracker", "food_diary") without their days colliding.
const val APP_ID = "adhd_tracker"

@Serializable
data class SyncSummaryResponse(
    val days_received: Int,
    val records_sent: Int,
    val records_accepted: Int,
    val records_conflicted: Int,
    val records_rejected: Int,
)

@Serializable
data class BatchSyncResponse(
    val sync_id: String,
    val summary: SyncSummaryResponse,
)

@Serializable
data class EntitiesVersionResponse(val app_id: String, val version: String)

class ApiClient(httpClient: HttpClient? = null) {

    val client: HttpClient = httpClient ?: HttpClient(Android) {
        install(ContentNegotiation) {
            json(Json { ignoreUnknownKeys = true })
        }
        install(HttpTimeout) {
            requestTimeoutMillis = 5_000
            connectTimeoutMillis = 5_000
        }
    }

    suspend fun login(baseUrl: String, email: String, password: String): Result<LoginResponse> {
        return runCatching {
            val response: HttpResponse = client.post("$baseUrl/api/v1/auth/login") {
                contentType(ContentType.Application.Json)
                setBody(LoginRequest(email, password))
            }
            if (response.status.isSuccess()) {
                response.body<LoginResponse>()
            } else {
                throw ApiException(response.status.value, "Login failed: ${response.status.description}")
            }
        }
    }

    suspend fun register(baseUrl: String, email: String, password: String): Result<RegisterResponse> {
        return runCatching {
            val response: HttpResponse = client.post("$baseUrl/api/v1/auth/register") {
                contentType(ContentType.Application.Json)
                setBody(RegisterRequest(email, password))
            }
            if (response.status.isSuccess()) {
                response.body<RegisterResponse>()
            } else {
                throw ApiException(response.status.value, "Register failed: ${response.status.description}")
            }
        }
    }

    suspend fun refreshToken(baseUrl: String, refreshToken: String): Result<LoginResponse> {
        return runCatching {
            val response: HttpResponse = client.post("$baseUrl/api/v1/auth/refresh") {
                contentType(ContentType.Application.Json)
                setBody(RefreshRequest(refreshToken))
            }
            if (response.status.isSuccess()) {
                response.body<LoginResponse>()
            } else {
                throw ApiException(response.status.value, "Refresh failed: ${response.status.description}")
            }
        }
    }

    suspend fun getMe(baseUrl: String, token: String): Result<MeResponse> {
        return runCatching {
            val response: HttpResponse = client.get("$baseUrl/api/v1/user/me?app_id=$APP_ID") {
                bearerAuth(token)
            }
            if (response.status.isSuccess()) {
                response.body<MeResponse>()
            } else {
                throw ApiException(response.status.value, "GetMe failed: ${response.status.description}")
            }
        }
    }

    suspend fun getEntitiesVersion(baseUrl: String, appId: String = APP_ID): Result<EntitiesVersionResponse> {
        return runCatching {
            val response: HttpResponse = client.get("$baseUrl/api/v1/config/entities/version?app_id=$appId")
            if (response.status.isSuccess()) {
                response.body<EntitiesVersionResponse>()
            } else {
                throw ApiException(response.status.value, "GetEntitiesVersion failed: ${response.status.description}")
            }
        }
    }

    suspend fun getEntitiesConfig(baseUrl: String, appId: String = APP_ID): Result<String> {
        return runCatching {
            val response: HttpResponse = client.get("$baseUrl/api/v1/config/entities?app_id=$appId")
            if (response.status.isSuccess()) {
                response.bodyAsText()
            } else {
                throw ApiException(response.status.value, "GetEntitiesConfig failed: ${response.status.description}")
            }
        }
    }

    suspend fun checkReachable(baseUrl: String): Boolean {
        return try {
            client.get(baseUrl)
            true
        } catch (e: Exception) {
            false
        }
    }

    suspend fun batchSync(baseUrl: String, token: String, request: BatchSyncRequest): Result<BatchSyncResponse> {
        return runCatching {
            val response: HttpResponse = client.post("$baseUrl/api/v1/sync/batch") {
                contentType(ContentType.Application.Json)
                bearerAuth(token)
                setBody(request)
                timeout { requestTimeoutMillis = 30_000 }
            }
            if (response.status.isSuccess()) {
                response.body<BatchSyncResponse>()
            } else {
                throw ApiException(response.status.value, "Sync failed: ${response.status.description}")
            }
        }
    }
}

class ApiException(val statusCode: Int, message: String) : Exception(message)
