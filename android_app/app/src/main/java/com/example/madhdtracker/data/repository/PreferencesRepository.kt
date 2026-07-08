package com.example.madhdtracker.data.repository

import android.content.Context

class PreferencesRepository(context: Context) {
    private val prefs = context.getSharedPreferences("adhd_prefs", Context.MODE_PRIVATE)

    fun areNotificationsEnabled(): Boolean {
        return prefs.getBoolean(KEY_NOTIFICATIONS_ENABLED, true)
    }

    fun setNotificationsEnabled(enabled: Boolean) {
        prefs.edit().putBoolean(KEY_NOTIFICATIONS_ENABLED, enabled).apply()
    }

    fun getServerUrl(): String {
        return prefs.getString(KEY_SERVER_URL, "") ?: ""
    }

    fun setServerUrl(url: String) {
        val normalized = url.trimEnd('/')
        prefs.edit().putString(KEY_SERVER_URL, normalized).apply()
    }

    companion object {
        private const val KEY_NOTIFICATIONS_ENABLED = "notifications_enabled"
        private const val KEY_SERVER_URL = "server_url"
    }
}
