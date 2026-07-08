package com.example.madhdtracker.data.repository

import android.content.Context
import androidx.room.Room
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.remote.ApiClient
import com.example.madhdtracker.data.remote.ApiException
import com.example.madhdtracker.data.remote.BatchSyncRequest
import com.example.madhdtracker.data.remote.SyncDayItem
import com.example.madhdtracker.data.remote.SyncValueItem

sealed class SyncAllResult {
    data class Success(val accepted: Int, val conflicted: Int) : SyncAllResult()
    data class Error(val message: String) : SyncAllResult()
    object NoServer : SyncAllResult()
    object NotLoggedIn : SyncAllResult()
}

sealed class LoginResult {
    data class Success(val email: String, val totalDays: Int, val createdAt: String) : LoginResult()
    data class Error(val message: String) : LoginResult()
    object NoServer : LoginResult()
}

data class UserInfo(val email: String, val totalDays: Int, val createdAt: String)

class UserRepository(private val context: Context) {

    private val prefsRepo = PreferencesRepository(context)
    private val encryptedPrefs = EncryptedPreferencesRepository(context)
    private val apiClient = ApiClient()

    fun getCurrentUser(): UserInfo? {
        val token = encryptedPrefs.accessToken
        val email = encryptedPrefs.userEmail
        return if (token.isNotBlank() && email.isNotBlank()) {
            UserInfo(email = email, totalDays = 0, createdAt = "")
        } else null
    }

    fun getServerUrl(): String = prefsRepo.getServerUrl()

    suspend fun checkServerReachable(): Boolean {
        val url = prefsRepo.getServerUrl()
        if (url.isBlank()) return false
        return apiClient.checkReachable(url)
    }

    suspend fun login(email: String, password: String): LoginResult {
        val url = prefsRepo.getServerUrl()
        if (url.isBlank()) return LoginResult.NoServer

        val result = apiClient.login(url, email, password)
        return result.fold(
            onSuccess = { loginResp ->
                encryptedPrefs.accessToken = loginResp.access_token
                if (loginResp.refresh_token.isNotBlank()) encryptedPrefs.refreshToken = loginResp.refresh_token
                encryptedPrefs.userEmail = email
                val meResult = apiClient.getMe(url, loginResp.access_token)
                meResult.fold(
                    onSuccess = { me ->
                        encryptedPrefs.userEmail = me.email
                        LoginResult.Success(me.email, me.total_days, me.created_at)
                    },
                    onFailure = {
                        LoginResult.Success(email, 0, "")
                    }
                )
            },
            onFailure = { ex ->
                val msg = when {
                    ex is ApiException && ex.statusCode == 401 -> "Nesprávne prihlasovacie údaje"
                    ex is ApiException && ex.statusCode == 409 -> "Účet s týmto emailom už existuje"
                    isConnectionError(ex) -> "Server nie je dostupný"
                    isTimeoutError(ex) -> "Server neodpovedá, skúste neskôr"
                    else -> "Prihlásenie zlyhalo"
                }
                LoginResult.Error(msg)
            }
        )
    }

    suspend fun register(email: String, password: String): LoginResult {
        val url = prefsRepo.getServerUrl()
        if (url.isBlank()) return LoginResult.NoServer

        val result = apiClient.register(url, email, password)
        return result.fold(
            onSuccess = { login(email, password) },
            onFailure = { ex ->
                val msg = when {
                    ex is ApiException && ex.statusCode == 409 -> "Účet s týmto emailom už existuje"
                    isConnectionError(ex) -> "Server nie je dostupný"
                    else -> "Registrácia zlyhala"
                }
                LoginResult.Error(msg)
            }
        )
    }

    fun logout() {
        encryptedPrefs.clearSession()
    }

    // Returns fresh access token or null if refresh failed
    private suspend fun refreshAccessToken(): String? {
        val url = prefsRepo.getServerUrl()
        val rt = encryptedPrefs.refreshToken
        if (url.isBlank() || rt.isBlank()) return null
        return apiClient.refreshToken(url, rt).fold(
            onSuccess = { resp ->
                encryptedPrefs.accessToken = resp.access_token
                if (resp.refresh_token.isNotBlank()) encryptedPrefs.refreshToken = resp.refresh_token
                resp.access_token
            },
            onFailure = { null }
        )
    }

    suspend fun syncAll(): SyncAllResult {
        val url = prefsRepo.getServerUrl()
        if (url.isBlank()) return SyncAllResult.NoServer
        var token = encryptedPrefs.accessToken
        if (token.isBlank()) return SyncAllResult.NotLoggedIn

        val db = Room.databaseBuilder(context, AppDatabase::class.java, "adhd_tracker.db")
            .fallbackToDestructiveMigration()
            .build()

        return try {
            val days = db.eventDayDao().getAll()
            val syncDays = days.map { day ->
                val values = db.eventValueDao().getByDay(day.id)
                SyncDayItem(
                    date = day.date,
                    updated_at = day.updatedAt,
                    values = values.map { v ->
                        SyncValueItem(
                            element_key = v.elementKey,
                            value_binary = v.valueBinary,
                            value_scale = v.valueScale,
                            updated_at = day.updatedAt,
                            note = v.note,
                        )
                    }
                )
            }

            val request = BatchSyncRequest(days = syncDays)
            var result = apiClient.batchSync(url, token, request)

            // On 401 try refresh once and retry
            if (result.isFailure) {
                val ex = result.exceptionOrNull()
                if (ex is ApiException && ex.statusCode == 401) {
                    val newToken = refreshAccessToken()
                    if (newToken != null) {
                        result = apiClient.batchSync(url, newToken, request)
                    }
                }
            }

            result.fold(
                onSuccess = { resp ->
                    SyncAllResult.Success(
                        accepted = resp.summary.records_accepted,
                        conflicted = resp.summary.records_conflicted,
                    )
                },
                onFailure = { ex ->
                    val msg = when {
                        ex is ApiException && ex.statusCode == 401 -> "Prihlásenie vypršalo, prihláste sa znova"
                        isConnectionError(ex) -> "Server nie je dostupný"
                        isTimeoutError(ex) -> "Server neodpovedá, skúste neskôr"
                        else -> "Synchronizácia zlyhala"
                    }
                    SyncAllResult.Error(msg)
                }
            )
        } finally {
            db.close()
        }
    }

    private fun isConnectionError(ex: Throwable): Boolean {
        return ex is java.net.ConnectException
            || ex is java.io.IOException
            || ex.cause is java.net.ConnectException
    }

    private fun isTimeoutError(ex: Throwable): Boolean {
        return ex is java.net.SocketTimeoutException
            || ex.cause is java.net.SocketTimeoutException
    }
}
